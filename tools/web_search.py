# tools/web_search.py
from tools.registry import registry
from duckduckgo_search import DDGS

def search_web(args: dict) -> str:
    """執行 DuckDuckGo 網頁搜尋的處理函數"""
    query = args.get("query")
    # 預設抓前 3 筆，避免回傳太多 Token 塞爆大腦
    max_results = args.get("max_results", 3)

    if not query:
        return "❌ 執行失敗：缺少 query 參數。"

    try:
        with DDGS() as ddgs:
            # 執行文字搜尋
            results = list(ddgs.text(query, max_results=max_results))
            
        if not results:
            return f"找不到關於「{query}」的結果。"

        # 將結果格式化成易讀的字串給大腦
        output = f"🔍 搜尋「{query}」的結果：\n\n"
        for i, res in enumerate(results, 1):
            output += f"{i}. 【{res.get('title')}】\n"
            output += f"   🔗 連結：{res.get('href')}\n"
            output += f"   📄 摘要：{res.get('body')}\n\n"

        return output
        
    except Exception as e:
        return f"❌ 搜尋失敗：{e}"

# 定義給大腦看的 JSON Schema
search_schema = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "當需要查詢最新資訊、時事、天氣或你不知道的事實時，請使用此工具上網搜尋。會回傳包含標題、連結與摘要的搜尋結果。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "精準的搜尋關鍵字 (例如: 'FastAPI 最新版本' 或 '新竹 週末天氣')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "要獲取的搜尋結果數量，預設為 3"
                }
            },
            "required": ["query"]
        }
    }
}

# 註冊到中央註冊表
registry.register("search_web", search_schema, search_web)