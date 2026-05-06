# test_memory_manager.py
import os
import shutil
from memory_manager import MemoryManager
from memory_provider import JSONMemoryProvider

def run_tests():
    print("=== 🚀 開始測試 memory_manager.py ===")
    
    # 建立測試環境
    test_dir = "test_manager_db"
    test_provider = JSONMemoryProvider(storage_dir=test_dir)
    # 將測試用的 Provider 注入給 Manager
    manager = MemoryManager(provider=test_provider)
    test_session = "manager_test_001"
    
    try:
        # ---------------------------------------------------------
        # 測試 1：透過 Manager 儲存資料
        # ---------------------------------------------------------
        print("\n⏳ [1/2] 測試 Manager 打包與存檔能力...")
        fake_summary = "Manager 測試摘要"
        fake_history = [{"role": "user", "content": "測試 Manager"}]
        
        manager.save_session(test_session, fake_summary, fake_history)
        
        # 驗證底層檔案是否真的產生了
        file_path = os.path.join(test_dir, f"{test_session}.json")
        assert os.path.exists(file_path), "Manager 未能成功呼叫 Provider 建立檔案"
        print("✅ 測試通過：Manager 成功指揮 Provider 完成寫入。")

        # ---------------------------------------------------------
        # 測試 2：透過 Manager 讀取資料
        # ---------------------------------------------------------
        print("\n⏳ [2/2] 測試 Manager 讀取與解包能力...")
        loaded_data = manager.load_session(test_session)
        
        assert loaded_data["summary"] == fake_summary, "讀取的摘要與寫入不符"
        assert len(loaded_data["history"]) == 1, "歷史紀錄長度不符"
        print("✅ 測試通過：Manager 成功讀取並回傳正確資料結構。")

    except AssertionError as e:
        print(f"\n❌ 測試失敗 (AssertionError): {e}")
        print("請標示為 `TASK_NOT_DONE_YET`。")
        return
    except Exception as e:
        print(f"\n❌ 發生未預期錯誤: {e}")
        print("請標示為 `TASK_NOT_DONE_YET`。")
        return
    finally:
        # 清理測試環境
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

    print("\n🎉 所有測試皆已通過！")

if __name__ == "__main__":
    run_tests()