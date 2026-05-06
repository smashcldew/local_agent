# cli.py
import sys
from memory_manager import MemoryManager
from context_compresser import ContextCompresser
from context_references import ContextReferences
from context_engine import ContextEngine
from run_agent import MaverickAgent
from commands import resolve_command, generate_help_text, COMMAND_REGISTRY

from display import Colors, print_banner, MaverickSpinner

# 載入你寫好的 Adapter
from qwen_adapter import QwenChatAdapter
from qwen3_coder_adapter import QwenCoderAdapter

class MaverickCLI:
    """外場經理：只負責處理終端機 I/O 與指令分發"""
    def __init__(self):
        # 預設大腦
        self.active_adapter = QwenAdapter()
        
        # 初始化核心引擎零件
        self.memory = MemoryManager(session_id="default")
        self.references = ContextReferences()
        self.compresser = ContextCompresser(llm_adapter=self.active_adapter)
        
        self.engine = ContextEngine(
            memory_manager=self.memory,
            compresser=self.compresser,
            references=self.references
        )
        
        # 實例化真正的 Agent
        self.agent = MaverickAgent(engine=self.engine, adapter=self.active_adapter)

    def run(self):
        print("==================================================")
        print("🚀 Maverick AI Core - Terminal Interface Initiated")
        print("==================================================")
        self.memory.load_session()
        print(f"[系統] 記憶載入完成。目前歷史對話: {len(self.memory.get_history())} 筆。")
        print("輸入 /help 或是 /h 來查看所有指令。\n")

        while True:
            try:
                user_input = input("\n[你] > ").strip()
                if not user_input:
                    continue

                # --- 指令攔截器 (Command Dispatcher) ---
                if user_input.startswith("/"):
                    canonical_cmd = resolve_command(user_input)
                    if not canonical_cmd:
                        print(f"⚠️ 未知指令。輸入 /help 查看說明。")
                        continue
                        
                    self._dispatch_command(canonical_cmd, user_input)
                    continue

                # --- 正式對話 (交給 Agent) ---
                print("\n[Maverick] > ", end="", flush=True)
                self.agent.chat(user_input)
                
            except KeyboardInterrupt:
                print("\n[系統] 偵測到中斷訊號，Maverick 強制關機。")
                sys.exit(0)

    def _dispatch_command(self, canonical_cmd: str, raw_input: str):
        """指令分發邏輯"""
        parts = raw_input.split()

        if canonical_cmd == "exit":
            print("Maverick 關機中。下次見！")
            sys.exit(0)
            
        elif canonical_cmd == "help":
            print(generate_help_text())
            
        elif canonical_cmd == "ref":
            if len(parts) >= 3 and parts[1] == "add":
                self.references.add_file(parts[2])
            elif len(parts) >= 2 and parts[1] == "ls":
                refs = self.references.get_raw_data()
                print(f"📄 目前掛載了 {len(refs)} 個檔案:", list(refs.keys()))
            elif len(parts) >= 2 and parts[1] == "clear":
                self.references.clear_all()
                print("🗑️ 已清空所有掛載檔案。")
            else:
                print("⚠️ 參數錯誤。用法: /ref [add <檔名> | ls | clear]")
                
        elif canonical_cmd == "mode":
            if len(parts) >= 2 and parts[1] == "code":
                self.agent.set_adapter(QwenCoderAdapter())
                print("🧠 已切換至 Qwen Coder (程式開發模式，預算升級！)")
            elif len(parts) >= 2 and parts[1] == "chat":
                self.agent.set_adapter(QwenAdapter())
                print("🧠 已切換至 Qwen Chat (日常對話模式)")
            else:
                print("⚠️ 參數錯誤。用法: /mode [chat | code]")

if __name__ == "__main__":
    cli = MaverickCLI()
    cli.run()