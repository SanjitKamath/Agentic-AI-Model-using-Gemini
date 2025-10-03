import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import google.generativeai as genai
import importlib
import pkgutil

# Import the refactored Agent class
from agent.agent import Agent

def load_tool_modules(module_dir="modules"):
    """
    Dynamically finds and imports all 'tools.py' files within subdirectories
    of the specified module directory. This is what makes the tools available to the agent.
    """
    print(f"--- Loading tool modules from '{module_dir}' directory ---")
    for (_, module_name, _) in pkgutil.iter_modules([module_dir]):
        full_module_path = f"{module_dir}.{module_name}"
        try:
            # Attempt to import the tools.py submodule
            importlib.import_module(f".tools", package=full_module_path)
            print(f"[SUCCESS] Loaded tools from '{full_module_path}'")
        except ModuleNotFoundError:
            # This is expected if a module doesn't have a tools.py file
            print(f"[INFO] No tools.py found in '{full_module_path}', skipping.")
        except Exception as e:
            print(f"[ERROR] Failed to load tools from '{full_module_path}': {e}")

# --- Application Startup ---
# Load all tool modules before the agent or server starts
load_tool_modules()

# Configure the Gemini client for the summarizer
# The agent will configure its own client based on the user's selection
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=gemini_api_key)
    summarizer_model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest"))
except Exception as e:
    print(f"Error configuring the summarizer model: {e}")
    summarizer_model = None


# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def summarize_result_for_user(query: str, agent_result: dict) -> str:
    """
    Takes the raw agent JSON result and uses an LLM to summarize it
    into a natural, human-readable response.
    """
    if "error" in agent_result:
        return f"An error occurred: {agent_result['error']}"
    if "clarification" in agent_result:
        return agent_result['clarification']

    if not summarizer_model:
        return "Summarizer model is not available. Please check configuration."

    result_str = json.dumps(agent_result.get("function_result", {}), indent=2)
    prompt = f"""
    Based on the user's query "{query}", a tool was executed and returned this JSON data:
    {result_str}

    Please provide a concise, friendly, and natural language response to the user.
    - Directly answer the original question.
    - Do not mention technical terms like "JSON", "agent", or "tool".
    - Use emojis like ✅ and ❌ where appropriate to indicate success or failure.
    - Start the response directly without any preamble.
    """
    try:
        response = summarizer_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error summarizing the result: {e}"

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main HTML user interface."""
    return FileResponse('templates/index.html')

@app.post("/chat")
async def chat(request: Request):
    """
    Handle incoming chat messages. This endpoint creates a new agent for each request
    based on the model provider selected in the UI.
    """
    data = await request.json()
    query = data.get("query", "")
    provider = data.get("provider", "gemini") # Default to 'gemini' if not specified

    if not query:
        return JSONResponse({"error": "Query cannot be empty."}, status_code=400)

    try:
        # Create a new agent instance for this specific request
        agent = Agent(provider=provider)
        
        # Run the agent to get the raw tool output
        agent_result = agent.run(query)
        
        # Use the summarizer to create a user-friendly response
        formatted_text = summarize_result_for_user(query, agent_result)
        
        return JSONResponse({"result": formatted_text})
    except Exception as e:
        # Catch any unexpected errors during agent initialization or execution
        return JSONResponse({"error": str(e)}, status_code=500)

def main():
    """Run the FastAPI application using uvicorn."""
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
