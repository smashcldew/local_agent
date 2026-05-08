# qwen_adapter.py
import json
import requests
from base_adapter import BaseAdapter
from display import MaverickSpinner, Colors

class QwenAdapter(BaseAdapter):
    def __init__(self, host="http://localhost:11434"):
        # 🌟 確定掛載官方支援 Tool Calling 的大腦！
        super().__init__(model_name="qwen2.5:7b", host=host, temperature=0.5)
        self.max_tokens = 4096  

    def get_max_tokens(self) -> int:
        return self.max_tokens

    def generate_response(self, messages, tools=None, silent=False): # 🌟 1. 新增 silent 參數
        use_stream = False if tools else True

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": use_stream,
            "options": {
                "temperature": self.temperature,
                "num_ctx" : self.max_tokens,
                "num_predict" : 2048,
                "repeat_penalty": 1.0
            }
        }
        
        if tools:
            payload["tools"] = tools

        # 🌟 2. 動態改變轉圈圈的提示文字
        spinner_text = "背景壓縮記憶中" if silent else "大腦推論中"
        spinner = MaverickSpinner(spinner_text)
        spinner.start()

        try:
            response = requests.post(self.api_url, json=payload, stream=use_stream, timeout=120)
            response.raise_for_status() 
            
            full_response = ""
            tool_calls_buffer = []  
            
            # --- 分支 A：串流模式 ---
            if use_stream:
                first_token_received = False
                for line in response.iter_lines():
                    if line:
                        # 🌟 3. 如果是前景聊天，收到第一個字就停掉動畫；如果是背景靜音，就讓它繼續轉！
                        if not first_token_received and not silent:
                            spinner.stop()
                            first_token_received = True
                            
                        chunk = json.loads(line)
                        msg = chunk.get("message", {})
                        
                        if "content" in msg and msg["content"]:
                            content = msg["content"]
                            # 🌟 4. 只有在非靜音狀態下才印出文字
                            if not silent:
                                print(content, end="", flush=True)
                            full_response += content
                
                # 🌟 5. 迴圈結束後，清理動畫與換行
                if silent:
                    spinner.stop() # 靜音模式在這裡才關閉動畫，畫面會瞬間乾淨
                elif not first_token_received:
                    spinner.stop()
                    
                if full_response and not silent:
                    print() 
                    
            # --- 分支 B：工具執行模式 ---
            else:
                spinner.stop() 
                result = response.json()
                msg = result.get("message", {})
                
                if "tool_calls" in msg:
                    tool_calls_buffer = msg["tool_calls"]
                    
                if "content" in msg and msg["content"]:
                    full_response = msg["content"]
                    if not silent: # 🌟 靜音防護
                        print(f"{Colors.GREY}{full_response}{Colors.RESET}")
            
            return full_response, tool_calls_buffer
            
        except requests.exceptions.Timeout:
            spinner.stop()
            error_msg = f"\n{Colors.RED}[系統錯誤] Qwen 思考超時，請重試。{Colors.RESET}"
            print(error_msg)
            return error_msg, []
            
        except Exception as e:
            spinner.stop()
            error_msg = f"\n{Colors.RED}[系統錯誤] Adapter 發生例外: {e}{Colors.RESET}"
            print(error_msg)
            return error_msg, []