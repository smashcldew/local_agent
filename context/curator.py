# context/curator.py
#
# 記憶策展(memory curation)。參考 NousResearch/hermes-agent (MIT) 的 learning loop /
# curator 概念:把對話中「值得長期記住」的事實(使用者偏好、決定、專案事實)萃取出來,
# 融合進背景摘要,讓 agent 跨 session 記得你。
# 參見 LICENSES/hermes-agent-MIT.txt
#
# 與 ContextCompressor 的分工:
#   - Compressor:為了「省 token」把超出預算的中段歷史壓成摘要(被動、容量驅動)。
#   - Curator   :主動從整段對話萃取「該長期保留的重點」更新摘要(主動、價值驅動)。
# 兩者都把結果寫進同一個 runtime_summary。


class MemoryCurator:
    def __init__(self, llm_adapter=None):
        self.llm_adapter = llm_adapter

    def curate(self, old_summary: str, history: list, llm_adapter=None) -> str:
        """
        從 history 萃取長期重點,與 old_summary 融合成新的背景摘要並回傳。
        無可用 adapter 或無對話時,原樣回傳 old_summary(安全 no-op)。
        """
        adapter = llm_adapter or self.llm_adapter
        if not adapter or not history:
            return old_summary

        convo = ""
        for m in history:
            role = m.get("role")
            if role in ("user", "assistant"):
                who = "使用者" if role == "user" else "AI"
                convo += f"[{who}]: {m.get('content', '')}\n"
        if not convo.strip():
            return old_summary

        prompt = f"""你是一位記憶策展助理。請從下列對話中,萃取「值得長期記住」的重點
(例如:使用者的偏好與習慣、重要決定、專案事實與進度、需要延續的待辦),
並與既有的背景摘要融合成一份全新、精煉的背景摘要。

【規則】
1. 只保留長期有價值的資訊,捨棄一次性的閒聊與過程細節。
2. 保留既有摘要中仍然成立的重點,加入新對話中的新事實。
3. 用客觀第三人稱、條列式。直接輸出摘要內容,不要任何開場白或結語。

【既有背景摘要】
{old_summary if old_summary else '(目前尚無摘要)'}

【近期對話】
{convo}
"""
        try:
            new_summary, _ = adapter.generate_response(
                [{"role": "user", "content": prompt}], silent=True
            )
            new_summary = (new_summary or "").strip()
            return new_summary or old_summary
        except Exception:
            return old_summary
