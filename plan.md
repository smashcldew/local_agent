# ai_core 移植計畫 — 從 Hermes Agent 汲取功能

> 參考來源:[NousResearch/hermes-agent](https://github.com/nousresearch/hermes-agent)(MIT 授權)
> 本文件為活動中的 roadmap,**每完成一步就更新進度**。最後更新:2026-10-28

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
| 1 | 記憶層:JSON → SQLite + FTS5 全文搜尋 | 高 | ✅ | 2026-10-28 完成,中文搜尋已驗證 |
| 2 | 工具分組(toolsets)+ 控制送進 prompt 的工具量 | 高 | ✅ | 2026-10-28 完成,含 /tools 指令 |
| 3 | Skills 可學習技能系統 | 中 | ✅ | 2026-10-28 完成,SKILL.md + skill 工具 |
| 4 | Adapter 架構強化 + 付費雲端模型分離 | 中 | ✅ | 2026-10-28 完成,cloud 預設關閉 |
| 5 | Context 壓縮與記憶策展(learning loop) | 中 | ✅ | 2026-10-28 完成,含 /remember |
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

### 階段 1 — 記憶層:SQLite + FTS5 【高】✅

**Hermes 怎麼做(事實):**
- `hermes_state.py`:SQLite 狀態庫,WAL 模式(多讀單寫),存 session metadata、
  訊息歷史、模型設定。
- `hermes_state_schema.py`:schema 建立與欄位對帳;使用 **FTS5 虛擬表**做全文搜尋。
- session 用 `parent_session_id` 串成壓縮鏈,並以來源標記(`cli`、`telegram`…)。

**比對項目(已完成):**
- [x] 我方 `JSONMemoryProvider` 存 `{summary, history:[{role,content}]}`;SQLite 版對外維持同一格式
- [x] `MemoryManager` 的 `save_session / load_session / list_sessions` 介面維持不變,ContextEngine 零修改
- [x] FTS5 在容器端測試可用,且 **trigram tokenizer 可用**(對中文關鍵)

**修改項目(已完成):**
- [x] `memory/provider.py` 新增 `SQLiteMemoryProvider`(實作 `BaseMemoryProvider`)
- [x] schema:`sessions`、`messages`(+ 索引)、`messages_fts`(FTS5 trigram)
- [x] `BaseMemoryProvider` 加入 `search()` 預設子字串實作;SQLite 以 FTS5 覆寫
- [x] `MemoryManager` 新增 `search_sessions(query)`
- [x] 保留 `JSONMemoryProvider` 當 fallback;預設後端改為 SQLite(`~/.maverick/memory/maverick.db`)
- [x] 冒煙測試:存 → 讀 → 覆寫(不累積)→ 中文全文搜尋(3 字走 FTS5、2 字走 fallback)→ JSON 介面不變 → CLI 建構

**已知注意事項:**
- FTS5 trigram 查詢需 ≥ 3 字元;較短查詢(中文雙字詞如「天氣」)自動退回子字串掃描。
- 舊的 `~/.maverick/memory/*.json` **不會自動遷移**到 SQLite;需要時再寫一次性匯入。

**驗收:** ✅ 能用中文關鍵字搜出過去 session,舊 JSON 介面行為不變。

---

### 階段 2 — 工具分組(toolsets)【高】✅

**Hermes 怎麼做:** `toolsets.py` 用命名清單(如 `_HERMES_CORE_TOOLS`)決定哪些工具
進 prompt。核心理念:**每個 tool 每次 API 呼叫都會送出,所以 core tool 門檻要高**,
新能力走插件。

**比對項目(已完成):**
- [x] 原 `registry.get_schemas()` 無差別回傳全部工具;agent 每輪都送全部
- [x] 現有 3 個工具(read/write/search),依情境分成 full / core / readonly / chat 四組

**修改項目(已完成):**
- [x] 新增 `tools/toolsets.py`:`TOOLSETS` 具名群組 + `resolve()` / `list_toolsets()`
- [x] `registry` 以 `name→schema` 索引,`get_schemas(toolset=…)` 過濾;未指定回全部(相容)、未知群組安全退回全部
- [x] `MaverickAgent` 加 `toolset` 參數,每輪依群組取工具
- [x] CLI 新增 `/tools [ls | use <群組>]`(別名 `/t`)
- [x] 測試:readonly 濾掉 write_local_file、chat 回空、未指定仍回 3 個、agent 實際傳出過濾後工具

**驗收:** ✅ 切換 toolset 後送進 prompt 的工具集合隨之改變,且預設行為不變。

---

### 階段 3 — Skills 可學習技能系統 【中】✅

**Hermes 怎麼做:** `skills/<類別>/<技能名>/SKILL.md`,YAML frontmatter
(`name / description / version / author / license / platforms / metadata.tags`),
可附 `scripts/`、`references/`。相容 agentskills.io 開放標準。頂層按類別分
(research、web、productivity…),各有 `DESCRIPTION.md`。

**比對項目(已完成):**
- [x] 採 Hermes / agentskills.io 格式:`skills/<名稱>/SKILL.md`,frontmatter 取 `name`、`description`
- [x] 為維持本地零依賴,自寫極簡 frontmatter 解析(不引入 PyYAML/ruamel)

**修改項目(已完成):**
- [x] 新增 `skills/` 套件 + `SkillManager`(掃描 repo 內建 + `~/.maverick/skills`、list/get/catalog)
- [x] 內建範例技能 `skills/python-code-review/SKILL.md`
- [x] 仿 Hermes 以工具暴露:`tools/skills_tool.py` 的 `skill_list` / `skill_view`,由模型按需載入
- [x] 併入 toolsets(full/core/readonly 皆含 skill 工具,屬唯讀),`run_agent` 匯入觸發註冊
- [x] 測試:掃描到內建技能、取用內文、找不到時友善提示、兩個工具可執行

**驗收:** ✅ 模型可透過 `skill_list` 看到技能、用 `skill_view` 取得完整步驟。

**備註:** 「任務完成後自動生成 skill」(self-improving)屬進階,留待日後;目前先完成
手動技能的載入與使用。

---

### 階段 4 — Adapter 架構強化 + 付費雲端分離 【中】✅

**Hermes 怎麼做:** 本地(`agent_init_ollama.py`、`chat_completion_local.py`)與付費
(`anthropic_adapter.py`、`bedrock_adapter.py`、`gemini_native_adapter.py`、
`vertex_adapter.py`…)都只是註冊進 provider registry 的 adapter;付費依賴放 extra,
由套件管理按需安裝。

**比對項目(已完成):**
- [x] 我方 registry 已是「名稱 → setup_fn」註冊式,本地/雲端共用同一介面,毋需大改
- [x] `adapters/__init__.py` 原本無差別自動載入頂層 `*_adapter.py`;需讓雲端可選

**修改項目(已完成):**
- [x] 新增 `adapters/cloud/` 子套件,收納付費雲端 adapter
- [x] `adapters/__init__.py`:頂層本地 adapter 一律載入;`cloud/` 僅在
      `MAVERICK_ENABLE_CLOUD=1` 時載入,預設關閉
- [x] 範例雲端 adapter `openai_compat_adapter.py`(OpenAI / OpenRouter / 自架相容;
      金鑰、端點、模型皆讀環境變數;無金鑰回友善錯誤不崩潰)
- [x] `requirements.txt`:核心僅 requests + duckduckgo_search;雲端零額外依賴,純靠設定開關
- [x] 測試:預設組建無 openai(純本地)、開環境變數後 openai 以 type=cloud 註冊、無金鑰呼叫回錯誤

**驗收:** ✅ 預設(不設環境變數)完全不載入任何付費雲端 adapter,核心純本地;
需要時一個環境變數即可掛上雲端。

**備註:** 串流 / `tenacity` 重試等介面強化風險較高且非當前需求,留待日後;本階段聚焦
「付費雲端分離」這個最初的明確需求。

---

### 階段 5 — Context 壓縮與記憶策展 【中】✅

**Hermes 怎麼做:** `agent/context_compressor.py` 做對話壓縮;`agent/curator.py` 做記憶
策展與定期 nudge(learning loop);`trajectory_compressor.py` 壓縮軌跡供訓練。

**比對項目(已完成):**
- [x] 現有 `compressor` 是「容量驅動」:超出 token 預算才把中段壓成摘要
- [x] 缺「價值驅動」的策展:主動把對話重點(偏好、決定、專案事實)存成長期記憶

**修改項目(已完成):**
- [x] 新增 `context/curator.py` 的 `MemoryCurator`:萃取長期重點融合進摘要;無 adapter 為安全 no-op
- [x] `ContextEngine` 加 `curator` 參數與 `curate_memory()`,用 compressor 當前 adapter、並持久化
- [x] CLI 新增 `/remember`(別名 `/rem`)手動觸發策展
- [x] 測試:無 adapter/無對話不變、有 adapter 產生新摘要、engine 策展後持久化

**驗收:** ✅ `/remember` 能把當前對話重點寫進長期背景摘要並存入 SQLite,跨 session 保留。

**備註:** 「定期自動 nudge 策展」可日後掛在對話輪次或排程上;目前先提供手動觸發。

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

- [x] 建立 `LICENSES/hermes-agent-MIT.txt`,放入 Hermes 的 LICENSE 全文
- [x] 凡移植/改寫自 Hermes 的檔案,檔頭註明(已套用於 `memory/provider.py`):
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

- **2026-10-28**
  - ✅ **階段 1 完成**:新增 `SQLiteMemoryProvider`(WAL + FTS5 trigram),`MemoryManager`
    新增 `search_sessions()`,預設後端改 SQLite,保留 JSON fallback。
  - ✅ 處理中文搜尋:trigram 需 ≥ 3 字,短查詢自動退回子字串掃描(「天氣」可命中)。
  - ✅ 冒煙測試全過(存/讀/覆寫/中文搜尋/JSON 介面/CLI 建構)。
  - ✅ 建立 `LICENSES/hermes-agent-MIT.txt`,`memory/provider.py` 檔頭標注來源。
  - ✅ 改寫 `README.md`(專案簡介、參考來源、特色、架構、用法)。
  - ✅ 把階段 1 的全文搜尋接上 CLI:新增 `/search <關鍵字>`(別名 `/find`、`/grep`)。
  - ⚠️ 修復:D 槽的 `cli.py` 一度被還原成重構前舊版(import 不存在的 `memory_manager`)、
    `context_compresser.py` 殘留重現。已重新套用重構的 `cli.py`。**`context_compresser.py`
    仍需使用者手動刪除**(我無刪除權限;目前無任何程式 import 它,屬無害殘留)。
  - ✅ 建立一支完整回歸測試腳本(編譯、記憶、上下文、adapter、工具、agent loop、CLI、指令),
    **每個階段完成都從頭重跑**。
  - ✅ **階段 2 完成**:`tools/toolsets.py` + registry 群組過濾 + `MaverickAgent.toolset` +
    CLI `/tools`。回歸測試 38/0 全過。
  - ✅ **階段 3 完成**:`skills/` + `SkillManager` + 範例技能 + `skill_list`/`skill_view` 工具,
    併入 toolsets。回歸測試 47/0 全過。
  - ✅ **階段 4 完成**:`adapters/cloud/` 子套件 + 環境變數開關 + OpenAI 相容範例 adapter +
    `requirements.txt`。預設純本地,雲端可選。回歸測試 51/0 全過。
  - ✅ **階段 5 完成**:`context/curator.py` 的 `MemoryCurator` + `engine.curate_memory()` +
    CLI `/remember`。回歸測試 57/0 全過。
  - ✅ **階段 1–5 全部完成**,完整回歸測試 57 項全綠(每階段都從頭重跑)。
  - ⏸️ 階段 6(cron)、7(gateway)依計畫暫緩,牽涉外部帳號/憑證,待使用者決定範圍後再啟動。
