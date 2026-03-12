# Job Search Agent Web App (Two-Agent Backend)

A local web application with a persistent backend service that runs **two cooperating agents**:

1. **Discovery Agent**: periodically scans credible job sources for each saved profile.
2. **Writer Agent**: automatically generates default cover-letter drafts for newly discovered jobs.

## Feature set

- Profile store with:
  - Resume text
  - LinkedIn URL
  - Additional experience stories
- Background two-agent service (start/stop from web UI)
- On-demand single run per profile
- Writing generation tools for:
  - Cover letters
  - Cold LinkedIn messages
  - LinkedIn InMail
  - Slack messages
- Per-profile writing customization guidelines saved as markdown
- Persistent acting principles markdown file (`data/AGENT_ACTING_PRINCIPLES.md`)

## Backend architecture

- `app.py`: Flask web app and route layer.
- `service.py`: long-lived orchestrator with two background workers.
  - Discovery loop runs every poll interval.
  - New jobs enqueue `(profile_id, job_id)` writing tasks.
  - Writer loop consumes queue and stores generated drafts.
- `storage.py`: SQLite data model and persistence.
  - `profiles`, `jobs`, `runs`, and `drafts` tables.
- `agent.py`: reusable run-cycle logic used by both CLI and service.
- `writer.py`: generation primitives + guidelines + acting principles.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:8000`.

## Job sources (default)

- Remote OK JSON feed
- We Work Remotely RSS feed

> Note: LinkedIn/Glassdoor protected-page scraping is intentionally not included.

## Data files

- `job_agent.db` SQLite database
- `data/profile_<id>_guidelines.md` writing preferences per profile
- `data/AGENT_ACTING_PRINCIPLES.md` persistent agent principles
