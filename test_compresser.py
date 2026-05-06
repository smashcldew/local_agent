# test_context_compresser.py
from context_compresser import ContextCompresser

class DummyAdapter:
    """測試專用的大腦，現在它也具備告訴精算師自己極限的能力了"""
    def get_max_tokens(self) -> int:
        return 8192 # 模擬 Qwen 預設的 8K 視窗

    def generate_response(self, messages: list) -> str:
        prompt_content = messages[0]['content']
        
        # 嚴格驗證送進去壓縮的內容
        assert "無關緊要的廢話1" in prompt_content, "中間的對話沒有被送去壓縮"
        assert "無關緊要的廢話2" in prompt_content, "中間的對話沒有被送去壓縮"
        assert "超巨大的怪獸訊息" in prompt_content, "超過尾部預算的長對話，應該被踢到中間去壓縮"
        
        # 頭部絕對不能被壓縮
        assert "最初的目標" not in prompt_content, "頭部對話不應該被送去壓縮"
        
        # 尾部在預算內的不能被壓縮
        assert "最新的問題" not in prompt_content, "尾部預算內的對話不應該被送去壓縮"
        
        return "這是一段經過 Token 預算演算法濃縮後的新摘要。"

def run_tests():
    print("=== 🚀 開始測試 context_compresser.py (精算師架構版) ===")
    
    dummy_brain = DummyAdapter()
    compresser = ContextCompresser(llm_adapter=dummy_brain)
    
    try:
        # 建立一組模擬對話
        fake_history = [
            # 頭部 (保留 2 筆)
            {"role": "user", "content": "這是頭部：最初的目標"},
            {"role": "assistant", "content": "這是頭部：好的，我記住了"},
            
            # 中間 (準備被壓縮)
            {"role": "user", "content": "這是中間：無關緊要的廢話1"},
            {"role": "assistant", "content": "這是中間：好的"},
            {"role": "user", "content": "這是中間：無關緊要的廢話2"},
            
            # 關鍵！我們創造一個超過 8000 字元的超長訊息 (絕對會撐爆精算師給的 4000 預算)
            {"role": "assistant", "content": "超巨大的怪獸訊息" * 1000}, 
            
            # 尾部 (最新的對話，預算內絕對塞得下)
            {"role": "user", "content": "這是尾部：最新的問題"},
            {"role": "assistant", "content": "這是尾部：我來回答你"}
        ]
        
        old_summary = "這是一個專案。"
        
        print("\n⏳ 測試「精算師動態預算與陣列切片」邏輯...")
        
        # 注意！這裡不用再傳入 tail_token_budget 了，壓縮機會自己去問精算師！
        new_summary, pruned_history = compresser.compress(
            old_summary, 
            fake_history, 
            keep_head_turns=2
        )
        
        # 驗證 1：摘要是否更新
        assert new_summary == "這是一段經過 Token 預算演算法濃縮後的新摘要。", "摘要未正確更新"
        
        # 驗證 2：修剪後的陣列內容是否正確 (頭 2 + 尾 2 = 4)
        assert len(pruned_history) == 4, f"修剪後的陣列長度不正確，預期為 4，實際為 {len(pruned_history)}"
        
        # 驗證 3：確保最胖的那筆對話被拔掉了
        for msg in pruned_history:
            assert "怪獸訊息" not in msg['content'], "超出預算的超長對話沒有被剔除"
            
        # 驗證 4：陣列內容是否精準保留了頭跟尾
        assert "最初的目標" in pruned_history[0]['content'], "頭部資料遺失"
        assert "最新的問題" in pruned_history[-2]['content'], "尾部資料遺失"
        
        print("✅ 測試通過：精算師成功發揮作用，演算法完美分離並保護了記憶！")

    except AssertionError as e:
        print(f"\n❌ 測試失敗 (AssertionError): {e}")
        return
    except Exception as e:
        print(f"\n❌ 發生未預期錯誤: {e}")
        return

    print("\n🎉 所有測試皆已通過！")

if __name__ == "__main__":
    run_tests()