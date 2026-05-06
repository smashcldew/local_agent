# qwen_adapter.py
import requests
from base_adapter import BaseOllamaAdapter

class QwenChatAdapter(BaseOllamaAdapter):
    """
    針對 Qwen 通用對話模型 (qwen3.5:9b) 的轉接器。
    目前降級為 qwen2.5:7b，因coder模型尚未載入。
    適合發想、校正與文字處理。
    """
    def __init__(self, host="http://localhost:11434"):
        super().__init__(model_name="qwen2.5:7b", host=host, temperature=0.5)

    def generate_response(self, messages):
        """履行合約：實作具體的網路請求邏輯"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status() 
            return response.json().get("message", {}).get("content", "")
            
        except requests.exceptions.Timeout:
            return "[系統錯誤] Qwen Chat 思考超時，請重試。"
        except requests.exceptions.RequestException as e:
            print(f"\n[錯誤] 無法連接到 Ollama 服務 ({self.api_url})")
            return "無法取得回應 (連線錯誤)。"