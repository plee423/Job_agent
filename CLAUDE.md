# Job Agent — Working Manual for Claude

## Project Overview

This is a **Flask web application** for job discovery and job-search writing workflows, hosted on **Vercel**.
It helps candidates find relevant remote jobs, score them against their profile, and generate
outreach materials (cover letters, LinkedIn messages, etc.).

Run locally with:
```bash
python app.py
# Open http://localhost:8000
```

Deployed on Vercel. Set `DATABASE_URL` in Vercel environment variables (Supabase Postgres connection string).

---

## Architecture

| File | Responsibility |
|------|---------------|
| [app.py](app.py) | Flask routes and web UI entry point |
| [agent.py](agent.py) | Periodic job discovery cycle logic |
| [sources.py](sources.py) | Job source adapters (Remote OK, We Work Remotely) |
| [matcher.py](matcher.py) | Keyword extraction, profile building, relevance scoring |
| [writer.py](writer.py) | Writing draft generation |
| [storage.py](storage.py) | Postgres database via psycopg2 (profiles, jobs, run history) |
| [api/index.py](api/index.py) | Vercel serverless entry point — imports `app` from app.py |
| [vercel.json](vercel.json) | Vercel routing + cron schedule |

### Templates
- [templates/home.html](templates/home.html) — Dashboard: profiles list + recent jobs
- [templates/profile_form.html](templates/profile_form.html) — Create/edit a candidate profile
- [templates/profile_detail.html](templates/profile_detail.html) — View profile + writing guidelines
- [templates/writer_form.html](templates/writer_form.html) — Generate outreach drafts

### Data storage
- **Supabase Postgres** — all persistent data (profiles, jobs, runs). Schema auto-creates on first connection.
- Guidelines are stored in the `profiles.guidelines` column — no flat files.
- No local file writes in production (Vercel filesystem is ephemeral).

---

## Hosting — Vercel

- All traffic is routed through `api/index.py` via `vercel.json` rewrites.
- Job discovery runs automatically once daily at 9am UTC via a Vercel Cron Job hitting `GET /api/cron/run-all` (Hobby plan limit: once per day).
- `DATABASE_URL` must be set as a Vercel environment variable (Supabase direct connection URI).
- Do **not** rely on the local filesystem in any code path — it will not persist between requests.

---

## Job Sources

| Source | Feed Type | Class |
|--------|-----------|-------|
| Remote OK | JSON API (`https://remoteok.com/api`) | `RemoteOkSource` |
| We Work Remotely | RSS feed (`https://weworkremotely.com/remote-jobs.rss`) | `WeWorkRemotelySource` |
| SerpApi (Google Jobs) | REST API | `SerpApiSource` (planned — covers LinkedIn/Glassdoor aggregated listings) |

Direct LinkedIn and Glassdoor scraping remain **excluded** (protected pages, ToS).

---

## Key Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Home dashboard |
| `/profiles/new` | GET | Profile creation form |
| `/profiles` | POST | Create a profile |
| `/profiles/<id>` | GET | View profile detail + guidelines |
| `/profiles/<id>/guidelines` | POST | Save writing guidelines |
| `/profiles/<id>/run` | POST | Trigger a job discovery cycle |
| `/write` | GET/POST | Generate writing drafts |
| `/api/cron/run-all` | GET | Vercel cron — runs discovery for all profiles |

---

## Scoring Logic (`matcher.py`)

Jobs are scored against a candidate profile using:
- **65% keyword overlap** — top 20 keywords extracted from resume vs. job title + description
- **35% title alignment** — role-type words (engineer, manager, etc.) in job title

Minimum score threshold: `0.15` (configurable via `--min-score` in CLI mode).

---

## Core Principles — Non-Negotiable

### 0. Execution Plan Before Any Code Change
- **Before making any code fix or change, present a clear execution plan to the user and wait for approval.**
- The plan must state: (1) the action Claude is about to take, and (2) the reasoning behind it in 1-2 short sentences.
- Do not proceed until the user confirms.

### 1. No Hallucination
- **Never invent job listings, company names, roles, or salaries.**
- All job data must come directly from what the source APIs/feeds return.
- If a source fails or returns no results, report that honestly — do not fabricate alternatives.

### 2. Always Show Source Links
- **Every job presented to the user must include its original URL.**
- The `JobPosting.url` field is mandatory. Jobs with no URL are skipped (`agent.py:48`).
- In any output (UI, logs, messages), the source link must be visible and clickable.
- Never summarize a job without attributing it to its source.

### 3. Truthful Writing Generation
- Writing drafts (cover letters, messages) must reflect the candidate's actual profile data.
- Do not add skills, roles, or accomplishments not present in `resume_text` or `extra_experience`.
- Flag to the user if the profile data is too sparse to generate a credible draft.

### 4. No Unauthorized Scraping
- Do not add scrapers that bypass authentication, CAPTCHAs, or rate limits.
- Only use publicly documented APIs or RSS feeds with appropriate `User-Agent` headers.

### 5. Data Integrity
- Profiles are stored in Postgres. Do not silently overwrite or delete profile data.
- The `add_if_new` deduplication in `storage.py` must be preserved — do not bypass it.

### 6. Context Handover
- **Read `HANDOVER.md` at the start of any session** where the user references prior work — before doing anything else.
- **Update `HANDOVER.md` continuously** as changes are made — not just at session end. Every meaningful file change, decision, or resolved issue should be reflected immediately.
- When context reaches ~95% capacity, do a final `HANDOVER.md` update, then ask the user to start a new conversation referencing it.
- `HANDOVER.md` is model-agnostic — do not write Claude-specific language into it. It is shared with Codex and other models via their own config files (`AGENTS.md`, etc.).

---

## Developer Notes

- Python 3.10+ required (uses `X | Y` union syntax).
- Dependencies: Flask, psycopg2-binary (see `requirements.txt`). No LLM SDKs currently.
- Tests live in [tests/](tests/) — run with `pytest`.
- The `writer.py` `generate_message` function is currently template-based (no LLM call).
  If an LLM is wired in later, the no-hallucination principle above becomes even more critical.
