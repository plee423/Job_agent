from __future__ import annotations

import os
from datetime import datetime

import psycopg2
import psycopg2.extras

from sources import JobPosting


_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS profiles (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        linkedin_url TEXT NOT NULL,
        resume_text TEXT NOT NULL,
        extra_experience TEXT DEFAULT '',
        guidelines TEXT DEFAULT '',
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        source TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        title TEXT,
        company TEXT,
        location TEXT,
        published_at TEXT,
        snippet TEXT,
        score REAL,
        first_seen_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS runs (
        id SERIAL PRIMARY KEY,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        discovered_count INTEGER DEFAULT 0,
        inserted_count INTEGER DEFAULT 0,
        errors TEXT
    )
    """,
    # Migrate: add guidelines column if upgrading from the old schema
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'profiles' AND column_name = 'guidelines'
        ) THEN
            ALTER TABLE profiles ADD COLUMN guidelines TEXT DEFAULT '';
        END IF;
    END $$
    """,
]


class Storage:
    def __init__(self, url: str | None = None) -> None:
        self.conn = psycopg2.connect(url or os.environ["DATABASE_URL"])
        self.conn.autocommit = False
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self.conn.cursor() as cur:
            for stmt in _SCHEMA_STATEMENTS:
                cur.execute(stmt)
        self.conn.commit()

    def create_or_update_profile(self, name: str, linkedin_url: str, resume_text: str, extra_experience: str = "") -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO profiles(name, linkedin_url, resume_text, extra_experience, guidelines, updated_at)
                VALUES(%s, %s, %s, %s, '', %s)
                RETURNING id
                """,
                (name, linkedin_url, resume_text, extra_experience, datetime.utcnow().isoformat()),
            )
            row = cur.fetchone()
        self.conn.commit()
        return int(row[0])

    def list_profiles(self) -> list[dict]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, linkedin_url, resume_text, extra_experience, guidelines, updated_at FROM profiles ORDER BY id DESC"
            )
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_profile(self, profile_id: int) -> dict | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, linkedin_url, resume_text, extra_experience, guidelines, updated_at FROM profiles WHERE id = %s",
                (profile_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            return dict(zip(cols, row))

    def save_guidelines(self, profile_id: int, guidelines: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE profiles SET guidelines = %s WHERE id = %s",
                (guidelines.strip(), profile_id),
            )
        self.conn.commit()

    def recent_jobs(self, limit: int = 25) -> list[dict]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT source, url, title, company, location, published_at, snippet, score, first_seen_at
                FROM jobs
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def begin_run(self) -> int:
        with self.conn.cursor() as cur:
            cur.execute("INSERT INTO runs(started_at) VALUES(%s) RETURNING id", (datetime.utcnow().isoformat(),))
            row = cur.fetchone()
        self.conn.commit()
        return int(row[0])

    def end_run(self, run_id: int, discovered_count: int, inserted_count: int, errors: str = "") -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE runs
                SET finished_at = %s, discovered_count = %s, inserted_count = %s, errors = %s
                WHERE id = %s
                """,
                (datetime.utcnow().isoformat(), discovered_count, inserted_count, errors, run_id),
            )
        self.conn.commit()

    def add_if_new(self, posting: JobPosting) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO jobs(source, url, title, company, location, published_at, snippet, score, first_seen_at)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        except psycopg2.errors.UniqueViolation:
            self.conn.rollback()
            return False

    def close(self) -> None:
        self.conn.close()
