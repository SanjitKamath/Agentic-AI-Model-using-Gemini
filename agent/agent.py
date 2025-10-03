import os
from difflib import get_close_matches
from agent.registry import get_registry
from agent.llm_clients import get_llm_client
from dotenv import load_dotenv

# Note: The 'load_modules' function is now implicitly handled by your main script startup
# or can be explicitly called from a loader file if you prefer. We assume modules are loaded.

load_dotenv()

class Agent:
    def __init__(self, provider=None, api_key=None, model=None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "gemini")
        self.api_key = api_key or os.getenv(f"{self.provider.upper()}_API_KEY")
        self.model_name = model or os.getenv(f"{self.provider.upper()}_MODEL", "gemini-1.5-flash-latest")
        
        self.llm_client = get_llm_client(self.provider, self.api_key, self.model_name)
        self.functions = get_registry()

    def run(self, prompt: str):
        parsed_choice = self.llm_client.get_tool_choice(prompt, self.functions)
        
        if "error" in parsed_choice:
            return parsed_choice

        func_name = parsed_choice.get("name")
        args = parsed_choice.get("args", {})

        if not func_name:
            if "clarification" in args:
                return {"clarification": args["clarification"]}
            return {"error": "Agent did not select a function."}

        return self._call_function(func_name, args)

    def _call_function(self, func_name: str, args: dict):
        # --- ADD THIS LINE FOR DEBUGGING ---
        print(f"\n[AGENT DEBUG] LLM chose function: '{func_name}' with args: {args}\n")
        # ------------------------------------
        
        resolved_name = self._resolve_function_name(func_name)
        if not resolved_name:
            return {"error": f"Unknown function: '{func_name}'."}

        func = self.functions[resolved_name]["func"]
        try:
            result = func(**args)
            return {"function_name": resolved_name, "function_args": args, "function_result": result}
        except Exception as e:
            return {"error": f"Error executing {resolved_name}: {str(e)}"}

    def _resolve_function_name(self, func_name: str):
        if func_name in self.functions:
            return func_name
        matches = get_close_matches(func_name, self.functions.keys(), n=1, cutoff=0.7)
        return matches[0] if matches else None