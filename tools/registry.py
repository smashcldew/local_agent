# tools/registry.py
from typing import Callable, Dict, Any, List, Optional

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []
        self._by_name: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, schema: dict, handler: Callable):
        """供各個工具模組在 import 時主動註冊自己"""
        self._tools[name] = handler
        self._schemas.append(schema)
        self._by_name[name] = schema

    def get_schemas(self, toolset: Optional[str] = None,
                    tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        回傳要送給模型的工具 schema。
        - 不帶參數：回傳全部已註冊工具（與舊行為相容）。
        - toolset="readonly"：只回傳該群組的工具（見 tools/toolsets.py）。
          未知的 toolset 名稱 → 安全退回「全部」。
        - tool_names=[...]：直接指定工具名稱清單。
        """
        if toolset is not None:
            from tools.toolsets import resolve
            names = resolve(toolset)
            if names is None:
                return list(self._schemas)  # 未知群組 → 全部
            tool_names = names
        if tool_names is not None:
            return [self._by_name[n] for n in tool_names if n in self._by_name]
        return list(self._schemas)

    def get_handler(self, name: str) -> Callable:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._by_name.keys())

# 實例化單例，供其他模組匯入
registry = ToolRegistry()
