# commands.py
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class CommandDef:
    """[企業級指令定義] 參考 Hermes 的 Slash Command Registry"""
    name: str                  # 標準指令名稱 (不含斜線)
    description: str           # 說明文字
    aliases: Tuple[str, ...] = ()  # 縮寫/別名
    args_hint: str = ""        # 參數提示

# 全域指令註冊表
COMMAND_REGISTRY = [
    CommandDef("exit", "結束 Maverick 系統", aliases=("quit", "q")),
    CommandDef("ref", "管理外部參照檔案", aliases=("r",), args_hint="[add <檔名> | ls | clear]"),
    CommandDef("mode", "切換大腦模型 (對話/程式碼)", aliases=("m",), args_hint="[chat | code]"),
    CommandDef("help", "顯示此說明選單", aliases=("h", "?")),
    CommandDef("new", "開啟新話題 (清除短期對話記憶)", aliases=("clear", "c")),
    CommandDef("session", "切換對話專案/Session", aliases=("s", "sess"), args_hint="[switch <名稱>]"),
]

def resolve_command(cmd_str: str) -> Optional[str]:
    """將使用者輸入的指令 (可能是別名) 解析為標準名稱"""
    cmd_str = cmd_str.lower().strip()
    if cmd_str.startswith("/"):
        cmd_str = cmd_str[1:]
        
    # 取出第一個單字作為指令
    base_cmd = cmd_str.split()[0] if cmd_str else ""
    
    for cmd in COMMAND_REGISTRY:
        if base_cmd == cmd.name or base_cmd in cmd.aliases:
            return cmd.name
    return None

def generate_help_text() -> str:
    """動態生成 Help 說明文字"""
    lines = ["【Maverick 指令選單】"]
    for cmd in COMMAND_REGISTRY:
        aliases_str = f" (或 /{', /'.join(cmd.aliases)})" if cmd.aliases else ""
        lines.append(f"  /{cmd.name.ljust(6)} {cmd.args_hint.ljust(20)} - {cmd.description}{aliases_str}")
    return "\n".join(lines)