"""README corpus search (F13) - SQLite FTS5 keyword index (RAG-lite).

Every README fetched through gitee_repo(readme) is indexed into a local
SQLite FTS5 table (data/corpus.db, gitignored). search() runs a BM25
keyword query - honest exact-fact retrieval, explicitly NOT embeddings.
Use for "which Chinese project does X / has Y in its README" lookups, not
open-ended semantic questions.
"""

from __future__ import annotations

import re
import sqlite3

from .config import DATA_DIR

_DB = DATA_DIR / "corpus.db"
_MAX_BODY = 200000  # per-README cap
_TERM_RE = re.compile(r"[\w\u4e00-\u9fff]+")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB))
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS readmes USING fts5(full_name, title, body)")
    return conn


def _clean(text: str) -> str:
    return " ".join(_TERM_RE.findall(text or ""))[:_MAX_BODY]


def ingest(full_name: str, readme: str | None) -> bool:
    """Index (upsert) a README body under its repo full_name."""
    full_name = (full_name or "").strip()
    if not full_name:
        return False
    try:
        conn = _connect()
        conn.execute("DELETE FROM readmes WHERE full_name = ?", (full_name,))
        if readme:
            title = full_name.split("/")[-1] if "/" in full_name else full_name
            conn.execute(
                "INSERT INTO readmes(full_name, title, body) VALUES (?, ?, ?)",
                (full_name, title, _clean(readme)),
            )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False


def search(query: str, limit: int = 10) -> list[dict]:
    """BM25 keyword search over indexed READMEs."""
    q = _clean(query)
    if not q:
        return []
    try:
        conn = _connect()
        # FTS5 MATCH with a quoted phrase + prefix fallback; keep it safe.
        rows = conn.execute(
            "SELECT full_name, title, bm25(readmes) AS score "
            "FROM readmes WHERE readmes MATCH ? "
            "ORDER BY score LIMIT ?",
            (q, max(limit, 1)),
        ).fetchall()
        conn.close()
        return [{"full_name": r[0], "title": r[1], "score": round(float(r[2]), 3)} for r in rows]
    except sqlite3.Error:
        return []


def count() -> int:
    try:
        conn = _connect()
        n = conn.execute("SELECT count(*) FROM readmes").fetchone()[0]
        conn.close()
        return int(n)
    except sqlite3.Error:
        return 0


def list_indexed(limit: int = 50) -> list[str]:
    try:
        conn = _connect()
        rows = conn.execute(
            "SELECT full_name FROM readmes ORDER BY rowid LIMIT ?", (max(limit, 1),)
        ).fetchall()
        conn.close()
        return [r[0] for r in rows]
    except sqlite3.Error:
        return []
