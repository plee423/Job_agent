# Job Search Agent Web App

A local web application for job discovery and job-search writing workflows.

## What it does

- Create and save **candidate profiles** with:
  - Resume text
  - LinkedIn profile URL
  - Extra experience stories
- Run job discovery cycles against credible, public feeds.
- Store jobs and run history in SQLite.
- Generate writing drafts for:
  - Cover letters
  - Cold LinkedIn messages
  - LinkedIn InMail
  - Slack messages
- Save per-profile writing customization guidelines as markdown files.
- Always maintain an `AGENT_ACTING_PRINCIPLES.md` markdown file in `data/`.

## Stack

- Flask web app (`app.py`)
- SQLite storage (`storage.py`)
- Source adapters (`sources.py`)
- Matcher/scorer (`matcher.py`)
- Message generation + guideline persistence (`writer.py`)

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

## Key routes

- `/` Home dashboard
- `/profiles/new` Create profile
- `/profiles/<id>` View profile + edit writing guidelines
- `/write` Generate writing drafts

## Data files

- `job_agent.db` SQLite database
- `data/profile_<id>_guidelines.md` writing preferences per profile
- `data/AGENT_ACTING_PRINCIPLES.md` persistent agent principles
