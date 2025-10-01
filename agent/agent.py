import os
import re
import json
import inspect
import importlib
import pkgutil
from difflib import get_close_matches
import google.generativeai as genai
from agent.registry import get_registry
from dotenv import load_dotenv

load_dotenv()

def load_modules(module_dir="modules"):
    """Dynamically imports all modules from a given directory."""
    import os
    import importlib
    import pkgutil
    print(f"\n[DEBUG] Attempting to load modules from: '{module_dir}'")
    abs_path = os.path.abspath(module_dir)
    print(f"[DEBUG] Absolute path is: '{abs_path}'")
    print(f"[DEBUG] Does path exist? {os.path.exists(abs_path)}")

    for (_, module_name, _) in pkgutil.iter_modules([module_dir]):
        print(f"[DEBUG] Found module: '{module_name}'")
        full_module_path = f"{module_dir}.{module_name}"

        # --- THIS IS THE CORRECTED LOGIC ---
        try:
            # Directly try to import the 'tools' submodule within the package
            importlib.import_module(f".tools", package=full_module_path)
            print(f"[DEBUG] Successfully imported tools from '{full_module_path}'")
        except ModuleNotFoundError:
            # This is normal if a module doesn't have a tools.py file
            print(f"[DEBUG] No tools.py found in '{full_module_path}', skipping.")

class Agent:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")

        if not self.api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY in environment.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        # --- MODIFIED: Load modules and then get the registry ---
        load_modules()
        self.functions = get_registry()

        # --- ADDED FOR DEBUGGING ---
        print("--- AGENT REGISTRY LOADED ---")
        print(f"Registered functions: {list(self.functions.keys())}")
        # ---------------------------

    def run(self, prompt: str):
        return self.handle_prompt(prompt)

    def _resolve_function_name(self, func_name: str):
        if not func_name:
            return None
        if func_name in self.functions:
            return func_name
        matches = get_close_matches(func_name, self.functions.keys(), n=1, cutoff=0.7)
        return matches[0] if matches else None

    def _call_function(self, func_name: str, args: dict):
        resolved_name = self._resolve_function_name(func_name)
        if not resolved_name:
            return {"error": f"Unknown function: '{func_name}'."}

        func_details = self.functions[resolved_name]
        func = func_details["func"]
        sig = func_details["signature"]

        try:
            bound_args = sig.bind(**args)
            bound_args.apply_defaults()
            result = func(**bound_args.arguments)
            # The agent's job is just to return the raw result.
            return {"function_name": resolved_name, "function_args": args, "function_result": result}
        except TypeError as e:
            return {"error": f"Argument mismatch for {resolved_name}: {e}"}
        except Exception as e:
            return {"error": f"Error executing {resolved_name}: {str(e)}"}

    def handle_prompt(self, prompt: str) -> dict:
        func_descs = []
        for f in self.functions.values():
            name = f['name']
            description = f['description']
            sig = f['signature']
            params = []
            for param in sig.parameters.values():
                p_name = param.name
                p_type = param.annotation.__name__ if param.annotation is not inspect.Parameter.empty else 'any'
                if param.default is inspect.Parameter.empty:
                    params.append(f'"{p_name}" ({p_type}, required)')
                else:
                    params.append(f'"{p_name}" ({p_type}, optional)')
            param_str = ", ".join(params)
            func_descs.append(f'- {name}({param_str}): {description}')
        
        func_desc_str = "\n".join(func_descs)

        system_prompt = f"""
You are a task-oriented agent. Your sole purpose is to select and execute a function that matches the user's request.
- You MUST select a function if one is relevant to the user's query.
- Do not answer questions yourself or decline requests if a suitable tool is available.
- You must respond ONLY in a valid JSON format.


Available functions:
{func_desc_str}

The JSON response must contain:
- "name": The exact name of the function to call.
- "args": A dictionary of arguments for the function.

Example of asking for clarification if 'employee_id' is missing:
{{"name": null, "args": {{"clarification": "Which employee ID would you like me to check?"}}}}
"""
        try:
            response = self.model.generate_content([system_prompt, prompt])
            raw_text = response.text
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            
            if not json_match:
                raise json.JSONDecodeError(f"No JSON object found in response: {raw_text}", raw_text, 0)
            
            json_str = json_match.group(0)
            parsed = json.loads(json_str)

        except json.JSONDecodeError:
            return {"error": f"Agent returned non-JSON response: {response.text}"}
        except Exception as e:
            return {"error": f"Agent response error: {str(e)}"}

        func_name = parsed.get("name")
        args = parsed.get("args", {})

        if not func_name:
            if "clarification" in args:
                return {"clarification": args["clarification"]}
            return {"error": "The agent did not select a function to execute."}

        # The final result is now just the raw output from the tool
        return self._call_function(func_name, args)