# Maverick (ai_core)

一個**本地優先**的 AI agent 核心。預設完全跑在本機模型上(透過 [Ollama](https://ollama.com) 的
`llama`、`gpt-oss`),不依賴任何付費雲端 API;付費的雲端模型是可選的、預設關閉的插件。

目標是打造一個會「記得你」的個人 agent:跨 session 保存記憶、能搜尋過去的對話、
用工具(讀寫檔案、網路搜尋)完成任務,並且架構清楚、每個大功能各司其職。

---

## 特色

- **本地優先,零雲端依賴** — 核心只需要本機的 Ollama 就能運作。付費雲端 adapter 獨立、可選。
- **可插拔的模型接層** — 透過 adapter registry 註冊模型;本地與雲端模型都只是「註冊進去的 adapter」,
  換模型不用改核心程式(`llama` / `gpt-oss`,未來可加 Anthropic、OpenAI…)。
- **持久化記憶 + 全文搜尋** — SQLite 後端(WAL 模式),以 FTS5 做跨 session 全文搜尋,
  並對中文友善(trigram tokenizer,短詞自動退回子字串比對)。保留 JSON 後端作為 fallback。
- **上下文管理** — session 載入/存檔、系統 prompt 組裝、對話壓縮(掐頭去尾留中間)、檔案引用。
- **工具系統** — 中央註冊表管理工具 schema 與 handler:讀取本地檔案、寫入檔案、網路搜尋。
- **清楚的模組邊界** — 記憶、上下文、模型接層、工具各自成資料夾,核心保持精簡。

---

## 參考來源

本專案的多項設計參考自 [**NousResearch/hermes-agent**](https://github.com/nousresearch/hermes-agent)(MIT 授權),
並依 ai_core 的規模重新改寫為精簡版,而非直接複製。

具體參考了:

| 功能 | 參考了 Hermes 的什麼 |
|------|----------------------|
| 記憶層 | `hermes_state` 的 SQLite 設計:WAL 模式、FTS5 全文搜尋、**trigram tokenizer(處理中文)** |
| 模型接層 | provider registry + adapter 介面;本地(Ollama)與付費雲端 adapter 分離、付費可選 |
| 工具 | `toolsets` 的「工具分組、控制送進 prompt 的工具量」概念(規劃中) |
| 技能 | `skills/` 的可學習技能系統與 agentskills.io 格式(規劃中) |

完整的移植計畫與進度見 [`plan.md`](./plan.md)。
Hermes Agent 的 MIT 授權全文保存於 [`LICENSES/hermes-agent-MIT.txt`](./LICENSES/hermes-agent-MIT.txt);
凡改寫自 Hermes 的檔案,會在檔頭標注來源。

---

## 架構

```
ai_core/
├── cli.py              # 終端機 I/O 與指令分發
├── run_agent.py        # Agent 主迴圈、工具執行、session 生命週期
├── commands.py         # 指令定義與解析
├── display.py          # 終端輸出(橫幅、spinner、顏色)
├── constants.py        # 全局路徑(~/.maverick/)
├── prompt_builder.py   # 系統 prompt 組裝
│
├── memory/             # 記憶層
│   ├── provider.py     #   BaseMemoryProvider / JSONMemoryProvider / SQLiteMemoryProvider(FTS5)
│   └── manager.py      #   MemoryManager:save / load / list / search_sessions
│
├── context/            # 上下文層
│   ├── engine.py       #   ContextEngine:載入/存檔、組裝最終 prompt
│   ├── compressor.py   #   ContextCompressor:對話壓縮
│   ├── references.py   #   ContextReferences:檔案引用
│   └── usage_estimate.py  # TokenEstimator:token 估算
│
├── adapters/           # 模型接層
│   ├── base_adapter.py #   BaseAdapter(ABC)
│   ├── registry.py     #   AdapterRegistry
│   ├── llama_adapter.py
│   └── gpt-oss_adapter.py
│
├── tools/              # 工具
│   ├── registry.py     #   ToolRegistry:schema + handler
│   ├── files_browser.py#   read_local_file
│   ├── file_editor.py  #   write_local_file
│   └── web_search.py   #   search_web
│
└── LICENSES/           # 第三方授權(Hermes Agent MIT)
```

---

## 需求

- Python 3.11+
- [Ollama](https://ollama.com),並已拉下模型(預設 `gpt-oss`,另有 `llama`):
  ```bash
  ollama pull gpt-oss:20b
  ```
- Python 套件:`requests`、`duckduckgo_search`

---

## 用法

```bash
python cli.py
```

啟動後進入互動式終端。預設大腦為 `gpt-oss`(可用 `/models switch llama` 切換),記憶存於 `~/.maverick/memory/maverick.db`
(可用環境變數 `MAVERICK_HOME` 覆寫基礎目錄)。

常用指令:

| 指令 | 說明 |
|------|------|
| `/models [ls \| switch <名稱>]` | 查看 / 切換大腦模型 |
| `/tools [ls \| use <群組>]` | 查看 / 切換工具群組(full / core / readonly / chat) |
| `/search <關鍵字>` | 全文搜尋過去所有對話 |
| `/session [ls \| switch <名稱>]` | 切換對話專案 |
| `/ref [add <檔名> \| ls \| clear]` | 掛載外部參考檔案 |
| `/new`、`/help`、`/exit` | 新話題 / 說明 / 離開 |

## 雲端模型(可選,預設關閉)

核心預設完全純本地。若要掛上 OpenAI 相容的付費雲端模型:

```bash
export MAVERICK_ENABLE_CLOUD=1          # 啟用 adapters/cloud/
export OPENAI_API_KEY=sk-...            # 你的金鑰
export OPENAI_BASE_URL=https://api.openai.com/v1   # 選填,可指向 OpenRouter / 自架
export OPENAI_MODEL=gpt-4o-mini         # 選填
python cli.py
# 進入後:/models switch openai
```

未設定 `MAVERICK_ENABLE_CLOUD` 時,`adapters/cloud/` 完全不會載入,`/models ls` 只會看到本地模型。

---

## 授權

本專案程式碼的授權見 `LICENSE`。改寫自 Hermes Agent 的部分依其 MIT 授權使用,
授權全文見 `LICENSES/hermes-agent-MIT.txt`。
