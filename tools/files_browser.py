# tools/files_browser.py
import os
from tools.registry import registry

def read_local_file(file_path: str) -> str:
    """真實被執行的 Python 函數：讀取本地檔案"""
    try:
        if not os.path.exists(file_path):
            return f"執行失敗：找不到檔案 {file_path}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 加上長度保護，避免單一檔案把 Token 預算全部吃光
            if len(content) > 3000:
                return content[:3000] + f"\n\n...[檔案過長，已截斷，原檔案大小: {len(content)} 字元]..."
            return content
    except Exception as e:
        return f"執行失敗：無法讀取檔案 ({str(e)})"

# 向中央註冊表報到
registry.register(
    name="read_local_file",
    schema={
        "type": "function",
        "function": {
            "name": "read_local_file",
            "description": "讀取並查看本地端電腦中的檔案內容。當需要了解程式碼或文件內容時使用此工具。必須提供正確的檔案路徑。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "檔案的絕對路徑或相對路徑"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    handler=lambda args, **kwargs: read_local_file(file_path=args.get("file_path", ""))
)