# Job Agent — Working Manual for Codex

## Start Here

Read [`HANDOVER.md`](HANDOVER.md) before doing anything else in a resumed session.
It contains current project state, active issues, recent changes, and next steps.

---

## Project Overview

Flask web application for job discovery and outreach writing, hosted on **Vercel** with **Supabase Postgres**.
Candidates upload a resume, get it analyzed by Claude AI, and the app finds matching remote jobs and generates outreach drafts.

Run locally:
```bash
pip install -r requirements.txt
python app.py
# Open http://localhost:8000
```

---

## Architecture

| File | Responsibility |
|------|---------------|
| `app.py` | Flask routes and web UI entry point |
| `agent.py` | Job discovery cycle logic |
| `llm.py` | Claude API resume analysis |
| `sources.py` | Job source adapters (Remote OK, We Work Remotely, SerpApi) |
| `matcher.py` | Keyword extraction and relevance scoring |
| `writer.py` | Outreach draft generation |
| `storage.py` | Postgres via psycopg2 |
| `api/index.py` | Vercel serverless entry point |
| `vercel.json` | Vercel routing + daily cron (9am UTC) |

### Templates
- `templates/home.html` — Dashboard
- `templates/profile_form.html` — Create profile (file upload + location)
- `templates/profile_detail.html` — Profile detail + AI analysis panel
- `templates/writer_form.html` — Generate outreach drafts

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | Yes | Supabase Postgres connection string (transaction pooler, port 6543) |
| `ANTHROPIC_API_KEY` | No | Enables LLM resume analysis via Claude |
| `SERPAPI_KEY` | No | Enables Google Jobs source (LinkedIn/Glassdoor aggregated) |

---

## Key Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Home dashboard |
| `/profiles/new` | GET | Profile creation form |
| `/profiles` | POST | Create a profile |
| `/profiles/<id>` | GET | Profile detail + AI analysis |
| `/profiles/<id>/guidelines` | POST | Save writing guidelines |
| `/profiles/<id>/run` | POST | Trigger job discovery |
| `/write` | GET/POST | Generate outreach drafts |
| `/api/cron/run-all` | GET | Vercel cron — runs discovery for all profiles |

---

## Core Principles — Non-Negotiable

### 0. Execution Plan Before Any Code Change
- Before making any fix or change, state: (1) the action you are about to take, and (2) the reasoning in 1-2 sentences.
- Wait for user confirmation before proceeding.

### 1. No Hallucination
- Never invent job listings, company names, roles, or salaries.
- All job data must come directly from source APIs/feeds.
- Report failures honestly — do not fabricate alternatives.

### 2. Always Show Source Links
- Every job must include its original URL. Jobs with no URL are skipped.
- Never summarize a job without attributing it to its source.

### 3. Truthful Writing Generation
- Drafts must reflect only the candidate's actual profile data.
- Do not add skills or accomplishments not present in `resume_text` or `extra_experience`.

### 4. No Unauthorized Scraping
- Only use publicly documented APIs or RSS feeds with appropriate `User-Agent` headers.
- No CAPTCHA bypass, no auth bypass, no rate limit evasion.

### 5. Data Integrity
- Do not silently overwrite or delete profile data.
- The `add_if_new` deduplication in `storage.py` must be preserved.

### 6. Context Handover
- Read `HANDOVER.md` at the start of any resumed session.
- Update `HANDOVER.md` continuously as changes are made — not just at session end.
- `HANDOVER.md` is model-agnostic. Do not write model-specific language into it.
