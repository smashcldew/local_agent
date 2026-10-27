# ai_core 移植計畫 — 從 Hermes Agent 汲取功能

> 參考來源:[NousResearch/hermes-agent](https://github.com/nousresearch/hermes-agent)(MIT 授權)
> 本文件為活動中的 roadmap,**每完成一步就更新進度**。最後更新:2026-10-27

---

## 0. 目標與原則

**目標:** 把 Hermes Agent 的成熟功能,逐步、精簡地移植進本地優先的 `ai_core`(Maverick),
同時保持核心純本地、付費雲端模型為可選插件。

**五條原則:**

1. **移植,不是搬檔案。** Hermes 有 1 萬多個 .py,幾乎都踩在它自己的底座上
   (`hermes_bootstrap`、`hermes_state`、`plugin_loader`、PM)。單抓一個檔案會因連鎖
   import 而跑不起來。做法是**看懂它怎麼做 → 用 ai_core 的風格重寫精簡版**;只有真正
   自包含的檔案才直接搬。
2. **現有的部分:先比對,再修改。** 凡是 ai_core 已經有的模組(adapters / tools /
   memory / context),先列出「我方現況 vs Hermes 做法」的差異表,確認要改什麼,
   才動手。不是看到就覆蓋。
3. **本地優先,付費可選。** 核心永遠能純靠 Ollama(llama / gpt-oss)運作。付費雲端
   adapter(Anthropic / OpenAI / Gemini…)做成預設關閉的獨立模組,不裝不影響核心。
4. **保留授權出處。** Hermes 是 MIT。凡移植來的程式碼,在檔頭標注來源,並在
   `LICENSES/hermes-agent-MIT.txt` 保留其授權全文(見 §5)。
5. **每步可驗證。** 每個階段完成都要能通過語法編譯 + 一個冒煙測試,才算 Done。

**狀態圖例:** ⬜ 未開始 ／ 🔄 進行中 ／ ✅ 完成 ／ ⏸️ 暫緩

---

## 1. 進度總覽

| # | 階段 | 優先度 | 狀態 | 備註 |
|---|------|:---:|:---:|------|
| 0 | 專案整理(改名、分資料夾、.gitignore) | — | ✅ | 2026-10-27 完成 |
| 1 | 記憶層:JSON → SQLite + FTS5 全文搜尋 | 高 | ⬜ | 為「搜尋過去對話」鋪路 |
| 2 | 工具分組(toolsets)+ 控制送進 prompt 的工具量 | 高 | ⬜ | |
| 3 | Skills 可學習技能系統 | 中 | ⬜ | Hermes 招牌功能 |
| 4 | Adapter 架構強化 + 付費雲端模型分離 | 中 | ⬜ | 本地/付費皆為註冊式 adapter |
| 5 | Context 壓縮與記憶策展(learning loop) | 中 | ⬜ | 擴充現有 compressor |
| 6 | Cron 排程 | 低 | ⬜ | 之後再談 |
| 7 | Gateway(Telegram / Discord…) | 低 | ⬜ | 大塊,最後 |

---

## 2. 現況對照(ai_core vs Hermes)

| 子系統 | ai_core 現況 | Hermes 對應 | 差距 |
|--------|-------------|-------------|------|
| 模型接層 | `adapters/`(base, registry, llama, gpt-oss) | `agent/*_adapter.py` + `agent/agent_init_ollama.py` | 介面雛形已有;缺付費/本地分離、金鑰輪替、串流 |
| 工具 | `tools/`(registry, file_editor, files_browser, web_search) | `tools/` + `toolsets.py` | 缺「工具分組」概念 |
| 記憶 | `memory/`(Base + JSON provider, manager) | `hermes_state_*.py`(SQLite WAL + FTS5) | 缺 DB 後端、全文搜尋、session 壓縮鏈 |
| 上下文 | `context/`(engine, compressor, references, usage_estimate) | `agent/context_compressor.py`、`curator.py`、`trajectory_compressor.py` | 缺記憶策展、learning loop |
| 技能 | (無) | `skills/`(agentskills.io 標準) | 全新 |
| 排程 | (無) | `cron/` | 全新 |
| 閘道 | (無) | `gateway/` | 全新 |

---

## 3. 各階段細節(先比對 → 再修改)

### 階段 1 — 記憶層:SQLite + FTS5 【高】⬜

**Hermes 怎麼做(事實):**
- `hermes_state.py`:SQLite 狀態庫,WAL 模式(多讀單寫),存 session metadata、
  訊息歷史、模型設定。
- `hermes_state_schema.py`:schema 建立與欄位對帳;使用 **FTS5 虛擬表**做全文搜尋。
- session 用 `parent_session_id` 串成壓縮鏈,並以來源標記(`cli`、`telegram`…)。

**比對項目(動手前要填):**
- [ ] 我方 `JSONMemoryProvider` 目前存哪些欄位 vs Hermes 的 session/message schema
- [ ] `MemoryManager` 的 `save_session / load_session / list_sessions` 介面能否不變
- [ ] FTS5 在目標 Python(本機版本)是否可用

**修改項目:**
- [ ] 在 `memory/` 新增 `SQLiteMemoryProvider`(實作現有 `BaseMemoryProvider` 介面)
- [ ] 設計最小 schema:`sessions`、`messages`、FTS5 虛擬表
- [ ] `MemoryManager` 新增 `search_sessions(query)` 方法
- [ ] 保留 `JSONMemoryProvider` 當 fallback,預設切換為 SQLite
- [ ] 冒煙測試:存 → 讀 → 全文搜尋命中

**驗收:** 能用關鍵字搜出過去 session,且舊 JSON 介面行為不變。

---

### 階段 2 — 工具分組(toolsets)【高】⬜

**Hermes 怎麼做:** `toolsets.py` 用命名清單(如 `_HERMES_CORE_TOOLS`)決定哪些工具
進 prompt。核心理念:**每個 tool 每次 API 呼叫都會送出,所以 core tool 門檻要高**,
新能力走插件。

**比對項目:**
- [ ] 我方 `tools/registry.py` 目前如何決定送哪些工具給模型
- [ ] 現有 4 個工具是否該全進 core,或分組

**修改項目:**
- [ ] `tools/` 新增 toolset 概念(具名工具群組)
- [ ] `registry` 支援「只取某 toolset 的 schema」
- [ ] 冒煙測試:切換 toolset,送進 prompt 的工具數隨之改變

---

### 階段 3 — Skills 可學習技能系統 【中】⬜

**Hermes 怎麼做:** `skills/<類別>/<技能名>/SKILL.md`,YAML frontmatter
(`name / description / version / author / license / platforms / metadata.tags`),
可附 `scripts/`、`references/`。相容 agentskills.io 開放標準。頂層按類別分
(research、web、productivity…),各有 `DESCRIPTION.md`。

**比對項目:** (ai_core 無對應,全新)
- [ ] 決定 ai_core 的 skill 目錄慣例與最小 frontmatter 欄位

**修改項目:**
- [ ] 新增 `skills/` 目錄與 loader
- [ ] skill 注入 prompt 的機制(與階段 2 的 toolset 整合)
- [ ] (進階)任務完成後自動生成 skill 的雛形

---

### 階段 4 — Adapter 架構強化 + 付費雲端分離 【中】⬜

**Hermes 怎麼做:** 本地(`agent_init_ollama.py`、`chat_completion_local.py`)與付費
(`anthropic_adapter.py`、`bedrock_adapter.py`、`gemini_native_adapter.py`、
`vertex_adapter.py`…)都只是註冊進 provider registry 的 adapter;付費依賴放 extra,
由套件管理按需安裝。

**比對項目:**
- [ ] 我方 `adapters/registry.py` 的註冊機制 vs Hermes 的 provider registry
- [ ] 現有 `BaseAdapter` 介面缺哪些(串流、金鑰、逾時重試)

**修改項目:**
- [ ] 把付費雲端 adapter 歸到獨立子目錄(如 `adapters/cloud/`),預設不載入
- [ ] `requirements` / extra 分離:核心只需本地依賴
- [ ] 介面補齊:串流回應、逾時與重試(參考 Hermes 用 `tenacity`)

**驗收:** 移除所有付費 adapter 後,核心仍能用 Ollama 正常對話。

---

### 階段 5 — Context 壓縮與記憶策展 【中】⬜

**Hermes 怎麼做:** `agent/context_compressor.py` 做對話壓縮;`agent/curator.py` 做記憶
策展與定期 nudge(learning loop);`trajectory_compressor.py` 壓縮軌跡供訓練。

**比對項目:**
- [ ] 我方 `context/compressor.py` 的「掐頭去尾留中間」策略 vs Hermes 的壓縮
- [ ] 是否要引入「記憶策展」(自動把重要資訊寫入長期記憶)

**修改項目:**
- [ ] 擴充 `context/compressor.py`
- [ ] (進階)新增 curator:定期把對話重點寫進階段 1 的 SQLite 記憶

---

### 階段 6 / 7 — Cron 排程、Gateway 【低】⏸️

待前五階段穩定後再規劃。Hermes 對應:`cron/`、`gateway/`、`tui_gateway/`。

---

## 4. 工作流程(每個階段都照這個跑)

1. 我鑽進 Hermes 對應程式碼,把「它怎麼做」拆清楚,填進該階段的**比對項目**。
2. 列出我方現況與差異,和你確認要改的範圍。
3. 動手修改,保留 MIT 出處標注。
4. 語法編譯 + 冒煙測試通過。
5. 更新本文件的**進度總覽**表與**進度日誌**,並提醒你 commit。

---

## 5. 授權與出處

Hermes Agent 為 **MIT 授權**,允許複製、修改、商用,條件為保留著作權與授權聲明。

- [ ] 建立 `LICENSES/hermes-agent-MIT.txt`,放入 Hermes 的 LICENSE 全文
- [ ] 凡移植/改寫自 Hermes 的檔案,檔頭註明:
  `# Adapted from NousResearch/hermes-agent (MIT). See LICENSES/hermes-agent-MIT.txt`

---

## 6. 進度日誌

- **2026-10-27**
  - ✅ 階段 0:`compresser`→`compressor` 拼字修正;`list_all_sessions`→`list_sessions`。
  - ✅ 階段 0:大功能分資料夾——新增 `memory/`(provider, manager)與
    `context/`(engine, compressor, references, usage_estimate),更新所有 import,
    全專案編譯 + CLI 建構冒煙測試通過。
  - ✅ 階段 0:新增 `.gitignore`。
  - ✅ 建立本移植計畫 `plan.md`。
  - ⬜ 下一步:等指示後啟動**階段 1(SQLite + FTS5 記憶層)**。
