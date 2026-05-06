# memory_manager.py
from memory_provider import JSONMemoryProvider, BaseMemoryProvider

# (用不到先註解) 企業級所需的擴充套件
# from typing import List, Dict, Optional
# import logging

class MemoryManager:
    """
    [Hermes 完整記憶管理層]
    負責業務邏輯的封裝。大腦引擎 (Context Engine) 只與本類別溝通，
    絕對不直接接觸底層的 Provider。
    """
    def __init__(self, provider: BaseMemoryProvider = None):
        # 依賴注入 (Dependency Injection)：
        # 預設使用 JSON 提供者，未來如果想換資料庫，只要在這裡改掉就好。
        self.provider = provider or JSONMemoryProvider()
        
        # (用不到先註解) 日誌追蹤系統
        # self.logger = logging.getLogger(__name__)

    # ==========================================
    # 核心基礎功能 (目前啟用)
    # ==========================================
    def save_session(self, session_id: str, summary_text: str, chat_history: list):
        """將『長期記憶(摘要)』與『短期記憶(對話)』打包，交由 Provider 存檔"""
        data = {
            "summary": summary_text,
            "history": chat_history
        }
        self.provider.save(session_id, data)

    def load_session(self, session_id: str) -> dict:
        """向 Provider 索取指定專案的記憶資料"""
        return self.provider.load(session_id)

    # ==========================================
    # 進階企業功能藍圖 (用不到先註解)
    # ==========================================
    
    # def delete_session(self, session_id: str) -> bool:
    #     """刪除整個專案的記憶 (GDPR 刪除權 / 硬碟空間清理)"""
    #     # return self.provider.delete(session_id)
    #     pass

    # def list_all_sessions(self) -> list:
    #     """列出所有存在的對話專案，可用於前端 UI 的歷史紀錄選單"""
    #     # return self.provider.list_sessions()
    #     pass

    # def export_session(self, session_id: str, format_type: str = "markdown") -> str:
    #     """將記憶匯出成人類可讀的檔案 (支援 JSON, Markdown)"""
    #     pass

    # async def async_save_session(self, session_id: str, summary_text: str, chat_history: list):
    #     """非同步儲存，提供給未來的高併發 Multi-Agent 或 API 伺服器使用"""
    #     # await self.provider.async_save(session_id, data)
    #     pass