# base_adapter.py
import requests
from abc import ABC, abstractmethod

class BaseOllamaAdapter(ABC):
    """
    Ollama 轉接器的抽象基底類別 (合約)。
    定義了所有本地模型都必須具備的基本屬性與行為。
    """
    def __init__(self, model_name, host="http://localhost:11434", temperature=0.7):
        self.model_name = model_name
        self.api_url = f"{host}/api/chat"
        self.temperature = temperature

    @abstractmethod
    def generate_response(self, messages):
        """
        [強制合約]
        任何繼承此類別的 Adapter，都必須實作這個方法。
        負責處理實際的網路請求與錯誤捕捉。
        """
        pass