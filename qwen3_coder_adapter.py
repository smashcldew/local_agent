# qwen_coder_adapter.py
import json
import requests
from base_adapter import BaseAdapter
from display import MaverickSpinner  # 🌟 引入視覺動畫引擎

class QwenCoderAdapter(BaseAdapter):
    """
    針對 Qwen Coder 程式碼專精模型的轉接器。
    適合設計架構、解釋原理與程式除錯。
    """
    def __init__(self, host="http://localhost:11434"):
        # 溫度設為 0，確保程式碼生成的絕對穩定性與邏輯性
        super().__init__(model_name="qwen3.5:9b", host=host, temperature=0)
        self.max_tokens = 8192  # 🌟 Coder 專屬的雙倍預算

    # 👇 履行合約 1：提供預算資訊給壓縮機
    def get_max_tokens(self) -> int:
        """履行合約：回傳最大上下文預算"""
        return self.max_tokens

    # 👇 履行合約 2：實作網路請求 (升級為串流版)
    def generate_response(self, messages):
        """履行合約：實作具體的網路請求邏輯"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,  # 🌟 開啟串流
            "options": {
                "temperature": self.temperature
            }
        }

        # 🌟 啟動專屬的等待動畫
        spinner = MaverickSpinner("Coder 架構推演中")
        spinner.start()

        try:
            response = requests.post(self.api_url, json=payload, stream=True, timeout=120)
            response.raise_for_status() 
            
            full_response = ""
            first_token_received = False
            
            for line in response.iter_lines():
                if line:
                    # 🌟 收到第一個字元，關閉動畫
                    if not first_token_received:
                        spinner.stop()
                        first_token_received = True
                        
                    # 解析 JSON 並印出文字
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                        print(content, end="", flush=True)
                        full_response += content
            
            if not first_token_received:
                spinner.stop()
                
            print() 
            return full_response
            
        except requests.exceptions.Timeout:
            spinner.stop()
            return "[系統錯誤] Qwen Coder 思考超時，請重試。"
        except requests.exceptions.RequestException as e:
            spinner.stop()
            print(f"\n[錯誤] 無法連接到 Ollama 服務 ({self.api_url})")
            return "無法取得回應 (連線錯誤)。"
        except Exception as e:
            spinner.stop()
            return f"[系統錯誤] 發生未預期的例外: {e}"