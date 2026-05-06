# memory_provider.py
import json
import os
from abc import ABC, abstractmethod
from constants import get_memory_dir

class BaseMemoryProvider(ABC):
    @abstractmethod
    def save(self, session_id, data):
        pass

    @abstractmethod
    def load(self, session_id):
        pass

class JSONMemoryProvider(BaseMemoryProvider):
    """
    [實作] 負責在本地端以 JSON 格式讀寫記憶檔案。
    已整合 constants.py 確保路徑絕對安全。
    """
    def __init__(self, storage_dir=None):
        self.storage_dir = storage_dir if storage_dir else get_memory_dir()
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_file_path(self, session_id):
        return os.path.join(self.storage_dir, f"{session_id}.json")

    def save(self, session_id, data):
        file_path = self._get_file_path(session_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, session_id):
        file_path = self._get_file_path(session_id)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "summary": "",
            "history": []
        }