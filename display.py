# display.py
import sys
import time
import threading

# 定義 ANSI 終端機顏色代碼
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    GREY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """印出帶有科技感的系統啟動橫幅"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print(" █▄ ▄█   ▄▀▀▄   ▀▄ ▄▀  █▀▀▀  █▀▀▄  ▀  ▄▀▀▀  █▄▀ ")
    print(" █ ▀ █  █▄▄▄▄█   ▐▄▌   █▀▀▀  █▄▄▀  █  █     █▀▄ ")
    print(" ▀   ▀  █    █    ▀    ▀▄▄▄  ▀  ▀▄ ▀   ▀▄▄▄ ▀  ▀")
    print(f"                                   AI Core v1.0{Colors.RESET}")
    print(f"{Colors.GREY}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.YELLOW}輸入 /help 或是 /h 來查看所有指令。{Colors.RESET}")
    print(f"{Colors.GREY}{'=' * 50}{Colors.RESET}\n")

class MaverickSpinner:
    """
    [多執行緒動畫] 
    在等待大腦推論 (Time-to-First-Token) 時顯示動態效果。
    """
    def __init__(self, message="思考中"):
        self.message = message
        self.is_running = False
        # 參考 Hermes 的 KawaiiSpinner 設計，加入一點動態感
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.thread = None

    def spin(self):
        i = 0
        while self.is_running:
            frame = self.frames[i % len(self.frames)]
            #  Hermes 規範：避免使用 \033[K 清除行，改用空白填充避免 prompt_toolkit 破圖
            sys.stdout.write(f"\r{Colors.MAGENTA}{frame} Maverick {self.message}...{' ' * 10}{Colors.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
        # 清除動畫，歸還乾淨的終端機行
        sys.stdout.write("\r" + " " * 40 + "\r")
        sys.stdout.flush()