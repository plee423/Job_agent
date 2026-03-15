# Job Agent — Project Handover

> Model-agnostic project state document. Updated at the end of each working session.
> Read this file at the start of any session to resume mid-work efficiently.

---

## Current Issue

None known. All planned features for this session have been implemented.
Vercel deployment was in progress at the end of last session — database connection issue was being resolved.

---

## Immediate Next Step

1. Add `ANTHROPIC_API_KEY` to Vercel → Settings → Environment Variables to enable LLM resume analysis
2. Verify full deployment works end-to-end: profile creation → LLM analysis → job discovery run

---

## Open Decisions

- `SERPAPI_KEY` has not been confirmed as added to Vercel yet — SerpApi source (LinkedIn/Glassdoor via Google Jobs) is disabled without it
- LLM analysis runs once at profile creation time — no way to re-trigger it yet without recreating the profile. May want a "Re-analyze resume" button later.

---

## Recent Changes (this session)

| File | What changed | Why |
|------|-------------|-----|
| `requirements.txt` | Added `pypdf`, `python-docx`, `anthropic` | Resume file upload + LLM integration |
| `storage.py` | Added `location` and `llm_profile` columns to profiles table with auto-migration | Store preferred job location and LLM-extracted resume data per profile |
| `llm.py` | New file — sends resume to Claude (`claude-sonnet-4-6`), returns structured JSON: target roles, skills, seniority, industries, search keywords | Replace frequency-based keyword extraction with LLM-powered analysis |
| `matcher.py` | `build_profile()` now accepts `llm_profile` dict; uses LLM keywords + target roles when available, falls back to frequency-based | Smarter job matching using Claude's understanding of the resume |
| `sources.py` | `SerpApiSource` now passes `profile.location` to the Google Jobs query | Location-aware job search |
| `agent.py` | `run_cycle()` accepts `llm_profile` dict, passes it to `build_profile` | Thread LLM data through the discovery pipeline |
| `app.py` | Calls `analyze_resume()` on profile create; added location field; threads location + llm_profile into run cycle and cron endpoint; added resume file upload support | Full integration of new features |
| `templates/profile_form.html` | Added location field and resume file upload (PDF/DOCX) | User-facing input for new features |
| `templates/profile_detail.html` | Shows preferred location + AI analysis panel (seniority, target roles, skills, keywords) | Surface LLM results to user |
| `CLAUDE.md` | Updated to reflect Vercel hosting, added Principle 0 (execution plan before changes), Principle 6 (handover process) | Keep working manual current |
| `HANDOVER.md` | Rewritten to be model-agnostic | Works as shared context for Claude, Codex, or any other LLM |

---

## Environment Variables

| Variable | Required | Source |
|----------|----------|--------|
| `DATABASE_URL` | Yes | Supabase → Settings → Database → Connection Pooling → Transaction mode URL (replace `[YOUR-PASSWORD]` with actual DB password from Supabase → Settings → Database) |
| `ANTHROPIC_API_KEY` | No (disables LLM resume analysis if absent, falls back to keyword frequency) | console.anthropic.com |
| `SERPAPI_KEY` | No (disables SerpApi/Google Jobs source if absent) | serpapi.com account dashboard |

---

## Architecture Summary

```
profile create → _extract_resume_text() [PDF/DOCX in memory]
              → analyze_resume() [Claude API → structured JSON]
              → storage.create_or_update_profile() [Postgres via psycopg2]

profile run   → run_cycle() [agent.py]
              → build_profile() [matcher.py — uses llm_profile if available]
              → source.search() [RemoteOK, WeWorkRemotely, SerpApi]
              → storage.add_if_new() [deduplication]

cron (9am UTC daily) → /api/cron/run-all → runs cycle for every profile
```

## File Map

```
Job_agent/
├── app.py              # Flask routes
├── agent.py            # Discovery cycle logic
├── llm.py              # Claude API resume analysis (NEW)
├── sources.py          # RemoteOkSource, WeWorkRemotelySource, SerpApiSource
├── matcher.py          # Keyword extraction + scoring (LLM-aware)
├── writer.py           # generate_message() only
├── storage.py          # Postgres via psycopg2
├── requirements.txt    # Flask, psycopg2-binary, pypdf, python-docx, anthropic
├── vercel.json         # Routing + daily cron (9am UTC)
├── api/
│   └── index.py        # Vercel entry point (sys.path fix included)
├── templates/
│   ├── home.html
│   ├── profile_form.html   # Has file upload + location field
│   ├── profile_detail.html # Shows LLM analysis panel
│   └── writer_form.html
├── CLAUDE.md           # Working manual for Claude
└── HANDOVER.md         # This file
```
