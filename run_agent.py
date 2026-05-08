# run_agent.py
import sys
import time
import json
from display import Colors
from tools.registry import registry  # 🌟 匯入中央註冊表
import tools.files_browser
import tools.file_editor

class MaverickAgent:
    """
    [代理人核心迴圈]
    具備動態思考狀態與「工具自動執行迴圈 (Agent Loop)」。
    """
    def __init__(self, engine, adapter):
        self.engine = engine
        self.adapter = adapter
        self.max_iterations = 5  # 避免大腦陷入無限迴圈

    def set_adapter(self, new_adapter):
        self.adapter = new_adapter

    def _show_status(self, message: str):
        sys.stdout.write(f"\r\033[K{Colors.PURPLE}[Maverick] > {Colors.RESET}\033[90m⚡ {message}\033[0m")
        sys.stdout.flush()
        time.sleep(0.1) 

    def chat(self, user_input: str) -> str:
        self._show_status("正在提取記憶與分析意圖...")
        self.engine.add_message("user", user_input)
        
        iterations = 0
        final_response = ""
        
        # 🌟 企業級 Agent Loop 開始！
        while iterations < self.max_iterations:
            iterations += 1
            
            self._show_status("正在編譯上下文與精算 Token 預算...")
            safe_context = self.engine.compile_context()
            
            self._show_status(f"正在喚醒神經網路大腦 (思考輪次 {iterations})...")
            sys.stdout.write(f"\r\033[K{Colors.PURPLE}[Maverick] > {Colors.RESET}")
            sys.stdout.flush()
            
            # 🌟 1. 從註冊表獲取可用工具的 JSON Schema
            tools_schema = registry.get_schemas()
            
            # 🌟 2. 呼叫 Adapter (這次真的把 tools 傳過去了！)
            response_text, tool_calls = self.adapter.generate_response(safe_context, tools=tools_schema)
            
            # --- 分支 A：大腦沒有呼叫工具，直接回答 ---
            if not tool_calls:
                self.engine.add_message("assistant", response_text)
                self.engine.save_context()
                final_response = response_text
                break
            
            # --- 分支 B：大腦決定呼叫工具！ ---
            print(f"\n{Colors.MAGENTA}⚡ [系統] 偵測到工具呼叫！{Colors.RESET}")
            
            # 1. 將大腦這次的呼叫紀錄存進記憶
            self.engine.add_message("assistant", response_text, tool_calls=tool_calls)
            
            # 2. 依序執行大腦要求的工具
            for tool_call in tool_calls:
                func_data = tool_call.get("function", {})
                tool_name = func_data.get("name")
                tool_args = func_data.get("arguments", {})
                
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except json.JSONDecodeError:
                        tool_args = {}

                # 🌟 [安全守衛] 人類審核機制 (Human-in-the-Loop)
                # 這裡可以維護一個危險工具的清單
                dangerous_tools = ["write_local_file", "execute_terminal"]
                
                if tool_name in dangerous_tools:
                    print(f"\n{Colors.YELLOW}⚠️ [系統守衛] 大腦請求執行危險操作：{Colors.RESET}{tool_name}")
                    
                    # 針對不同工具做友善的預覽
                    if tool_name == "write_local_file":
                        file_path = tool_args.get("file_path", "未知路徑")
                        content = tool_args.get("content", "")
                        preview = content[:50].replace('\n', ' ') + ("..." if len(content) > 50 else "")
                        print(f"{Colors.GREY}   目標檔案: {file_path}{Colors.RESET}")
                        print(f"{Colors.GREY}   內容預覽: {preview}{Colors.RESET}")
                    else:
                        print(f"{Colors.GREY}   參數: {tool_args}{Colors.RESET}")
                    
                    # 阻塞等待人類授權
                    choice = input(f"{Colors.YELLOW}   是否允許執行？ [y/N]: {Colors.RESET}").strip().lower()
                    
                    # 預設為 N (拒絕)，必須明確輸入 y 才會放行
                    if choice not in ['y', 'yes']:
                        print(f"{Colors.RED}   🚫 操作已被人類拒絕。{Colors.RESET}")
                        # 關鍵：將拒絕的結果寫回記憶，讓大腦知道發生了什麼事
                        result_text = f"❌ 執行失敗：人類使用者拒絕了執行 {tool_name} 的請求。請向使用者道歉或詢問其他作法。"
                        self.engine.add_message("tool", result_text, name=tool_name)
                        continue  # 跳過這個工具的執行，進入下一個迴圈
                
                # --- 通過審核 (或非危險工具)，正常執行 ---
                print(f"{Colors.GREY}   ⚙️ 執行本地工具: {tool_name}(...){Colors.RESET}")
                
                handler = registry.get_handler(tool_name)
                if handler:
                    result_text = handler(tool_args)
                else:
                    result_text = f"執行失敗：找不到工具 {tool_name}"
                    
                # 3. 將執行結果以 role: "tool" 寫回記憶
                self.engine.add_message("tool", result_text, name=tool_name)
                
            print(f"{Colors.GREY}   ✅ 執行完畢，將結果送回大腦重新思考...{Colors.RESET}\n")
            
        if iterations >= self.max_iterations:
            print(f"\n{Colors.RED}⚠️ 達到最大思考次數限制 ({self.max_iterations})，強制中斷。{Colors.RESET}")
            final_response = "（系統強制中斷：超過最大思考次數）"
            
        return final_response