# memory/provider.py
#
# SQLite + FTS5 記憶後端的設計參考 NousResearch/hermes-agent (MIT) 的 hermes_state 層:
#   - WAL 模式(多讀單寫)
#   - FTS5 全文搜尋,使用 trigram tokenizer(可正確處理中文 / CJK)
# 參見 LICENSES/hermes-agent-MIT.txt
import json
import os
import time
import sqlite3
from abc import ABC, abstractmethod
from constants import get_memory_dir


class BaseMemoryProvider(ABC):
    """記憶後端介面。大腦引擎只透過 MemoryManager 間接使用,不直接碰這層。"""

    @abstractmethod
    def save(self, session_id, data):
        ...

    @abstractmethod
    def load(self, session_id):
        ...

    @abstractmethod
    def list_sessions(self):
        ...

    def search(self, query, limit=20):
        """
        跨 session 全文搜尋,回傳 [{"session_id","role","content"}]。
        預設實作:掃描所有 session 做子字串比對(給沒有專屬搜尋能力的後端用,如 JSON)。
        SQLite 後端會以 FTS5 覆寫這個方法。
        """
        results = []
        needle = (query or "").lower()
        if not needle:
            return results
        for sid in self.list_sessions():
            data = self.load(sid)
            for msg in data.get("history", []):
                content = msg.get("content", "") or ""
                if needle in content.lower():
                    results.append({
                        "session_id": sid,
                        "role": msg.get("role"),
                        "content": content,
                    })
                    if len(results) >= limit:
                        return results
        return results


class JSONMemoryProvider(BaseMemoryProvider):
    """[Fallback] 以 JSON 檔讀寫記憶,一個 session 一個檔。路徑由 constants 控管。"""

    def __init__(self, storage_dir=None):
        self.storage_dir = storage_dir if storage_dir else get_memory_dir()
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_file_path(self, session_id):
        return os.path.join(self.storage_dir, f"{session_id}.json")

    def save(self, session_id, data):
        file_path = self._get_file_path(session_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, session_id):
        file_path = self._get_file_path(session_id)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"summary": "", "history": []}

    def list_sessions(self):
        """掃描記憶目錄,回傳所有存在的 session 名稱"""
        if not os.path.exists(self.storage_dir):
            return []
        return [fn[:-5] for fn in os.listdir(self.storage_dir) if fn.endswith(".json")]


class SQLiteMemoryProvider(BaseMemoryProvider):
    """
    [預設] 以 SQLite 儲存記憶,並以 FTS5 提供跨 session 全文搜尋。

    資料格式對外維持與 JSON 後端一致:load() 回傳 {"summary", "history": [...]}。
    儲存模型:
      - sessions(session_id PK, summary, source, updated_at)
      - messages(id PK, session_id, seq, role, content, created_at)
      - messages_fts  : FTS5(content) trigram,手動與 messages 同步
    FTS5 若在此 SQLite build 不可用,會自動退回父類別的子字串搜尋。
    """

    def __init__(self, db_path=None, source="cli"):
        self.source = source
        if db_path is None:
            db_path = os.path.join(str(get_memory_dir()), "maverick.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._fts_enabled = False
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._connect()
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    summary    TEXT DEFAULT '',
                    source     TEXT DEFAULT 'cli',
                    updated_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    seq        INTEGER NOT NULL,
                    role       TEXT,
                    content    TEXT,
                    created_at REAL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, seq)"
            )
            # FTS5(trigram:對中文友善)。不可用則退回父類別搜尋。
            try:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
                    USING fts5(content, session_id UNINDEXED, tokenize='trigram')
                """)
                self._fts_enabled = True
            except sqlite3.OperationalError:
                self._fts_enabled = False
            conn.commit()
        finally:
            conn.close()

    def save(self, session_id, data):
        summary = data.get("summary", "") or ""
        history = data.get("history", []) or []
        now = time.time()
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO sessions(session_id, summary, source, updated_at) VALUES(?,?,?,?) "
                "ON CONFLICT(session_id) DO UPDATE SET summary=excluded.summary, updated_at=excluded.updated_at",
                (session_id, summary, self.source, now),
            )
            # 整個 session 重寫:先清掉舊訊息(含 FTS),再重建
            conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
            if self._fts_enabled:
                conn.execute("DELETE FROM messages_fts WHERE session_id=?", (session_id,))
            for seq, msg in enumerate(history):
                role = msg.get("role")
                content = msg.get("content", "") or ""
                conn.execute(
                    "INSERT INTO messages(session_id, seq, role, content, created_at) VALUES(?,?,?,?,?)",
                    (session_id, seq, role, content, now),
                )
                if self._fts_enabled and content:
                    conn.execute(
                        "INSERT INTO messages_fts(content, session_id) VALUES(?,?)",
                        (content, session_id),
                    )
            conn.commit()
        finally:
            conn.close()

    def load(self, session_id):
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT summary FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if row is None:
                return {"summary": "", "history": []}
            msgs = conn.execute(
                "SELECT role, content FROM messages WHERE session_id=? ORDER BY seq ASC",
                (session_id,),
            ).fetchall()
            history = [{"role": m["role"], "content": m["content"]} for m in msgs]
            return {"summary": row["summary"] or "", "history": history}
        finally:
            conn.close()

    def list_sessions(self):
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT session_id FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
            return [r["session_id"] for r in rows]
        finally:
            conn.close()

    def search(self, query, limit=20):
        if not query:
            return []
        # FTS5 trigram 需要 >= 3 字元才能比對;較短的查詢(常見的中文雙字詞,如
        # 「天氣」)改用子字串掃描,避免漏掉命中。
        if not self._fts_enabled or len(query.strip()) < 3:
            return super().search(query, limit=limit)
        conn = self._connect()
        try:
            # 以雙引號包起查詢字串,避免 FTS5 把輸入當成運算子語法
            fts_query = '"' + query.replace('"', '""') + '"'
            try:
                rows = conn.execute(
                    "SELECT session_id, content FROM messages_fts "
                    "WHERE messages_fts MATCH ? LIMIT ?",
                    (fts_query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                return super().search(query, limit=limit)
            return [{"session_id": r["session_id"], "role": None, "content": r["content"]}
                    for r in rows]
        finally:
            conn.close()
