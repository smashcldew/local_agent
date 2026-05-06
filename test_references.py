# test_context_references.py
import os
from context_references import ContextReferences

def run_tests():
    print("=== 🚀 開始測試 context_references.py (解耦版) ===")
    
    ref_manager = ContextReferences()
    test_file_name = "dummy_test_code.py"
    
    try:
        # 1. 準備一個純文字假檔案來測試
        with open(test_file_name, "w", encoding="utf-8") as f:
            f.write("def hello_world():\n    print('Hello')")

        # ---------------------------------------------------------
        # 測試 1：正常掛載檔案
        # ---------------------------------------------------------
        print("\n⏳ [1/3] 測試正常掛載檔案...")
        success = ref_manager.add_file(test_file_name)
        assert success is True, "檔案掛載失敗，回傳了 False"
        print("✅ 測試通過：倉庫成功收容檔案。")

        # ---------------------------------------------------------
        # 測試 2：驗證資料純淨度 (架構解耦的核心)
        # ---------------------------------------------------------
        print("\n⏳ [2/3] 測試索取原始資料 (確保無排版污染)...")
        raw_data = ref_manager.get_raw_data()
        
        assert test_file_name in raw_data, "字典中拿不到檔案的 Key"
        assert "def hello_world():" in raw_data[test_file_name], "字典中拿不到檔案的 Value (原始碼)"
        
        # 嚴格斷言：確保這裡面沒有寫死的 Markdown 標籤
        assert "--- 開始檔案" not in raw_data[test_file_name], "架構污染！資料中不應該包含排版標籤"
        print("✅ 測試通過：倉庫完美交出了純淨的原始字典。")

        # ---------------------------------------------------------
        # 測試 3：防呆機制 (讀取不存在的檔案)
        # ---------------------------------------------------------
        print("\n⏳ [3/3] 測試防呆機制 (讀取不存在的檔案)...")
        fail_result = ref_manager.add_file("not_exist_file.txt")
        assert fail_result is False, "讀取不存在的檔案應該要回傳 False"
        print("✅ 測試通過：防呆機制攔截成功。")

    except AssertionError as e:
        print(f"\n❌ 測試失敗 (AssertionError): {e}")
        return
    except Exception as e:
        print(f"\n❌ 發生未預期錯誤: {e}")
        return
    finally:
        # 清理測試環境
        if os.path.exists(test_file_name):
            os.remove(test_file_name)

    print("\n🎉 所有測試皆已通過！")

if __name__ == "__main__":
    run_tests()