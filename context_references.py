# context_references.py
import os

class ContextReferences:
    """
    [資料參照層 - 企業解耦版]
    只負責做「倉庫管理員」：驗證本地檔案存在、讀取內容並暫存於記憶體。
    絕對不負責排版，將 Prompt 的組裝權力交還給上層引擎。
    """
    def __init__(self):
        # 暫存區結構：{ "檔名": "檔案原始內容字串" }
        self.active_references = {}

    def add_file(self, file_path: str) -> bool:
        """安全地讀取本地檔案並存入暫存區"""
        if not os.path.exists(file_path):
            print(f"[警告] 倉庫管理員找不到檔案: {file_path}")
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            filename = os.path.basename(file_path)
            self.active_references[filename] = content
            print(f"📄 倉庫已收入檔案: {filename} (長度: {len(content)} 字元)")
            return True
            
        except UnicodeDecodeError:
            print(f"[錯誤] {file_path} 不是純文字檔案，拒絕收入。")
            return False
        except Exception as e:
            print(f"[錯誤] 讀取檔案 {file_path} 發生異常: {e}")
            return False

    def remove_file(self, filename: str):
        """從暫存區卸載指定的檔案"""
        if filename in self.active_references:
            del self.active_references[filename]
            print(f"🗑️ 倉庫已清出檔案: {filename}")

    def clear_all(self):
        """清空整個倉庫的參照檔案"""
        self.active_references.clear()

    def get_raw_data(self) -> dict:
        """
        【架構解耦核心】
        只交出「原始資料」，絕對不包含 Markdown 或 XML 等排版標籤。
        上層的 Engine 會呼叫這支 API，拿走資料後自己去組裝 Prompt。
        """
        return self.active_references