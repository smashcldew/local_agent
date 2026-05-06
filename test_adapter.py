# test_adapter.py
from qwen_adapter import QwenChatAdapter
from qwen3_coder_adapter import QwenCoderAdapter

def main():
    print("=== 🚀 開始測試 Maverick 雙核心大腦 ===\n")

    # ---------------------------------------------------------
    # 測試一：通用對話大腦 (Qwen Chat)
    # ---------------------------------------------------------
    print("⏳ [1/2] 正在喚醒 Qwen Chat (通用對話模型)...")
    try:
        chat_adapter = QwenChatAdapter()
        # 準備一個簡單的問題
        chat_messages = [{"role": "user", "content": "你好，請用短短一句話跟你的開發者打招呼！"}]
        
        # 發送請求
        chat_response = chat_adapter.generate_response(chat_messages)
        
        print("✅ Qwen Chat 測試成功！")
        print(f"💬 模型回應: {chat_response}\n")
    except Exception as e:
        print(f"❌ Qwen Chat 測試失敗: {e}\n")

    # ---------------------------------------------------------
    # 測試二：程式專精大腦 (Qwen Coder)
    # ---------------------------------------------------------
    print("⏳ [2/2] 正在喚醒 Qwen Coder (程式專精模型)...")
    try:
        coder_adapter = QwenCoderAdapter()
        # 準備一個程式相關的問題
        coder_messages = [{"role": "user", "content": "請只給我一行 Python 程式碼，用來印出 'Hello Maverick'，不要寫其他解釋。"}]
        
        # 發送請求
        coder_response = coder_adapter.generate_response(coder_messages)
        
        print("✅ Qwen Coder 測試成功！")
        print(f"💻 模型回應: {coder_response}\n")
    except Exception as e:
        print(f"❌ Qwen Coder 測試失敗: {e}\n")

    print("=== 測試結束 ===")

if __name__ == "__main__":
    main()