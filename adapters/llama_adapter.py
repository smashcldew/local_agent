# adapters/llama_adapter.py
import json
import requests
from display import MaverickSpinner, Colors
from .base_adapter import BaseAdapter
from .registry import adapter_registry

class LlamaAdapter(BaseAdapter):
    """
    專屬於 Llama 的橋接器。
    """
    def __init__(self, host="http://localhost:11434"):
        super().__init__(model_name="llama3.1:8b", host=host, temperature=0.9)
        self.max_tokens = 8192

    def get_max_tokens(self) -> int:
        return self.max_tokens

    def generate_response(self, messages, tools=None, silent=False):
        use_stream = False if tools else True
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": use_stream,
            "options": {"temperature": self.temperature, "num_ctx": self.max_tokens}
        }
        if tools:
            payload["tools"] = tools

        spinner_text = "背景壓縮記憶中" if silent else f"{self.model_name} 推論中"
        spinner = MaverickSpinner(spinner_text)
        spinner.start()

        try:
            response = requests.post(self.api_url, json=payload, stream=use_stream, timeout=180)
            response.raise_for_status() 
            
            full_response = ""
            tool_calls_buffer = []  
            
            if use_stream:
                first_token = False
                for line in response.iter_lines():
                    if line:
                        if not first_token and not silent:
                            spinner.stop()
                            first_token = True
                        chunk = json.loads(line)
                        msg = chunk.get("message", {})
                        if "content" in msg and msg["content"]:
                            content = msg["content"]
                            if not silent:
                                print(content, end="", flush=True)
                            full_response += content
                if silent or not first_token:
                    spinner.stop() 
                if full_response and not silent:
                    print() 
            else:
                spinner.stop() 
                result = response.json()
                msg = result.get("message", {})
                if "tool_calls" in msg:
                    tool_calls_buffer = msg["tool_calls"]
                if "content" in msg and msg["content"]:
                    full_response = msg["content"]
                    if not silent: 
                        print(f"{Colors.GREY}{full_response}{Colors.RESET}")
            return full_response, tool_calls_buffer
            
        except Exception as e:
            spinner.stop()
            error_msg = f"\n{Colors.RED}[系統錯誤] {self.model_name} 發生例外: {e}{Colors.RESET}"
            print(error_msg)
            return error_msg, []

adapter_registry.register(
    name="llama",
    description="本地端 Llama 3.1",
    model_type="local",
    setup_fn=lambda: LlamaAdapter()
)