# adapters/cloud/openai_compat_adapter.py
#
# OpenAI 相容的付費雲端 adapter(OpenAI / OpenRouter / 自架相容端點皆可)。
# 參考 NousResearch/hermes-agent (MIT) 的 provider/adapter 分離作法:雲端 adapter
# 與本地 adapter 共用同一個 BaseAdapter 介面與 registry,差別只在於「可選、需金鑰」。
# 參見 LICENSES/hermes-agent-MIT.txt
#
# 設定(皆為環境變數):
#   OPENAI_API_KEY    金鑰(未設定則呼叫時回傳清楚錯誤,不會崩潰)
#   OPENAI_BASE_URL   端點,預設 https://api.openai.com/v1
#   OPENAI_MODEL      模型名稱,預設 gpt-4o-mini
#   OPENAI_MAX_TOKENS 上下文預算,預設 8192
import os
import requests
from display import Colors
from adapters.base_adapter import BaseAdapter
from adapters.registry import adapter_registry


class OpenAICompatAdapter(BaseAdapter):
    def __init__(self, model_name=None, base_url=None, api_key=None):
        model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        super().__init__(model_name=model_name, host=base_url, temperature=0.7)
        # BaseAdapter 預設 api_url 指向 Ollama 的 /api/chat,這裡覆寫成 OpenAI 相容端點
        self.base_url = base_url
        self.api_url = f"{base_url}/chat/completions"
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "8192"))

    def get_max_tokens(self) -> int:
        return self.max_tokens

    def generate_response(self, messages, tools=None, silent=False):
        if not self.api_key:
            return ("❌ 未設定 OPENAI_API_KEY，無法使用雲端模型。"
                    "請設定金鑰,或用 /models switch llama 切回本地模型。", [])
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model_name, "messages": messages, "temperature": self.temperature}
        if tools:
            payload["tools"] = tools
        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=180)
            resp.raise_for_status()
            data = resp.json()
            choice = (data.get("choices") or [{}])[0]
            msg = choice.get("message", {}) or {}
            content = msg.get("content") or ""
            tool_calls = msg.get("tool_calls") or []
            if content and not silent:
                print(f"{Colors.GREY}{content}{Colors.RESET}")
            return content, tool_calls
        except Exception as e:
            err = f"❌ 雲端模型呼叫失敗：{e}"
            if not silent:
                print(f"{Colors.RED}{err}{Colors.RESET}")
            return err, []


adapter_registry.register(
    name="openai",
    description="OpenAI 相容雲端模型(需 OPENAI_API_KEY;OpenAI / OpenRouter / 自架端點皆可)",
    model_type="cloud",
    setup_fn=lambda: OpenAICompatAdapter(),
)
