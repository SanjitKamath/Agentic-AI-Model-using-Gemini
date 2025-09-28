import inspect
from typing import Callable, Dict, Any

_REGISTRY: Dict[str, Dict[str, Any]] = {}

def register(name: str = None, description: str = None, schema: dict = None):
    """Decorator to register any Python function in the agent."""
    def deco(func: Callable):
        key = name or func.__name__
        sig = inspect.signature(func)
        _REGISTRY[key] = {
            "func": func,
            "name": key,
            "description": description or (func.__doc__ or ""),
            "signature": sig,
            "schema": schema or {}
        }
        return func
    return deco

def get_registry():
    return _REGISTRY

def get_function(name: str):
    return _REGISTRY.get(name)
