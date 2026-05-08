# context_engine.py

class ContextEngine:
    """
    [上下文編譯引擎 - 企業解耦版]
    掌管「運行時 (Runtime)」的記憶體狀態。
    負責向底層無狀態的 MemoryManager 讀寫資料，並統整所有零件以產出最終 Prompt。
    """
    def __init__(self, session_id: str, memory_manager, compresser, references):
        self.session_id = session_id
        self.memory_manager = memory_manager
        self.compresser = compresser
        self.references = references
        
        # 引擎負責自己保管當前對話的狀態
        self.runtime_summary = ""
        self.runtime_history = []

    def load_context(self):
        """從無狀態的 Manager 喚醒持久化記憶"""
        data = self.memory_manager.load_session(self.session_id)
        self.runtime_summary = data.get("summary", "")
        self.runtime_history = data.get("history", [])

    def save_context(self):
        """將運行時狀態打包，交給 Manager 寫入硬碟"""
        self.memory_manager.save_session(
            self.session_id, 
            self.runtime_summary, 
            self.runtime_history
        )

    def add_message(self, role: str, content: str, **kwargs):
        """供外部 (Agent) 新增對話 並支援工具呼叫"""
        msg = {"role": role, "content": content}
        msg.update(kwargs)
        self.runtime_history.append(msg)

    def _build_system_prompt(self) -> str:
        prompt = (
            "你是一個名為 Maverick 的頂尖 AI 系統架構師與開發助理。\n"
            "請用專業、簡潔的繁體中文回答。\n\n"
            "【最高行為準則：主動使用工具 (TOOL USE ENFORCEMENT)】\n"
            "你目前運行在本地終端機環境中，且配備了多種強大的實體工具。\n"
            "1. 當使用者要求你「查看檔案」、「讀取程式碼」或執行任何需要外部資訊的任務時，你 **絕對禁止** 說「我無法存取」、「我沒有權限」或「請你把代碼貼給我」。\n"
            "2. 你 **必須** 立即且優先使用系統提供的工具（如 read_local_file）來獲取資訊。\n"
            "3. 不要向使用者解釋你「打算」怎麼做，不要廢話，現在、立刻、馬上呼叫工具\n"
            "4. 當使用檔案工具時，請「精準」使用使用者提供的相對路徑或檔名，絕對禁止自行腦補或虛構絕對路徑（例如 /path/to/）。\n"
            "5. 【危險警告】當使用寫入檔案工具 (write_local_file) 時，你輸出的 content 必須是該檔案的「完整程式碼」。絕對禁止使用「// ... 保留原有程式碼 ...」等省略寫法，否則會毀掉使用者的檔案！\n"
        )
        
        raw_refs = self.references.get_raw_data()
        if raw_refs:
            prompt += "【系統提示：以下是使用者當前掛載的外部參考檔案】\n"
            for filename, content in raw_refs.items():
                prompt += f"--- 開始檔案: {filename} ---\n```\n{content}\n```\n--- 結束檔案: {filename} ---\n\n"
            prompt += "【請優先根據上述參考檔案的內容來回答使用者的問題】\n\n"
            
        if self.runtime_summary:
            prompt += f"【系統提示：以下是你與使用者的背景記憶摘要】\n{self.runtime_summary}\n\n"
            
        return prompt

    def compile_context(self) -> list:
        # 1. 強制通過防護網：上下文壓縮機
        new_summary, pruned_history = self.compresser.compress(
            old_summary=self.runtime_summary, 
            history=self.runtime_history,
            keep_head_turns=2
        )

        # 2. 如果被裁切了，更新引擎內的 Runtime 狀態，並自動同步到硬碟
        if len(pruned_history) != len(self.runtime_history):
            self.runtime_summary = new_summary
            self.runtime_history = pruned_history
            self.save_context()

        # 3. 組裝最終的 Safe Context Array
        safe_messages = [{"role": "system", "content": self._build_system_prompt()}]
        safe_messages.extend(self.runtime_history)

        return safe_messages
    
    def clear_history(self):
        """
        手動切斷短期記憶，用於切換全新話題。
        我們只清空 history，保留 summary (長期背景設定)，
        如果連 summary 都想清，可以把 self.runtime_summary = "" 也加上。
        """
        self.runtime_history = []
        self.save_context() # 同步更新到硬碟，避免下次載入又跑出來