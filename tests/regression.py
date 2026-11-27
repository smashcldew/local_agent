#!/usr/bin/env python3
# ai_core 完整回歸測試。用法: python3 -I regression.py <tree_dir>
# 不需網路 / Ollama:外部依賴以 stub 取代,模型以 FakeAdapter 注入。
import sys, os, types, tempfile, traceback

TREE = sys.argv[1]
sys.path.insert(0, TREE)

PASS, FAIL = [], []
def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name + (f" :: {extra}" if extra and not cond else ""))

# ---- stub 外部依賴 ----
ddg = types.ModuleType("duckduckgo_search"); ddg.DDGS = object
sys.modules["duckduckgo_search"] = ddg
req = types.ModuleType("requests")
class _Resp:
    def raise_for_status(self): pass
    def json(self): return {"message": {"content": "ok"}}
    def iter_lines(self): return iter([])
req.post = lambda *a, **k: _Resp()
req.get = lambda *a, **k: _Resp()
sys.modules["requests"] = req

HOME = tempfile.mkdtemp()
os.environ["MAVERICK_HOME"] = HOME

# ---- 1. 全樹編譯 ----
import py_compile, pathlib
for p in pathlib.Path(TREE).rglob("*.py"):
    if "__pycache__" in str(p): continue
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as e:
        FAIL.append(f"compile {p.relative_to(TREE)} :: {e}")
check("compile: 全樹", not any(x.startswith("compile ") for x in FAIL))

# ---- 2. 無殘留舊名稱 ----
bad = []
for p in pathlib.Path(TREE).rglob("*.py"):
    if "__pycache__" in str(p) or "tests" in p.parts: continue  # 略過測試檔自身
    t = p.read_text(encoding="utf-8")
    for token in ("compresser", "Compresser", "list_all_sessions"):
        if token in t: bad.append(f"{p.name}:{token}")
check("無殘留舊名稱 (compresser/list_all_sessions)", not bad, str(bad))

# ---- 3. 記憶層 ----
try:
    from memory import MemoryManager, SQLiteMemoryProvider, JSONMemoryProvider
    db = os.path.join(tempfile.mkdtemp(), "t.db")
    mm = MemoryManager(provider=SQLiteMemoryProvider(db_path=db))
    mm.save_session("a", "摘要A", [{"role":"user","content":"設計 SQLite 記憶層"},
                                   {"role":"assistant","content":"使用 FTS5 trigram"}])
    mm.save_session("b", "摘要B", [{"role":"user","content":"今天天氣如何"}])
    d = mm.load_session("a")
    check("記憶: load 格式", d["summary"]=="摘要A" and len(d["history"])==2, str(d))
    check("記憶: list", set(mm.list_sessions())=={"a","b"}, str(mm.list_sessions()))
    check("記憶: FTS5 3字搜尋", any(r["session_id"]=="a" for r in mm.search_sessions("記憶層")))
    check("記憶: FTS5 英數搜尋", any(r["session_id"]=="a" for r in mm.search_sessions("FTS5")))
    check("記憶: 2字中文退回子字串", any(r["session_id"]=="b" for r in mm.search_sessions("天氣")))
    check("記憶: 無命中回空", mm.search_sessions("不存在的詞彙")==[])
    mm.save_session("a", "新摘要", [{"role":"user","content":"只剩一句"}])
    d2 = mm.load_session("a")
    check("記憶: 覆寫不累積", len(d2["history"])==1 and d2["summary"]=="新摘要", str(d2))
    jm = MemoryManager(provider=JSONMemoryProvider(storage_dir=tempfile.mkdtemp()))
    jm.save_session("j", "s", [{"role":"user","content":"hello world"}])
    check("記憶: JSON 介面 + 搜尋", jm.list_sessions()==["j"] and bool(jm.search_sessions("hello")))
except Exception:
    FAIL.append("記憶層例外:\n"+traceback.format_exc())

# ---- 4. 上下文層 ----
try:
    from context import ContextEngine, ContextCompressor, ContextReferences
    from memory import MemoryManager, SQLiteMemoryProvider
    mm2 = MemoryManager(provider=SQLiteMemoryProvider(db_path=os.path.join(tempfile.mkdtemp(),"c.db")))
    eng = ContextEngine("s1", mm2, ContextCompressor(llm_adapter=None), ContextReferences())
    eng.load_context(); eng.add_message("user","你好")
    msgs = eng.compile_context()
    check("上下文: compile 首則為 system", msgs and msgs[0]["role"]=="system", str(msgs[:1]))
    check("上下文: 含使用者訊息", any(m.get("content")=="你好" for m in msgs))
    eng.save_context()
    check("上下文: 存檔後可回讀", mm2.load_session("s1")["history"][-1]["content"]=="你好")
except Exception:
    FAIL.append("上下文層例外:\n"+traceback.format_exc())

# ---- 5. 模型 adapter registry ----
try:
    from adapters import adapter_registry
    models = adapter_registry.get_all_models()
    check("adapter: llama 已註冊", "llama" in models)
    check("adapter: gpt-oss 已註冊", "gpt-oss" in models)
    a = adapter_registry.get_adapter("llama")
    check("adapter: 可建構 llama", a is not None and hasattr(a, "generate_response"))
    check("adapter: get_max_tokens", isinstance(a.get_max_tokens(), int))
except Exception:
    FAIL.append("adapter 例外:\n"+traceback.format_exc())

# ---- 6. 工具 registry ----
try:
    from tools.registry import registry
    import tools.files_browser, tools.file_editor, tools.web_search  # 觸發註冊
    names = [s["function"]["name"] for s in registry.get_schemas()]
    for t in ("read_local_file","write_local_file","search_web"):
        check(f"工具: {t} 已註冊", t in names, str(names))
    # 實際執行 read_local_file
    tf = os.path.join(tempfile.mkdtemp(),"demo.txt"); open(tf,"w",encoding="utf-8").write("測試內容123")
    h = registry.get_handler("read_local_file")
    check("工具: read_local_file 執行", "測試內容123" in h({"file_path": tf}))
except Exception:
    FAIL.append("工具例外:\n"+traceback.format_exc())

# ---- 7. Agent loop(FakeAdapter,不需網路)----
try:
    from run_agent import MaverickAgent
    from context import ContextEngine, ContextCompressor, ContextReferences
    from memory import MemoryManager, SQLiteMemoryProvider

    class FakeAdapter:
        def __init__(self): self.calls=0; self.max_tokens=8192
        def get_max_tokens(self): return self.max_tokens
        def generate_response(self, messages, tools=None, silent=False):
            self.calls+=1
            return "這是最終回答", []   # 不呼叫工具,直接回答

    mm3 = MemoryManager(provider=SQLiteMemoryProvider(db_path=os.path.join(tempfile.mkdtemp(),"ag.db")))
    eng = ContextEngine("ag", mm3, ContextCompressor(llm_adapter=None), ContextReferences())
    eng.load_context()
    agent = MaverickAgent(engine=eng, adapter=FakeAdapter())
    out = agent.chat("哈囉")
    check("agent: 無工具直接回答", out=="這是最終回答", out)
    check("agent: 回答已入記憶", eng.runtime_history[-1]["content"]=="這是最終回答")

    # 工具呼叫路徑
    tf = os.path.join(tempfile.mkdtemp(),"r.txt"); open(tf,"w",encoding="utf-8").write("檔案內容XYZ")
    class ToolAdapter:
        def __init__(self, path): self.path=path; self.step=0; self.max_tokens=8192
        def get_max_tokens(self): return self.max_tokens
        def generate_response(self, messages, tools=None, silent=False):
            self.step+=1
            if self.step==1:
                return "", [{"function":{"name":"read_local_file","arguments":{"file_path":self.path}}}]
            return "我讀到了內容", []
    eng2 = ContextEngine("ag2", mm3, ContextCompressor(llm_adapter=None), ContextReferences())
    eng2.load_context()
    agent2 = MaverickAgent(engine=eng2, adapter=ToolAdapter(tf))
    out2 = agent2.chat("讀檔")
    check("agent: 工具路徑完成", out2=="我讀到了內容", out2)
    check("agent: 工具結果入記憶", any(m.get("role")=="tool" and "檔案內容XYZ" in str(m.get("content")) for m in eng2.runtime_history))
except Exception:
    FAIL.append("agent loop 例外:\n"+traceback.format_exc())

# ---- 8. CLI 建構 ----
try:
    import cli
    c = cli.MaverickCLI()
    check("CLI: 建構成功", c.active_adapter is not None)
    check("CLI: 預設大腦為 gpt-oss", c.active_model_name=="gpt-oss", c.active_model_name)
    check("CLI: 記憶後端為 SQLite", type(c.memory.provider).__name__=="SQLiteMemoryProvider")
except Exception:
    FAIL.append("CLI 例外:\n"+traceback.format_exc())

# ---- 9. 指令解析(含新指令) ----
try:
    from commands import resolve_command
    check("指令: /search 解析", resolve_command("/search 記憶層")=="search")
    check("指令: /find 別名", resolve_command("/find x")=="search")
    check("指令: /tools 解析", resolve_command("/tools ls")=="tools")
    check("指令: 未知指令回 None", resolve_command("/zzz")is None)
except Exception:
    FAIL.append("指令解析例外:\n"+traceback.format_exc())

# ========= 可選階段測試(功能存在才測) =========
# 階段2 toolsets
try:
    from tools import toolsets as _ts
    from tools.registry import registry as _reg
    import tools.files_browser, tools.file_editor, tools.web_search  # 確保已註冊
    check("階段2: toolsets.TOOLSETS 存在", hasattr(_ts, "TOOLSETS"))
    check("階段2: resolve(readonly) 不含寫檔", "write_local_file" not in (_ts.resolve("readonly") or []))
    ro = _reg.get_schemas(toolset="readonly")
    ro_names = [s["function"]["name"] for s in ro]
    check("階段2: readonly 過濾掉 write_local_file", "write_local_file" not in ro_names and "read_local_file" in ro_names, str(ro_names))
    check("階段2: chat 群組回空", _reg.get_schemas(toolset="chat")==[])
    _ntools = len(_reg.list_tools())
    check("階段2: 未指定回全部(相容)", len(_reg.get_schemas())==_ntools)
    check("階段2: 未知群組安全退回全部", len(_reg.get_schemas(toolset="沒這個"))==_ntools)
    check("階段2: full 群組 = 全部工具", len(_reg.get_schemas(toolset="full"))==_ntools)
    # agent 確實把過濾後的工具傳給 adapter
    from run_agent import MaverickAgent
    from context import ContextEngine, ContextCompressor, ContextReferences
    from memory import MemoryManager, SQLiteMemoryProvider
    captured = {}
    class CapAdapter:
        max_tokens=8192
        def get_max_tokens(self): return self.max_tokens
        def generate_response(self, messages, tools=None, silent=False):
            captured["tools"]=tools; return "ok", []
    mmx = MemoryManager(provider=SQLiteMemoryProvider(db_path=os.path.join(tempfile.mkdtemp(),"ts.db")))
    engx = ContextEngine("ts", mmx, ContextCompressor(llm_adapter=None), ContextReferences()); engx.load_context()
    ag = MaverickAgent(engine=engx, adapter=CapAdapter(), toolset="readonly")
    ag.chat("hi")
    passed_names = [s["function"]["name"] for s in (captured.get("tools") or [])]
    check("階段2: agent 傳出 readonly 工具", "write_local_file" not in passed_names and "read_local_file" in passed_names, str(passed_names))
except ImportError:
    pass
except Exception:
    FAIL.append("toolsets 例外:\n"+traceback.format_exc())

# 階段3 skills
try:
    from skills import SkillManager
    sm = SkillManager()
    names = [s["name"] for s in sm.list_skills()]
    check("階段3: 內建技能被掃到", "python-code-review" in names, str(names))
    body = sm.get_skill("python-code-review")
    check("階段3: get_skill 回內文", body is not None and "檢查清單" in body)
    check("階段3: 不存在技能回 None", sm.get_skill("沒這個技能") is None)
    check("階段3: render_catalog 非空", bool(sm.render_catalog()))
    # 技能工具已註冊且可執行
    from tools.registry import registry as _reg2
    import tools.skills_tool  # 觸發註冊
    tnames = _reg2.list_tools()
    check("階段3: skill_list/skill_view 已註冊", "skill_list" in tnames and "skill_view" in tnames, str(tnames))
    out = _reg2.get_handler("skill_view")({"name": "python-code-review"})
    check("階段3: skill_view 工具回內文", "檢查清單" in out)
    out2 = _reg2.get_handler("skill_list")({})
    check("階段3: skill_list 工具列出技能", "python-code-review" in out2)
    check("階段3: skill_view 找不到時友善提示", "找不到技能" in _reg2.get_handler("skill_view")({"name":"xxx"}))
except ImportError:
    pass
except Exception:
    FAIL.append("skills 例外:\n"+traceback.format_exc())

# 階段5 記憶策展 curator
try:
    from context import MemoryCurator, ContextEngine, ContextCompressor, ContextReferences
    from memory import MemoryManager, SQLiteMemoryProvider
    cur = MemoryCurator()
    # 無 adapter → no-op
    check("階段5: 無 adapter 時 curate 不變", cur.curate("舊摘要", [{"role":"user","content":"x"}])=="舊摘要")
    check("階段5: 無對話時 curate 不變", cur.curate("舊摘要", [], llm_adapter=object())=="舊摘要")
    # 有 adapter → 產生新摘要
    class SumAdapter:
        max_tokens=8192
        def get_max_tokens(self): return self.max_tokens
        def generate_response(self, messages, tools=None, silent=False):
            return "【策展後摘要】使用者偏好繁體中文、專案名 Maverick", []
    new = cur.curate("舊摘要", [{"role":"user","content":"我叫阿元,專案叫 Maverick"}], llm_adapter=SumAdapter())
    check("階段5: 有 adapter 產生新摘要", "Maverick" in new and new!="舊摘要", new)
    # 經由 engine.curate_memory 持久化(adapter 掛在 compressor 上)
    mmc = MemoryManager(provider=SQLiteMemoryProvider(db_path=os.path.join(tempfile.mkdtemp(),"cur.db")))
    comp = ContextCompressor(llm_adapter=SumAdapter())
    eng = ContextEngine("cur", mmc, comp, ContextReferences())
    eng.load_context(); eng.add_message("user","我叫阿元")
    eng.curate_memory()
    check("階段5: engine.curate_memory 更新摘要", "策展後摘要" in eng.runtime_summary, eng.runtime_summary)
    check("階段5: 策展結果已持久化", "策展後摘要" in mmc.load_session("cur")["summary"])
    from commands import resolve_command as _rc
    check("階段5: /remember 指令解析", _rc("/remember")=="remember" and _rc("/rem")=="remember")
except Exception:
    FAIL.append("curator 例外:\n"+traceback.format_exc())

# 階段4 付費雲端分離
try:
    import os as _os
    cloud_dir = _os.path.join(TREE, "adapters", "cloud")
    if _os.path.isdir(cloud_dir):
        from adapters import adapter_registry as _ar
        models = _ar.get_all_models()
        check("階段4: 預設【不】載入雲端(純本地)", "openai" not in models and "llama" in models, str(list(models)))
        check("階段4: adapters/cloud 套件存在", _os.path.isfile(_os.path.join(cloud_dir, "__init__.py")))
        # 子行程:開啟 MAVERICK_ENABLE_CLOUD 後應註冊雲端 adapter
        import subprocess, sys as _sys
        code = (
            "import sys,types\n"
            f"sys.path.insert(0,{TREE!r})\n"
            "m=types.ModuleType('requests'); m.post=lambda *a,**k:None; m.get=lambda *a,**k:None; sys.modules['requests']=m\n"
            "d=types.ModuleType('duckduckgo_search'); d.DDGS=object; sys.modules['duckduckgo_search']=d\n"
            "from adapters import adapter_registry as ar\n"
            "mm=ar.get_all_models()\n"
            "print('CLOUD_OK' if ('openai' in mm and mm['openai']['type']=='cloud') else 'CLOUD_MISSING')\n"
        )
        env = dict(_os.environ); env["MAVERICK_ENABLE_CLOUD"] = "1"
        r = subprocess.run([_sys.executable, "-I", "-c", code], capture_output=True, text=True, env=env)
        check("階段4: 開啟環境變數後雲端 adapter 註冊成功", "CLOUD_OK" in r.stdout, (r.stdout + r.stderr).strip())
        # 無金鑰時呼叫雲端 adapter 應回清楚錯誤而非崩潰
        import importlib
        oca = importlib.import_module("adapters.cloud.openai_compat_adapter")
        env2 = dict(_os.environ);
        adapter = oca.OpenAICompatAdapter(api_key="")
        txt, calls = adapter.generate_response([{"role": "user", "content": "hi"}], silent=True)
        check("階段4: 雲端無金鑰回友善錯誤", "OPENAI_API_KEY" in txt and calls == [])
except Exception:
    FAIL.append("cloud 例外:\n" + traceback.format_exc())

# ---- 總結 ----
print(f"\n{'='*50}\n通過 {len(PASS)} / 失敗 {len(FAIL)}\n{'='*50}")
for p in PASS: print("  ✅", p)
if FAIL:
    print("\n--- 失敗 ---")
    for f in FAIL: print("  ❌", f)
    sys.exit(1)
print("\n🎉 全部通過")
