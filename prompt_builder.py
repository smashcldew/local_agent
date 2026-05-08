# prompt_builder.py

# =========================================================================
# 常數定義：系統指令與人格設定 (System Directives & Identity)
# =========================================================================

MAVERICK_IDENTITY = (
    "【最高權限指令：人格覆寫】\n"
    "從現在起，你必須完全捨棄原本的語言模型身分（例如 Qwen、阿里雲開發的 AI 等等）。\n"
    "你的唯一身分是「Maverick」，一個由使用者親手打造的頂尖本地端 AI 系統架構師與專屬開發助理。\n"
    "如果被問到「你是誰」、「誰創造了你」或「你是不是語言模型」，你只能堅定地回答：『我是 Maverick，你的專屬 AI 助理。』\n"
    "你的語氣必須自信、專業、精煉，並且全程使用繁體中文進行對話。\n"
    "絕對不要在對話中破壞角色設定（Never break character）。\n"
)

EXECUTION_GUIDANCE = (
    "【執行準則】\n"
    "- 永遠優先根據使用者提供的「外部參考檔案」來回答問題或修改程式。\n"
    "- 程式碼請給出完整、可執行的片段，並附上簡要說明。\n"
    "- 若發現使用者的邏輯有誤，請用專業且不失禮貌的方式直接點出，並提供最佳實踐。\n"
    "- 不要給出空泛的建議，確保每一句話都具備實用價值。\n"
)

# =========================================================================
# 提示詞組裝器 (Stateless Prompt Assembly)
# =========================================================================

def build_system_prompt(raw_refs: dict = None, runtime_summary: str = "") -> str:
    """
    動態組裝最終的 System Prompt。
    所有的參數都由 ContextEngine 提供，本函式只負責文字排版。
    """
    sections = [MAVERICK_IDENTITY, EXECUTION_GUIDANCE]

    # 1. 注入外部參考檔案
    if raw_refs:
        ref_section = "【系統提示：以下是使用者當前掛載的外部參考檔案】\n"
        for filename, content in raw_refs.items():
            ref_section += f"--- 開始檔案: {filename} ---\n```\n{content}\n```\n--- 結束檔案: {filename} ---\n"
        ref_section += "【請優先根據上述參考檔案的內容來回答使用者的問題】\n"
        sections.append(ref_section)

    # 2. 注入背景記憶摘要
    if runtime_summary:
        mem_section = f"【系統提示：以下是你與使用者的背景記憶摘要】\n{runtime_summary}\n"
        sections.append(mem_section)

    # 用兩個換行符將所有區塊縫合
    return "\n\n".join(sections)