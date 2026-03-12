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
"""


class Storage:
    def __init__(self, path: str = "job_agent.db") -> None:
        self.path = path
        self.conn = sqlite3.connect(self.path)
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
        cur = self.conn.execute(
            "SELECT id, name, linkedin_url, resume_text, extra_experience, updated_at FROM profiles ORDER BY id DESC"
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_profile(self, profile_id: int) -> dict | None:
        cur = self.conn.execute(
            "SELECT id, name, linkedin_url, resume_text, extra_experience, updated_at FROM profiles WHERE id = ?",
            (profile_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

    def recent_jobs(self, limit: int = 25) -> list[dict]:
        cur = self.conn.execute(
            """
            SELECT source, url, title, company, location, published_at, snippet, score, first_seen_at
            FROM jobs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

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
