import re
import json
import inspect
from abc import ABC, abstractmethod

import google.generativeai as genai
from openai import OpenAI  # for the OpenAI provider

# Try to import the correct client for deepseek
try:
    from deepseek import DeepSeekAPI
except ImportError as e:
    DeepSeekAPI = None
    _deepseek_import_error = e

# --- Helper function to map Python types to JSON Schema types ---
def get_json_schema_type(py_type):
    if py_type is int:
        return "integer"
    if py_type is float:
        return "number"
    if py_type is bool:
        return "boolean"
    # Default to string for any other type, including Enums that inherit from str
    return "string"

class LLMClient(ABC):
    @abstractmethod
    def get_tool_choice(self, prompt: str, functions: dict) -> dict:
        """
        Queries the LLM to get a function call choice based on the user prompt.
        Returns a dict like:
           { "name": ..., "args": {...} }
        Or { "error": "..." } if something failed.
        """
        pass


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("Google API key not found.")
        genai.configure(api_key=api_key)
        self.model_name = model

    def get_tool_choice(self, prompt: str, functions: dict) -> dict:
        try:
            gemini_tools = self._format_functions_for_gemini(functions)
            model = genai.GenerativeModel(model_name=self.model_name, tools=gemini_tools)

            # Force the model to choose a tool if one is relevant
            tool_config = {"function_calling_config": "ANY"}
            
            response = model.generate_content(prompt, tool_config=tool_config)

            if (response.candidates and
                response.candidates[0].content.parts and
                hasattr(response.candidates[0].content.parts[0], "function_call")):

                function_call = response.candidates[0].content.parts[0].function_call
                
                # Correctly convert the Gemini 'Struct' object to a Python dict
                args = dict(function_call.args) if function_call.args else {}
                
                return {
                    "name": function_call.name,
                    "args": args
                }

            return {"name": None, "args": {"clarification": "No tool was selected by the Gemini model."}}

        except Exception as e:
            return {"error": f"Gemini API Error or no tool chosen: {str(e)}"}

    def _format_functions_for_gemini(self, functions: dict) -> list:
        tool_list = []
        for func_details in functions.values():
            sig = func_details["signature"]
            properties, required = {}, []
            for param in sig.parameters.values():
                # Use the helper to get the correct JSON Schema type
                param_type = get_json_schema_type(param.annotation)
                properties[param.name] = {"type": param_type}
                
                if param.default is inspect.Parameter.empty:
                    required.append(param.name)
            
            tool_list.append({
                "function_declarations": [{
                    "name": func_details["name"],
                    "description": func_details["description"],
                    "parameters": {"type": "object", "properties": properties, "required": required}
                }]
            })
        return tool_list
    
class DeepSeekClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        if DeepSeekAPI is None:
            raise ImportError("deepseek.DeepSeekAPI not available, failed to import: "
                              + repr(_deepseek_import_error))
        if not api_key:
            raise ValueError("DeepSeek API key not found.")
        self.client = DeepSeekAPI(api_key=api_key)
        self.model = model

    def get_tool_choice(self, prompt: str, functions: dict) -> dict:
        tools = self._format_functions_for_tool_api(functions)
        try:
            # Use the OpenAI-compatible chat interface
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                tools=tools,
                tool_choice="auto"
            )
            msg = response.choices[0].message
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                call = msg.tool_calls[0]
                return {
                    "name": call.function.name,
                    "args": json.loads(call.function.arguments)
                }
            return {"name": None, "args": {"clarification": "Could not choose a tool; please clarify."}}
        except Exception as e:
            return {"error": f"DeepSeek API Error: {str(e)}"}

    def _format_functions_for_tool_api(self, functions: dict) -> list:
        formatted = []
        for f in functions.values():
            sig = f["signature"]
            props = {}
            for p in sig.parameters.values():
                props[p.name] = {"type": "string", "description": f"Parameter {p.name}"}
            required = [p.name for p in sig.parameters.values()
                        if p.default is inspect.Parameter.empty]
            formatted.append({
                "type": "function",
                "function": {
                    "name": f["name"],
                    "description": f["description"],
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": required
                    }
                }
            })
        return formatted


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("OpenAI API key not found.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def get_tool_choice(self, prompt: str, functions: dict) -> dict:
        tools = self._format_functions_for_tool_api(functions)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                tools=tools,
                tool_choice="auto"
            )
            msg = response.choices[0].message
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                call = msg.tool_calls[0]
                return {
                    "name": call.function.name,
                    "args": json.loads(call.function.arguments)
                }
            return {"name": None, "args": {"clarification": "Could not choose a tool; please clarify."}}
        except Exception as e:
            return {"error": f"OpenAI API Error: {str(e)}"}

    def _format_functions_for_tool_api(self, functions: dict) -> list:
        formatted = []
        for f in functions.values():
            sig = f["signature"]
            props = {}
            for p in sig.parameters.values():
                props[p.name] = {"type": "string", "description": f"Parameter {p.name}"}
            required = [p.name for p in sig.parameters.values()
                        if p.default is inspect.Parameter.empty]
            formatted.append({
                "type": "function",
                "function": {
                    "name": f["name"],
                    "description": f["description"],
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": required
                    }
                }
            })
        return formatted


def get_llm_client(provider: str, api_key: str, model: str) -> LLMClient:
    provider = provider.lower()
    if provider == "gemini":
        return GeminiClient(api_key=api_key, model=model)
    elif provider == "deepseek":
        return DeepSeekClient(api_key=api_key, model=model)
    elif provider == "openai":
        return OpenAIClient(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
