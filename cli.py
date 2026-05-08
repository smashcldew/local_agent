# cli.py
import sys
from memory_manager import MemoryManager
from context_compresser import ContextCompresser
from context_references import ContextReferences
from context_engine import ContextEngine
from run_agent import MaverickAgent
from commands import resolve_command, generate_help_text

# 👉 匯入你的科技感視覺引擎
from display import Colors, print_banner

# 載入你寫好的 Adapter
from qwen_adapter import QwenAdapter
from qwen3_coder_adapter import QwenCoderAdapter

class MaverickCLI:
    """外場經理：只負責處理終端機 I/O 與指令分發"""
    def __init__(self):
        # 預設大腦
        self.active_adapter = QwenAdapter()
        
        # 1. 初始化底層無狀態零件
        self.memory = MemoryManager()
        self.references = ContextReferences()
        self.compresser = ContextCompresser(llm_adapter=self.active_adapter)
        
        # 2. 初始化中樞神經 (掌管對話進度與 Session)
        self.engine = ContextEngine(
            session_id="maverick_default_project",
            memory_manager=self.memory,
            compresser=self.compresser,
            references=self.references
        )
        
        # 3. 實例化真正的 Agent
        self.agent = MaverickAgent(engine=self.engine, adapter=self.active_adapter)

    def run(self):
        # 👉 呼叫超酷的橫幅 (這會取代原本那三行 ============ 的 print)
        print_banner()
        
        # 啟動時請引擎載入記憶
        self.engine.load_context()
        print(f"{Colors.GREY}[系統] 記憶載入完成。目前歷史對話: {len(self.engine.runtime_history)} 筆。{Colors.RESET}")

        while True:
            try:
                # 👉 加上綠色區分使用者的輸入視覺層次
                user_input = input(f"\n{Colors.PINK}[你] > {Colors.RESET}").strip()
                if not user_input:
                    continue

                # --- 指令攔截器 (Command Dispatcher) ---
                if user_input.startswith("/"):
                    canonical_cmd = resolve_command(user_input)
                    if not canonical_cmd:
                        print(f"{Colors.YELLOW}⚠️ 未知指令。輸入 /help 查看說明。{Colors.RESET}")
                        continue
                        
                    self._dispatch_command(canonical_cmd, user_input)
                    continue

                # --- 正式對話 (交給 Agent) ---
                # 👉 給 Maverick 的名字加上代表性的青色 (CYAN)
                print(f"\n{Colors.CYAN}[Maverick] > {Colors.RESET}", end="", flush=True)
                self.agent.chat(user_input)
                
            except KeyboardInterrupt:
                print(f"\n{Colors.RED}[系統] 偵測到中斷訊號，Maverick 強制關機。{Colors.RESET}")
                sys.exit(0)

    def _dispatch_command(self, canonical_cmd: str, raw_input: str):
        """指令分發邏輯"""
        parts = raw_input.split()

        if canonical_cmd == "exit":
            print(f"{Colors.GREY}Maverick 關機中。下次見！{Colors.RESET}")
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
                print(f"{Colors.YELLOW}⚠️ 參數錯誤。用法: /ref [add <檔名> | ls | clear]{Colors.RESET}")
                
        elif canonical_cmd == "mode":
            if len(parts) >= 2 and parts[1] == "code":
                new_adapter = QwenCoderAdapter()
                self.agent.set_adapter(new_adapter)
                self.engine.compresser.llm_adapter = new_adapter
                print(f"{Colors.CYAN}🧠 已切換至 Qwen Coder (程式開發模式，預算升級！){Colors.RESET}")
                
            elif len(parts) >= 2 and parts[1] == "chat":
                new_adapter = QwenAdapter()
                self.agent.set_adapter(new_adapter)
                self.engine.compresser.llm_adapter = new_adapter
                print(f"{Colors.CYAN}🧠 已切換至 Qwen Chat (日常對話模式){Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠️ 參數錯誤。用法: /mode [chat | code]{Colors.RESET}")

        elif canonical_cmd == "new":
            self.engine.clear_history()
            print(f"{Colors.MAGENTA}✨ 記憶已斬斷！Maverick 已準備好迎接全新的話題。{Colors.RESET}")
        
        elif canonical_cmd == "session":
            if len(parts) >= 3 and parts[1] == "switch":
                new_session_id = parts[2]
                
                # 1. 物理存檔：將當前話題安全寫入原本的 JSON 檔
                self.engine.save_context()
                
                # 2. 切換軌道：替換引擎的 Session ID
                self.engine.session_id = new_session_id
                
                # 3. 清空內存：把當前記憶體內的舊對話徹底清除，防止話題污染
                self.engine.runtime_history = []
                self.engine.runtime_summary = ""
                
                # 4. 重新載入：呼叫記憶管理員，載入新 Session 的歷史紀錄
                self.engine.load_context()
                
                print(f"\n{Colors.CYAN}🔄 已成功切換至專案空間: [{new_session_id}]{Colors.RESET}")
                print(f"{Colors.GREY}[系統] 載入該專案歷史對話: {len(self.engine.runtime_history)} 筆。{Colors.RESET}")
            
            elif len(parts) >= 2 and parts[1] in ["ls", "list"]:
                sessions = self.memory.list_all_sessions()
                if not sessions:
                    print(f"{Colors.YELLOW}📂 目前沒有任何存檔的專案。{Colors.RESET}")
                else:
                    print(f"\n{Colors.CYAN}📂 目前存在的專案空間 (Sessions):{Colors.RESET}")
                    for s in sessions:
                        # 標示出哪一個是當前正在使用的
                        if s == self.engine.session_id:
                            print(f"  {Colors.GREEN}➜ {s} (當前){Colors.RESET}")
                        else:
                            print(f"    {s}")
                    print() # 換行美化

            else:
                print(f"{Colors.YELLOW}⚠️ 參數錯誤。用法: /session switch <專案名稱>{Colors.RESET}")

if __name__ == "__main__":
    cli = MaverickCLI()
    cli.run()