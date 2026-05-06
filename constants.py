# constants.py
import os
from pathlib import Path

def get_maverick_home() -> Path:
    """
    [企業級路徑管理]
    取得 Maverick 的全局基礎目錄。
    預設為 ~/.maverick/。支援透過環境變數 MAVERICK_HOME 覆寫。
    """
    # 如果使用者有設定環境變數，優先使用環境變數
    env_home = os.getenv("MAVERICK_HOME")
    if env_home:
        base_path = Path(env_home)
    else:
        # 預設放在使用者的家目錄下 (Windows: C:\Users\xxx\.maverick, Mac/Linux: ~/.maverick)
        base_path = Path.home() / ".maverick"
        
    # 確保基礎目錄存在
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path

def get_memory_dir() -> Path:
    """取得記憶體專用的儲存目錄"""
    memory_path = get_maverick_home() / "memory"
    memory_path.mkdir(parents=True, exist_ok=True)
    return memory_path

def display_maverick_home() -> str:
    """
    用於在終端機印給使用者看的友善路徑。
    (對齊 Hermes 的 display_hermes_home 規範)
    """
    home_str = str(get_maverick_home())
    user_home = str(Path.home())
    # 如果路徑在使用者的家目錄下，將其簡化為 ~ 符號
    if home_str.startswith(user_home):
        return home_str.replace(user_home, "~", 1)
    return home_str