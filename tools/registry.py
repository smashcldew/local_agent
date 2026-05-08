# tools/registry.py
from typing import Callable, Dict, Any, List

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []

    def register(self, name: str, schema: dict, handler: Callable):
        """供各個工具模組在 import 時主動註冊自己"""
        self._tools[name] = handler
        self._schemas.append(schema)

    def get_schemas(self) -> List[Dict[str, Any]]:
        return self._schemas

    def get_handler(self, name: str) -> Callable:
        return self._tools.get(name)

# 實例化單例，供其他模組匯入
registry = ToolRegistry()