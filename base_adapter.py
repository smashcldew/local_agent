# base_adapter.py
import requests
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """
    Ollama 轉接器的抽象基底類別 (合約)。
    定義了所有本地模型都必須具備的基本屬性與行為。
    """
    def __init__(self, model_name, host="http://localhost:11434", temperature=0.5):
        self.model_name = model_name
        self.api_url = f"{host}/api/chat"
        self.temperature = temperature

    @abstractmethod
    def generate_response(self, messages, tools=None, silent=False):
        """
        [強制合約]
        任何繼承此類別的 Adapter，都必須實作這個方法。
        負責處理實際的網路請求與錯誤捕捉。
        silent=True 時，代表這是背景任務，請勿在終端機印出任何文字。
        """
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """
        [強制合約]
        回傳該模型支援的最大上下文預算。
        壓縮機將依賴此數值來判斷是否需要裁切對話。
        """
        pass