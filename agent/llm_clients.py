import os
import re
import json
import inspect
import requests
from abc import ABC, abstractmethod
from dotenv import load_dotenv

import google.generativeai as genai
from openai import OpenAI  # for the OpenAI provider


# -------------------- Helper --------------------
def get_json_schema_type(py_type):
    """Map Python types to JSON schema types."""
    if py_type is int:
        return "integer"
    if py_type is float:
        return "number"
    if py_type is bool:
        return "boolean"
    return "string"


# -------------------- Base Interface --------------------
class LLMClient(ABC):
    @abstractmethod
    def get_tool_choice(self, prompt: str, functions: dict) -> dict:
        """
        Queries the LLM to get a function call choice based on the user prompt.
        Returns:
           { "name": ..., "args": {...} }
        Or { "error": "..." } if something failed.
        """
        pass


# -------------------- Gemini --------------------
class GeminiClient(LLMClient):
    ALLOWED_MODELS = ["gemini-2.0-flash"]

    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash-latest"):
        if not api_key:
            load_dotenv()
            api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not found in .env or constructor.")

        if model not in self.ALLOWED_MODELS:
            raise ValueError(f"Model '{model}' not allowed. Use one of: {self.ALLOWED_MODELS}")

        genai.configure(api_key=api_key)
        self.model_name = model

    def get_tool_choice(self, prompt: str, functions: dict) -> dict:
        try:
            gemini_tools = self._format_functions_for_gemini(functions)
            model = genai.GenerativeModel(model_name=self.model_name, tools=gemini_tools)
            tool_config = {"function_calling_config": "ANY"}
            response = model.generate_content(prompt, tool_config=tool_config)

            if (
                response.candidates
                and response.candidates[0].content.parts
                and hasattr(response.candidates[0].content.parts[0], "function_call")
            ):
                function_call = response.candidates[0].content.parts[0].function_call
                args = dict(function_call.args) if function_call.args else {}
                return {"name": function_call.name, "args": args}

            return {"name": None, "args": {"clarification": "No tool was selected by Gemini."}}
        except Exception as e:
            return {"error": f"Gemini API Error: {str(e)}"}

    def _format_functions_for_gemini(self, functions: dict) -> list:
        tool_list = []
        for func_details in functions.values():
            sig = func_details["signature"]
            properties, required = {}, []
            for param in sig.parameters.values():
                param_type = get_json_schema_type(param.annotation)
                properties[param.name] = {"type": param_type}
                if param.default is inspect.Parameter.empty:
                    required.append(param.name)
            tool_list.append(
                {
                    "function_declarations": [
                        {
                            "name": func_details["name"],
                            "description": func_details["description"],
                            "parameters": {"type": "object", "properties": properties, "required": required},
                        }
                    ]
                }
            )
        return tool_list


# -------------------- DeepSeek (via OpenRouter) --------------------
class DeepSeekClient(LLMClient):
    FREE_TIER_MODELS = [
        "deepseek/deepseek-r1:free",
        "deepseek/deepseek-chat-v3.1:free",
        "tngtech/deepseek-r1t-chimera:free",
    ]

    def __init__(self, api_key: str = None, model: str = "deepseek/deepseek-chat-v3.1:free"):
        if not api_key:
            load_dotenv()
            api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OpenRouter API key not found in .env or constructor.")
        if model not in self.FREE_TIER_MODELS:
            raise ValueError(f"Model '{model}' not allowed. Use one of: {self.FREE_TIER_MODELS}")

        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def get_tool_choice(self, prompt: str, functions: dict) -> dict:
        tools = self._format_functions_for_tool_api(functions)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "tools": tools,
            "tool_choice": "auto",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openrouter.ai",
            "X-Title": "DeepSeek Tool Client",
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            choices = data.get("choices", [])
            if not choices:
                return {"name": None, "args": {"clarification": "No response from model."}}

            msg = choices[0].get("message", {})
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                call = tool_calls[0]
                func = call.get("function", {})
                name = func.get("name")
                args = func.get("arguments", "{}")
                try:
                    parsed_args = json.loads(args)
                except json.JSONDecodeError:
                    parsed_args = {"error": "Invalid JSON arguments"}
                return {"name": name, "args": parsed_args}

            return {"name": None, "args": {"clarification": "No tool selected by DeepSeek."}}
        except requests.RequestException as e:
            return {"error": f"OpenRouter API Error: {str(e)}"}

    def _format_functions_for_tool_api(self, functions: dict) -> list:
        formatted = []
        for f in functions.values():
            sig = f["signature"]
            props = {}
            for p in sig.parameters.values():
                props[p.name] = {"type": "string", "description": f"Parameter {p.name}"}
            required = [p.name for p in sig.parameters.values() if p.default is inspect.Parameter.empty]
            formatted.append(
                {
                    "type": "function",
                    "function": {
                        "name": f["name"],
                        "description": f["description"],
                        "parameters": {"type": "object", "properties": props, "required": required},
                    },
                }
            )
        return formatted


# -------------------- OpenAI --------------------
class OpenAIClient(LLMClient):
    ALLOWED_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        if not api_key:
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in .env or constructor.")
        if model not in self.ALLOWED_MODELS:
            raise ValueError(f"Model '{model}' not allowed. Use one of: {self.ALLOWED_MODELS}")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def get_tool_choice(self, prompt: str, functions: dict) -> dict:
        tools = self._format_functions_for_tool_api(functions)
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}], tools=tools, tool_choice="auto"
            )
            msg = response.choices[0].message
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                call = msg.tool_calls[0]
                return {"name": call.function.name, "args": json.loads(call.function.arguments)}
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
            required = [p.name for p in sig.parameters.values() if p.default is inspect.Parameter.empty]
            formatted.append(
                {
                    "type": "function",
                    "function": {
                        "name": f["name"],
                        "description": f["description"],
                        "parameters": {"type": "object", "properties": props, "required": required},
                    },
                }
            )
        return formatted


# -------------------- Factory Function --------------------
def get_llm_client(provider: str, api_key: str = None, model: str = None) -> LLMClient:
    provider = provider.lower()
    if provider == "gemini":
        return GeminiClient(api_key=api_key, model=model or "gemini-1.5-flash-latest")
    elif provider == "deepseek":
        return DeepSeekClient(api_key=api_key, model=model or "deepseek/deepseek-chat-v3.1:free")
    elif provider == "openai":
        return OpenAIClient(api_key=api_key, model=model or "gpt-4o-mini")
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
