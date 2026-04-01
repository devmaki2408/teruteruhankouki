# database.py
# ============================================================
# SQLite を使ったデータ永続化層。
# DB ファイルは data/app.db に配置する。
# テーブルは初回接続時に自動作成される。
# ============================================================

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")


# ------------------------------------------------------------------
# 接続管理
# ------------------------------------------------------------------

@contextmanager
def get_connection():
    """コンテキストマネージャ形式で接続を提供し、終了時に自動コミット・クローズする。"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # カラム名でアクセス可能にする
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    """テーブルが存在しない場合に作成する。アプリ起動時に呼ぶ。"""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                target      TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS issues (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  INTEGER NOT NULL,
                issue_index INTEGER NOT NULL,
                text        TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS ideas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  INTEGER NOT NULL,
                issue_id    INTEGER NOT NULL,
                idea_index  INTEGER NOT NULL,
                title       TEXT NOT NULL,
                summary     TEXT NOT NULL,
                score       INTEGER NOT NULL,
                detail_json TEXT,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (issue_id)   REFERENCES issues(id)
            );
        """)


# ------------------------------------------------------------------
# セッション
# ------------------------------------------------------------------

def create_session(target: str) -> int:
    """新しいセッションを作成して session_id を返す。"""
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (target, created_at) VALUES (?, ?)",
            (target, now),
        )
        return cur.lastrowid


def get_session(session_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None


# ------------------------------------------------------------------
# 課題
# ------------------------------------------------------------------

def save_issues(session_id: int, issues: list[dict]) -> list[int]:
    """
    課題リストを DB に保存し、挿入した行の id リストを返す。
    issues の各要素は {"text": str} を持つ辞書を想定。
    """
    now = datetime.utcnow().isoformat()
    ids = []
    with get_connection() as conn:
        for idx, issue in enumerate(issues):
            cur = conn.execute(
                "INSERT INTO issues (session_id, issue_index, text, created_at) VALUES (?, ?, ?, ?)",
                (session_id, idx, issue["text"], now),
            )
            ids.append(cur.lastrowid)
    return ids


def get_issues(session_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM issues WHERE session_id = ? ORDER BY issue_index",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ------------------------------------------------------------------
# 事業案
# ------------------------------------------------------------------

def save_ideas(session_id: int, issue_db_id: int, ideas: list[dict]) -> list[int]:
    """
    事業案リストを DB に保存し、挿入した行の id リストを返す。
    ideas の各要素は {"title", "summary", "score"} を持つ辞書を想定。
    """
    now = datetime.utcnow().isoformat()
    ids = []
    with get_connection() as conn:
        for idx, idea in enumerate(ideas):
            cur = conn.execute(
                """INSERT INTO ideas
                   (session_id, issue_id, idea_index, title, summary, score, detail_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    issue_db_id,
                    idx,
                    idea["title"],
                    idea["summary"],
                    idea["score"],
                    None,
                    now,
                ),
            )
            ids.append(cur.lastrowid)
    return ids


def get_ideas(session_id: int, issue_db_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM ideas WHERE session_id = ? AND issue_id = ? ORDER BY idea_index",
            (session_id, issue_db_id),
        ).fetchall()
        return [dict(r) for r in rows]


# ------------------------------------------------------------------
# 詳細（detail_json の保存・取得）
# ------------------------------------------------------------------

def save_detail(idea_db_id: int, detail: dict) -> None:
    """事業案の詳細分析結果を JSON 文字列として保存する。"""
    with get_connection() as conn:
        conn.execute(
            "UPDATE ideas SET detail_json = ? WHERE id = ?",
            (json.dumps(detail, ensure_ascii=False), idea_db_id),
        )


def get_detail(idea_db_id: int) -> Optional[dict]:
    """保存済みの詳細分析結果を返す。未保存なら None。"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT detail_json FROM ideas WHERE id = ?", (idea_db_id,)
        ).fetchone()
        if row and row["detail_json"]:
            return json.loads(row["detail_json"])
        return None