import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from backend.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    pub_date TEXT,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS article_keywords (
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    keyword_id INTEGER NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, keyword_id)
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(SCHEMA)


# --- keywords ---

def add_keyword(keyword: str) -> bool:
    """중복이면 False, 신규 등록이면 True."""
    with get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO keywords (keyword, created_at) VALUES (?, ?)",
                (keyword, datetime.now(timezone.utc).isoformat()),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def delete_keyword(keyword_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))


def list_keywords() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, keyword, created_at FROM keywords ORDER BY keyword"
        ).fetchall()
        return [dict(row) for row in rows]


def keyword_exists(keyword: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM keywords WHERE keyword = ?", (keyword,)
        ).fetchone()
        return row is not None


# --- articles ---

def upsert_article(article: dict, matched_keyword_ids: list[int]) -> bool:
    """link 기준 upsert. 매칭된 키워드는 기존 태그와 합집합으로 병합.

    Returns: 신규 기사면 True, 기존 기사 갱신이면 False.
    """
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM articles WHERE link = ?", (article["link"],)
        ).fetchone()

        if existing:
            article_id = existing["id"]
            conn.execute(
                """
                UPDATE articles
                SET title = ?, description = ?, pub_date = ?, synced_at = ?
                WHERE id = ?
                """,
                (
                    article["title"],
                    article.get("description", ""),
                    article.get("pub_date", ""),
                    now,
                    article_id,
                ),
            )
            is_new = False
        else:
            cursor = conn.execute(
                """
                INSERT INTO articles (link, title, description, pub_date, synced_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    article["link"],
                    article["title"],
                    article.get("description", ""),
                    article.get("pub_date", ""),
                    now,
                ),
            )
            article_id = cursor.lastrowid
            is_new = True

        for keyword_id in matched_keyword_ids:
            conn.execute(
                "INSERT OR IGNORE INTO article_keywords (article_id, keyword_id) VALUES (?, ?)",
                (article_id, keyword_id),
            )
        return is_new


def list_articles_for_keyword(keyword_id: int, limit: int = 200) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.link, a.title, a.description, a.pub_date, a.synced_at
            FROM articles a
            JOIN article_keywords ak ON ak.article_id = a.id
            WHERE ak.keyword_id = ?
            ORDER BY a.pub_date DESC
            LIMIT ?
            """,
            (keyword_id, limit),
        ).fetchall()
        return [_with_keywords(conn, dict(row)) for row in rows]


def list_unclassified_articles(limit: int = 200) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.link, a.title, a.description, a.pub_date, a.synced_at
            FROM articles a
            LEFT JOIN article_keywords ak ON ak.article_id = a.id
            WHERE ak.article_id IS NULL
            ORDER BY a.pub_date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_with_keywords(conn, dict(row)) for row in rows]


def _with_keywords(conn: sqlite3.Connection, article: dict) -> dict:
    kw_rows = conn.execute(
        """
        SELECT k.keyword FROM keywords k
        JOIN article_keywords ak ON ak.keyword_id = k.id
        WHERE ak.article_id = ?
        """,
        (article["id"],),
    ).fetchall()
    article["keywords"] = [row["keyword"] for row in kw_rows]
    return article


def list_all_articles() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, link FROM articles").fetchall()
        return [dict(row) for row in rows]


def delete_articles(article_ids: list[int]) -> int:
    if not article_ids:
        return 0
    with get_connection() as conn:
        placeholders = ",".join("?" * len(article_ids))
        cursor = conn.execute(
            f"DELETE FROM articles WHERE id IN ({placeholders})", article_ids
        )
        return cursor.rowcount


def article_link_exists(link: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM articles WHERE link = ?", (link,)).fetchone()
        return row is not None


# --- meta ---

def set_meta(key: str, value: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_meta(key: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None
