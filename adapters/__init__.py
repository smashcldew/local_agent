# adapters/__init__.py
import os
import importlib
from .registry import adapter_registry

current_dir = os.path.dirname(__file__)

for filename in os.listdir(current_dir):
    if filename.endswith("_adapter.py") and filename != "base_adapter.py":
        module_name = filename[:-3]
        importlib.import_module(f"adapters.{module_name}")

__all__ = ["adapter_registry"]