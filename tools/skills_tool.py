# tools/skills_tool.py
#
# 把技能系統接成工具,讓模型能「列出技能」與「按需載入某個技能的完整步驟」。
# 參考 NousResearch/hermes-agent (MIT) 的 skills_list / skill_view 工具。
# 參見 LICENSES/hermes-agent-MIT.txt
from tools.registry import registry
from skills import SkillManager

_manager = SkillManager()


def skill_list(args: dict = None) -> str:
    items = _manager.list_skills()
    if not items:
        return "目前沒有可用的技能。"
    return "可用技能:\n" + "\n".join(f"- {s['name']}: {s['description']}" for s in items)


def skill_view(args: dict) -> str:
    name = args.get("name", "") if isinstance(args, dict) else ""
    if not name:
        return "❌ 執行失敗：缺少 name 參數。"
    body = _manager.get_skill(name)
    if body is None:
        avail = ", ".join(s["name"] for s in _manager.list_skills()) or "(無)"
        return f"❌ 找不到技能「{name}」。可用技能:{avail}"
    return body


skill_list_schema = {
    "type": "function",
    "function": {
        "name": "skill_list",
        "description": "列出目前所有可用的技能(skill)及其用途說明。當不確定有哪些技能可用時先呼叫此工具。",
        "parameters": {"type": "object", "properties": {}},
    },
}

skill_view_schema = {
    "type": "function",
    "function": {
        "name": "skill_view",
        "description": "讀取某個技能的完整內容與步驟。當某個技能符合當前任務時,呼叫此工具取得它的詳細指引後再照做。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "技能名稱(由 skill_list 取得)"}
            },
            "required": ["name"],
        },
    },
}

registry.register("skill_list", skill_list_schema, lambda args, **kwargs: skill_list(args))
registry.register("skill_view", skill_view_schema, skill_view)
