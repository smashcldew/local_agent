# run_agent.py

class MaverickAgent:
    """
    [代理人核心迴圈]
    純粹的商業邏輯層。不負責任何 print() 或 UI 渲染！
    """
    def __init__(self, engine, adapter):
        self.engine = engine
        self.adapter = adapter

    def chat(self, user_input: str) -> str:
        """
        執行單次對話回合，回傳 AI 的文字回覆
        """
        # 1. 將使用者的話寫入記憶
        self.engine.memory.add_message("user", user_input)
        
        # 2. 透過 Context Engine 編譯出不會爆 VRAM 的提示詞陣列
        safe_context = self.engine.compile_context()
        
        # 3. 呼叫大腦推論
        response_text = self.adapter.generate_response(safe_context)
        
        # 4. 記錄 AI 的回答並存檔
        self.engine.memory.add_message("assistant", response_text)
        self.engine.memory.save_session()
        
        return response_text