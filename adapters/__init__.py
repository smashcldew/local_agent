# adapters/__init__.py
import os
import importlib
from .registry import adapter_registry

current_dir = os.path.dirname(__file__)

# 1. 本地 adapter:頂層的 *_adapter.py 一律自動載入(純本地,無付費)
for filename in os.listdir(current_dir):
    if filename.endswith("_adapter.py") and filename != "base_adapter.py":
        module_name = filename[:-3]
        importlib.import_module(f"adapters.{module_name}")


def _truthy(v) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "on")


# 2. 付費雲端 adapter:集中於 adapters/cloud/,預設【關閉】。
#    需設定環境變數 MAVERICK_ENABLE_CLOUD=1 才會載入並註冊,確保核心永遠純本地。
if _truthy(os.getenv("MAVERICK_ENABLE_CLOUD", "")):
    try:
        importlib.import_module("adapters.cloud")
    except Exception as e:
        print(f"[警告] 雲端 adapter 載入失敗（略過，核心仍可純本地運作）: {e}")

__all__ = ["adapter_registry"]
