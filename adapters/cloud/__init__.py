# adapters/cloud/__init__.py
#
# 付費雲端模型 adapter 集中於此。此套件【預設不會被載入】——
# 只有在環境變數 MAVERICK_ENABLE_CLOUD=1 時,adapters/__init__.py 才會 import 它。
# 這樣核心永遠能純靠本地模型(Ollama)運作;付費雲端是可選、可拔的。
#
# 在此 import 各家雲端 adapter 以完成註冊。
from . import openai_compat_adapter  # noqa: F401

__all__ = ["openai_compat_adapter"]
