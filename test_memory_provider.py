# test_memory_provider.py
import os
import shutil
from memory_provider import JSONMemoryProvider

def run_tests():
    print("=== 🚀 開始測試 memory_provider.py ===")
    
    # 使用一個專門的測試資料夾，避免污染未來真實的資料
    test_dir = "test_memory_db"
    provider = JSONMemoryProvider(storage_dir=test_dir)
    test_session = "test_session_001"
    
    try:
        # ---------------------------------------------------------
        # 測試 1：讀取不存在的檔案 (應該要回傳預設結構)
        # ---------------------------------------------------------
        print("\n⏳ [1/3] 測試讀取空專案...")
        empty_data = provider.load(test_session)
        assert empty_data["summary"] == "", "預設 summary 應該為空字串"
        assert empty_data["history"] == [], "預設 history 應該為空陣列"
        print("✅ 測試通過：空專案防呆機制正常。")

        # ---------------------------------------------------------
        # 測試 2：儲存資料到本地端
        # ---------------------------------------------------------
        print("\n⏳ [2/3] 測試寫入資料...")
        fake_data = {
            "summary": "這是一段測試用的記憶摘要。",
            "history": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好，我是 Maverick！"}
            ]
        }
        provider.save(test_session, fake_data)
        file_path = os.path.join(test_dir, f"{test_session}.json")
        assert os.path.exists(file_path), "JSON 檔案沒有被成功建立"
        print(f"✅ 測試通過：檔案已成功寫入 {file_path}")

        # ---------------------------------------------------------
        # 測試 3：再次讀取剛寫入的資料
        # ---------------------------------------------------------
        print("\n⏳ [3/3] 測試讀取已存在的資料...")
        loaded_data = provider.load(test_session)
        assert loaded_data["summary"] == fake_data["summary"], "讀取的摘要與寫入不符"
        assert len(loaded_data["history"]) == 2, "歷史紀錄長度不符"
        print("✅ 測試通過：資料讀取精準無誤。")

    except AssertionError as e:
        print(f"\n❌ 測試失敗 (AssertionError): {e}")
        print("請標示為 `TASK_NOT_DONE_YET`。")
        return
    except Exception as e:
        print(f"\n❌ 發生未預期錯誤: {e}")
        print("請標示為 `TASK_NOT_DONE_YET`。")
        return
    finally:
        # 測試結束後，清理測試用的資料夾
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

    print("\n🎉 所有測試皆已通過！")

if __name__ == "__main__":
    run_tests()