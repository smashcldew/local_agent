# adapters/registry.py

class AdapterRegistry:
    def __init__(self):
        self._models = {}

    def register(self, name: str, description: str, model_type: str, setup_fn):
        self._models[name] = {
            "type": model_type,
            "description": description,
            "setup": setup_fn
        }

    def get_all_models(self) -> dict:
        return self._models

    def get_adapter(self, name: str):
        if name in self._models:
            return self._models[name]["setup"]()
        return None

adapter_registry = AdapterRegistry()