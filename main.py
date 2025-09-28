# main.py
import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import google.generativeai as genai

from agent.agent import Agent

# Load environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")

if not GOOGLE_API_KEY:
    raise ValueError("Google API key not found. Set GOOGLE_API_KEY in environment.")

# Initialize agent. This will now automatically discover tools in the `modules` directory.
agent = Agent(api_key=GOOGLE_API_KEY, model=MODEL_NAME)
# Initialize a separate model for summarization
summarizer_model = genai.GenerativeModel(MODEL_NAME)

# FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW GENERIC SUMMARIZER ---
def summarize_result_for_user(query: str, agent_result: dict) -> str:
    """Takes the raw agent JSON result and summarizes it for the user."""
    
    if "error" in agent_result:
        return f"An error occurred: {agent_result['error']}"
    if "clarification" in agent_result:
        return agent_result['clarification']

    # Convert the JSON result to a string for the prompt
    result_str = json.dumps(agent_result.get("function_result", {}), indent=2)

    prompt = f"""
    The user asked: "{query}"

    An agent executed a tool and returned the following JSON data:
    {result_str}     

    Based on this data, write a concise, friendly, and natural language response to the user.
    - Directly answer the user's original question.
    - Do not mention the words "JSON", "agent", or "tool".
    - Start the response directly without any preamble like "Here is the summary:".
    - Use emojis like ✅ and ❌ where appropriate to indicate success or failure.
    """
    
    try:
        response = summarizer_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error summarizing the result: {e}"

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the external HTML file."""
    return FileResponse('templates/index.html')

@app.post("/chat")
async def chat(request: Request):
    """Handle chat messages."""
    data = await request.json()
    query = data.get("query", "")
    if not query:
        return JSONResponse({"error": "Query cannot be empty."}, status_code=400)

    try:
        # Step 1: Run the agent to get a tool result (raw JSON)
        agent_result = agent.run(query)

        # Step 2: Use the LLM to format the raw result into a human-friendly response
        formatted_text = summarize_result_for_user(query, agent_result)
        
        return JSONResponse({"result": formatted_text})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

def main():
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()