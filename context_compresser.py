# context_compresser.py
from usage_estimate import TokenEstimator

class ContextCompresser:
    """
    [企業級上下文壓縮機]
    結合 TokenEstimator，執行「掐頭去尾留中間」的精準記憶修剪。
    """
    def __init__(self, llm_adapter=None):
        self.llm_adapter = llm_adapter
        self.estimator = TokenEstimator(llm_adapter=self.llm_adapter)

    def compress(self, old_summary: str, history: list, keep_head_turns: int = 2):
        if not self.llm_adapter:
            print("[警告] ContextCompresser 未掛載 LLM Adapter，放棄壓縮。")
            return old_summary, history
            
        if len(history) <= keep_head_turns:
            return old_summary, history

        # 向精算師請請款：取得動態預算
        tail_token_budget = self.estimator.calculate_tail_budget()
        print(f"\n⏳ [上下文壓縮機] 啟動。精算師核准尾部預算: {tail_token_budget} Tokens...")

        head_msgs = history[:keep_head_turns]
        remaining_msgs = history[keep_head_turns:]
        
        tail_msgs = []
        middle_msgs = []
        current_tail_tokens = 0
        budget_exceeded = False
        
        for msg in reversed(remaining_msgs):
            if not budget_exceeded:
                # 請精算師幫忙算這句話多長
                msg_tokens = self.estimator.estimate_tokens(msg['content'])
                if current_tail_tokens + msg_tokens <= tail_token_budget:
                    tail_msgs.insert(0, msg)
                    current_tail_tokens += msg_tokens
                else:
                    budget_exceeded = True
                    middle_msgs.insert(0, msg)
            else:
                middle_msgs.insert(0, msg)
                
        if not middle_msgs:
            return old_summary, history

        print(f"✂️ 結算：尾部消耗了 {current_tail_tokens} 預算，{len(middle_msgs)} 筆歷史移交壓縮。")

        middle_text = ""
        for msg in middle_msgs:
            role = "使用者" if msg['role'] == 'user' else "AI"
            middle_text += f"[{role}]: {msg['content']}\n"

        # 這裡未來可以移到 prompts/ 資料夾
        prompt = f"""
        你是一個專業的記憶總結助理。請將以下的「舊的摘要」與「一段過去的對話紀錄」進行融合，
        生成一份全新、完整的背景摘要。
        
        【規則】：
        1. 用客觀的第三人稱描述。
        2. 務必保留舊摘要中的關鍵資訊，並加入新對話中的重要結論與進度。
        3. 直接輸出新的摘要內容，不要包含任何開場白或結語。
        
        【舊的摘要】：
        {old_summary if old_summary else '目前尚無摘要。'}
        
        【過去的對話紀錄】：
        {middle_text}
        """

        messages = [{"role": "user", "content": prompt}]
        try:
            new_summary = self.llm_adapter.generate_response(messages)
            new_summary = new_summary.strip()
        except Exception as e:
            print(f"[警告] 壓縮過程中發生錯誤: {e}。退回舊記憶。")
            return old_summary, history

        pruned_history = head_msgs + tail_msgs
        
        return new_summary, pruned_history