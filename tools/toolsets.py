# tools/toolsets.py
#
# 工具分組。參考 NousResearch/hermes-agent (MIT) 的 toolsets.py:
# 以具名清單決定哪些工具送進 prompt。核心理念——每個 tool 每次 API 呼叫都會送出,
# 所以要能按情境只給必要的工具,控制 context 長度與風險。
# 參見 LICENSES/hermes-agent-MIT.txt

# 具名工具群組:名稱 -> 該群組包含的工具名稱(需與各工具 register 的 name 一致)。
TOOLSETS = {
    # 完整工具(等同不指定)
    "full":     ["read_local_file", "write_local_file", "search_web", "skill_list", "skill_view"],
    # 核心:讀寫檔 + 搜尋 + 技能
    "core":     ["read_local_file", "write_local_file", "search_web", "skill_list", "skill_view"],
    # 唯讀:不含任何會改動檔案的工具,適合只做查詢/分析的情境(技能為唯讀,保留)
    "readonly": ["read_local_file", "search_web", "skill_list", "skill_view"],
    # 純對話:完全不給工具
    "chat":     [],
}

# 預設群組(None 代表「全部已註冊的工具」,見 registry.get_schemas)
DEFAULT_TOOLSET = "full"


def resolve(name):
    """把 toolset 名稱解析成工具名稱清單。未知名稱回傳 None(由呼叫端決定如何處理)。"""
    if name is None:
        return None
    return TOOLSETS.get(name)


def list_toolsets():
    """回傳所有群組的淺拷貝,供 UI 列印。"""
    return {k: list(v) for k, v in TOOLSETS.items()}
