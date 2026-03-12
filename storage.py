from __future__ import annotations

import sqlite3
from datetime import datetime

from sources import JobPosting


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    company TEXT,
    location TEXT,
    published_at TEXT,
    snippet TEXT,
    score REAL,
    first_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    linkedin_url TEXT NOT NULL,
    resume_text TEXT NOT NULL,
    extra_experience TEXT DEFAULT "",
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    discovered_count INTEGER DEFAULT 0,
    inserted_count INTEGER DEFAULT 0,
    errors TEXT
);

CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(profile_id, job_id, message_type),
    FOREIGN KEY(profile_id) REFERENCES profiles(id),
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
"""


class Storage:
    def __init__(self, path: str = "job_agent.db") -> None:
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def create_or_update_profile(self, name: str, linkedin_url: str, resume_text: str, extra_experience: str = "") -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO profiles(name, linkedin_url, resume_text, extra_experience, updated_at)
            VALUES(?, ?, ?, ?, ?)
            """,
            (name, linkedin_url, resume_text, extra_experience, datetime.utcnow().isoformat()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_profiles(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, name, linkedin_url, resume_text, extra_experience, updated_at FROM profiles ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_profile(self, profile_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT id, name, linkedin_url, resume_text, extra_experience, updated_at FROM profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()
        return dict(row) if row else None

    def recent_jobs(self, limit: int = 25) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT id, source, url, title, company, location, published_at, snippet, score, first_seen_at
            FROM jobs ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_job_id_by_url(self, url: str) -> int | None:
        row = self.conn.execute("SELECT id FROM jobs WHERE url = ?", (url,)).fetchone()
        return int(row["id"]) if row else None

    def get_job(self, job_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT id, source, url, title, company, location, published_at, snippet, score, first_seen_at FROM jobs WHERE id = ?",
            (job_id,),
        ).fetchone()
        return dict(row) if row else None

    def create_or_update_draft(self, profile_id: int, job_id: int, message_type: str, content: str, status: str) -> int:
        self.conn.execute(
            """
            INSERT INTO drafts(profile_id, job_id, message_type, content, status, updated_at)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_id, job_id, message_type)
            DO UPDATE SET content = excluded.content, status = excluded.status, updated_at = excluded.updated_at
            """,
            (profile_id, job_id, message_type, content, status, datetime.utcnow().isoformat()),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM drafts WHERE profile_id = ? AND job_id = ? AND message_type = ?",
            (profile_id, job_id, message_type),
        ).fetchone()
        return int(row["id"])

    def list_drafts(self, profile_id: int | None = None, limit: int = 50) -> list[dict]:
        if profile_id is None:
            rows = self.conn.execute(
                """
                SELECT d.id, d.profile_id, d.job_id, d.message_type, d.status, d.updated_at,
                       j.title AS job_title, j.company AS job_company
                FROM drafts d
                JOIN jobs j ON j.id = d.job_id
                ORDER BY d.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT d.id, d.profile_id, d.job_id, d.message_type, d.status, d.updated_at,
                       j.title AS job_title, j.company AS job_company
                FROM drafts d
                JOIN jobs j ON j.id = d.job_id
                WHERE d.profile_id = ?
                ORDER BY d.id DESC
                LIMIT ?
                """,
                (profile_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def begin_run(self) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO runs(started_at) VALUES(?)", (datetime.utcnow().isoformat(),))
        self.conn.commit()
        return int(cur.lastrowid)

    def end_run(self, run_id: int, discovered_count: int, inserted_count: int, errors: str = "") -> None:
        self.conn.execute(
            """
            UPDATE runs
            SET finished_at = ?, discovered_count = ?, inserted_count = ?, errors = ?
            WHERE id = ?
            """,
            (datetime.utcnow().isoformat(), discovered_count, inserted_count, errors, run_id),
        )
        self.conn.commit()

    def add_if_new(self, posting: JobPosting) -> bool:
        try:
            self.conn.execute(
                """
                INSERT INTO jobs(source, url, title, company, location, published_at, snippet, score, first_seen_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    posting.source,
                    posting.url,
                    posting.title,
                    posting.company,
                    posting.location,
                    posting.published_at,
                    posting.snippet,
                    posting.score,
                    datetime.utcnow().isoformat(),
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def close(self) -> None:
        self.conn.close()
