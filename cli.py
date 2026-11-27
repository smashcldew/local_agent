# cli.py
import sys
from memory import MemoryManager
from context import ContextCompressor, ContextReferences, ContextEngine
from run_agent import MaverickAgent
from commands import resolve_command, generate_help_text

from display import Colors, print_banner

from adapters import adapter_registry

class MaverickCLI:
    """外場經理：只負責處理終端機 I/O 與指令分發"""
    def __init__(self):
        # 預設大腦
        self.active_model_name = "gpt-oss"
        self.active_adapter = adapter_registry.get_adapter(self.active_model_name)

        if not self.active_adapter:
            print(f"{Colors.RED}錯誤：找不到預設大腦 'gpt-oss'。請檢查 adapters/gpt-oss_adapter.py 是否已正確註冊。{Colors.RESET}")
            sys.exit(1)

        # 1. 初始化底層無狀態零件
        self.memory = MemoryManager()
        self.references = ContextReferences()
        self.compressor = ContextCompressor(llm_adapter=self.active_adapter)

        # 2. 初始化中樞神經 (掌管對話進度與 Session)
        self.engine = ContextEngine(
            session_id="maverick_default_project",
            memory_manager=self.memory,
            compressor=self.compressor,
            references=self.references
        )

        # 3. 實例化真正的 Agent
        self.agent = MaverickAgent(engine=self.engine, adapter=self.active_adapter)

    def run(self):
        print_banner()

        # 啟動時請引擎載入記憶
        self.engine.load_context()
        print(f"{Colors.GREY}[系統] 記憶載入完成。目前歷史對話: {len(self.engine.runtime_history)} 筆。{Colors.RESET}")

        while True:
            try:
                user_input = input(f"\n{Colors.PINK}[你] > {Colors.RESET}").strip()
                if not user_input:
                    continue

                # --- 指令攔截器 (Command Dispatcher) ---
                if user_input.startswith("/"):
                    canonical_cmd = resolve_command(user_input)
                    if not canonical_cmd:
                        print(f"{Colors.YELLOW}未知指令。輸入 /help 查看說明。{Colors.RESET}")
                        continue

                    self._dispatch_command(canonical_cmd, user_input)
                    continue

                # --- 正式對話 (交給 Agent) ---
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
                print(f"目前掛載了 {len(refs)} 個檔案:", list(refs.keys()))
            elif len(parts) >= 2 and parts[1] == "clear":
                self.references.clear_all()
                print("已清空所有掛載檔案。")
            else:
                print(f"{Colors.YELLOW}參數錯誤。用法: /ref [add <檔名> | ls | clear]{Colors.RESET}")

        elif canonical_cmd in ["model", "models"]:
            if len(parts) == 1 or parts[1] == "ls":
                print(f"\n{Colors.CYAN}=== 可用的模型型錄 ==={Colors.RESET}")
                models = adapter_registry.get_all_models()
                for name, info in models.items():
                    badge = "[雲端]" if info["type"] == "cloud" else "[本地]"
                    if name == self.active_model_name:
                        print(f"  {Colors.GREEN}➜ {Colors.YELLOW}{name:<13}{Colors.RESET} {badge} {info['description']} {Colors.GREEN}(當前){Colors.RESET}")
                    else:
                        print(f"    {Colors.YELLOW}{name:<13}{Colors.RESET} {badge} {info['description']}")
                print(f"{Colors.CYAN}========================={Colors.RESET}")
                print(f"提示：輸入 /models switch <名稱> 即可切換大腦。")

            elif len(parts) >= 3 and parts[1] == "switch":
                target_model = parts[2].lower()
                new_adapter = adapter_registry.get_adapter(target_model)

                if new_adapter:
                    print(f"{Colors.GREY}正在連線並切換大腦至 {target_model}...{Colors.RESET}")
                    self.active_model_name = target_model
                    self.active_adapter = new_adapter
                    self.agent.set_adapter(new_adapter)
                    self.engine.compressor.llm_adapter = new_adapter

                    print(f"{Colors.GREEN}成功切換！Maverick 現在使用 {target_model} 為您服務。{Colors.RESET}")
                else:
                    print(f"{Colors.RED}找不到模型 '{target_model}'。請輸入 /models ls 查看可用清單。{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}參數錯誤。用法: /models [ls | switch <模型名稱>]{Colors.RESET}")

        elif canonical_cmd == "new":
            self.engine.clear_history()
            print(f"{Colors.MAGENTA}記憶已斬斷！Maverick 已準備好迎接全新的話題。{Colors.RESET}")

        elif canonical_cmd == "tools":
            from tools.toolsets import list_toolsets, resolve
            current = self.agent.toolset or "full"
            if len(parts) == 1 or parts[1] == "ls":
                print(f"\n{Colors.CYAN}=== 工具群組 (toolsets) ==={Colors.RESET}")
                for name, tool_names in list_toolsets().items():
                    mark = f" {Colors.GREEN}(當前){Colors.RESET}" if name == current else ""
                    print(f"  {Colors.YELLOW}{name:<10}{Colors.RESET} {tool_names}{mark}")
                print(f"{Colors.CYAN}=========================={Colors.RESET}")
                print("提示：輸入 /tools use <群組名> 即可切換。")
            elif len(parts) >= 3 and parts[1] == "use":
                target = parts[2].lower()
                if resolve(target) is None:
                    print(f"{Colors.RED}找不到工具群組 '{target}'。請輸入 /tools ls 查看。{Colors.RESET}")
                else:
                    self.agent.toolset = target
                    print(f"{Colors.GREEN}已切換工具群組至 '{target}'。{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}參數錯誤。用法: /tools [ls | use <群組名>]{Colors.RESET}")

        elif canonical_cmd == "remember":
            print(f"{Colors.GREY}正在將當前對話的重點策展進長期記憶...{Colors.RESET}")
            before = self.engine.runtime_summary
            after = self.engine.curate_memory()
            if after and after != before:
                print(f"{Colors.GREEN}長期記憶已更新。{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}沒有需要更新的長期記憶(或目前未掛載可用模型)。{Colors.RESET}")

        elif canonical_cmd == "search":
            # 跨 session 全文搜尋(FTS5)。用法: /search <關鍵字>
            if len(parts) < 2:
                print(f"{Colors.YELLOW}參數錯誤。用法: /search <關鍵字>{Colors.RESET}")
            else:
                query = raw_input.split(None, 1)[1].strip()
                hits = self.memory.search_sessions(query)
                if not hits:
                    print(f"{Colors.YELLOW}找不到包含「{query}」的歷史對話。{Colors.RESET}")
                else:
                    print(f"\n{Colors.CYAN}搜尋「{query}」命中 {len(hits)} 筆:{Colors.RESET}")
                    for h in hits:
                        snippet = (h.get("content") or "").replace("\n", " ")[:60]
                        print(f"  {Colors.GREEN}[{h['session_id']}]{Colors.RESET} {snippet}")
                    print()

        elif canonical_cmd == "session":
            if len(parts) >= 3 and parts[1] == "switch":
                new_session_id = parts[2]

                # 1. 物理存檔：將當前話題安全寫入後端
                self.engine.save_context()

                # 2. 切換軌道：替換引擎的 Session ID
                self.engine.session_id = new_session_id

                # 3. 清空內存：把當前記憶體內的舊對話徹底清除，防止話題污染
                self.engine.runtime_history = []
                self.engine.runtime_summary = ""

                # 4. 重新載入：呼叫記憶管理員，載入新 Session 的歷史紀錄
                self.engine.load_context()

                print(f"\n{Colors.CYAN}已成功切換至專案空間: [{new_session_id}]{Colors.RESET}")
                print(f"{Colors.GREY}[系統] 載入該專案歷史對話: {len(self.engine.runtime_history)} 筆。{Colors.RESET}")

            elif len(parts) >= 2 and parts[1] in ["ls", "list"]:
                sessions = self.memory.list_sessions()
                if not sessions:
                    print(f"{Colors.YELLOW}目前沒有任何存檔的專案。{Colors.RESET}")
                else:
                    print(f"\n{Colors.CYAN}目前存在的專案空間 (Sessions):{Colors.RESET}")
                    for s in sessions:
                        if s == self.engine.session_id:
                            print(f"  {Colors.GREEN}➜ {s} (當前){Colors.RESET}")
                        else:
                            print(f"    {s}")
                    print()

            else:
                print(f"{Colors.YELLOW}參數錯誤。用法: /session switch <專案名稱>{Colors.RESET}")

if __name__ == "__main__":
    cli = MaverickCLI()
    cli.run()
