# usage_estimate.py

class TokenEstimator:
    """
    [系統精算師]
    負責估算 Token 使用量，以及為系統配置安全預算。
    與特定的 LLM 解耦，提供泛用的計算服務。
    """
    def __init__(self, llm_adapter=None):
        self.llm_adapter = llm_adapter
        
        # 企業級預算保留區 (可以根據專案需求隨時調整)
        self.RESERVE_GENERATION = 1000  # 預留給 AI 回答
        self.RESERVE_HEAD_SYS = 1000    # 預留給系統提示詞與人設
        self.RESERVE_TOOLS = 2000       # 預留給外部工具與 RAG 檢索

    def estimate_tokens(self, text: str) -> int:
        """
        粗略估算 Token 數量。
        未來若要更精準，可在此引入 tiktoken 模組。
        """
        # 保守估計：1 個字元 = 1 Token
        return len(text)

    def calculate_tail_budget(self) -> int:
        """
        動態計算尾部 (短期記憶) 的可用 Token 預算。
        """
        if not self.llm_adapter or not hasattr(self.llm_adapter, 'get_max_tokens'):
            # 防呆：無大腦時給予保守預設值
            return 4000 
            
        total_capacity = self.llm_adapter.get_max_tokens()
        
        # 扣除硬性保留區
        available_budget = total_capacity - self.RESERVE_GENERATION - self.RESERVE_HEAD_SYS - self.RESERVE_TOOLS
        
        # 終極防呆：確保預算不為負數，最低保障 1000
        return max(1000, available_budget)