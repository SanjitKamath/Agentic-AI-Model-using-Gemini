# utils/gemini_client.py
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Please set GEMINI_API_KEY in your environment or .env file")

# Configure the official client
genai.configure(api_key=GEMINI_API_KEY)

# Helper: Ask Gemini which function to call.
def query_gemini(model: str, prompt: str, functions: list, max_output_chars: int = 2000) -> str:
    """
    Query Gemini to pick a function and produce JSON like:
    {"name": "function_name", "args": {"a": 1, "b": 2}}
    - functions: list of dicts containing {"name", "description", "schema"}
    - model: e.g., "gemini-1.5-flash"

    Returns raw text (expected to be JSON).
    """
    # Build a system + user prompt that explains available functions.
    func_lines = []
    for f in functions:
        name = f.get("name")
        desc = f.get("description", "")
        schema = f.get("schema", {})
        schema_repr = json.dumps(schema)
        func_lines.append(f"- {name}: {desc} | schema: {schema_repr}")

    system_message = (
        "You are a careful assistant whose task is to select exactly one function to call "
        "based on the user's request. Only choose a function if it matches the user's intent. "
        "Output strictly JSON in the format: {\"name\": \"function_name\", \"args\": {...}}. "
        "If no function is appropriate, return {\"name\": null, \"args\": {}}.\n\n"
        "Available functions:\n" + "\n".join(func_lines)
    )

    # Compose the messages: some SDKs accept a list of messages; use generate_text or generate depending on SDK version.
    try:
        # Using the generative model convenience interface
        model_obj = genai.get_model(model)
        response = model_obj.generate(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_output_chars=max_output_chars,
        )
        # response may have 'candidates' or 'content' depending on version
        # Attempt to extract text robustly:
        text = ""
        if hasattr(response, "candidates") and response.candidates:
            # Some clients return .candidates[0].content[0].text
            try:
                text = response.candidates[0].content[0].text
            except Exception:
                text = str(response.candidates[0])
        else:
            # Fallback: str(response)
            text = getattr(response, "text", None) or str(response)
        return text
    except Exception as e:
        # Bubble up or convert to simpler text
        return json.dumps({"name": None, "args": {}, "error": f"Gemini query error: {e}"})
