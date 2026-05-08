# tools/file_editor.py
import os
from tools.registry import registry

def write_local_file(args: dict) -> str:
    """
    實體寫入檔案的處理函數。
    會自動建立不存在的父目錄。
    """
    file_path = args.get("file_path")
    content = args.get("content")

    if not file_path or content is None:
        return "❌ 執行失敗：缺少 file_path 或 content 參數。"

    try:
        # 自動建立不存在的資料夾 (例如：src/components/button.py -> 會自動建 src/components)
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # 以寫入模式 (w) 打開，這會完全覆蓋舊檔案
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"✅ 成功寫入檔案：{file_path} (共 {len(content)} 字元)"
    except Exception as e:
        return f"❌ 寫入失敗：{e}"

# 定義給大腦看的 JSON Schema
write_file_schema = {
    "type": "function",
    "function": {
        "name": "write_local_file",
        "description": "將文字或程式碼寫入指定的本地端檔案。如果檔案存在會「完全覆蓋」，如果目錄不存在會「自動建立」。",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要寫入的相對路徑 (例如: tools/test_script.py)"
                },
                "content": {
                    "type": "string",
                    "description": "要寫入檔案的「完整內容」。請勿省略任何程式碼，必須提供完整的字串。"
                }
            },
            "required": ["file_path", "content"]
        }
    }
}

# 註冊到中央註冊表
registry.register("write_local_file", write_file_schema, write_local_file)