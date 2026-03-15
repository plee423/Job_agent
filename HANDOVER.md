# Job Agent — Project Handover

> Model-agnostic project state document. Updated at the end of each working session.
> Read this file at the start of any session to resume mid-work efficiently.

---

## Current Issue

Vercel deployment is live but the app is returning 500 errors on all routes due to Supabase authentication failure.

**Root cause:** `DATABASE_URL` environment variable in Vercel still contains the `[YOUR-PASSWORD]` placeholder.

**Fix in progress:** User is replacing the placeholder with the actual Supabase database password (found in Supabase → Settings → Database → Database password), then redeploying.

**Connection details:**
- Using Supabase **transaction pooler** (not direct connection)
- Host: `aws-0-us-west-2.pooler.supabase.com`, port `6543`
- Username format: `postgres.hsqlgrngdbcrtmhdkgnq`

---

## Immediate Next Step

Verify the app loads at the Vercel URL after the correct `DATABASE_URL` is set and a redeploy is triggered.

---

## Open Decisions

- `SERPAPI_KEY` has not been added to Vercel yet — SerpApi source (LinkedIn/Glassdoor via Google Jobs) is currently disabled. User needs to add it when ready.

---

## Recent Changes (last session)

| File | What changed | Why |
|------|-------------|-----|
| `storage.py` | Rewrote from `sqlite3` → `psycopg2`. Added `guidelines` column to `profiles`. | Vercel filesystem is ephemeral; Supabase Postgres is the persistent store. |
| `app.py` | Removed file-based guidelines logic. Added `/api/cron/run-all` endpoint. | Guidelines now live in DB. Cron replaces the background polling loop. |
| `writer.py` | Removed file I/O functions. Only `generate_message()` remains. | No file writes allowed in serverless environment. |
| `requirements.txt` | Added `psycopg2-binary>=2.9`. | Required for Postgres connection. |
| `vercel.json` | New — routes all traffic to `api/index`, daily cron at 9am UTC. | Cron limited to once/day on Vercel Hobby plan. |
| `api/index.py` | New — adds project root to `sys.path`, imports Flask `app`. | Vercel needs an entry point in `api/`; `sys.path` fix required for sibling imports. |
| `sources.py` | Added `SerpApiSource` class. | Covers LinkedIn/Glassdoor listings via Google Jobs API. |
| `CLAUDE.md` | Updated to reflect Vercel hosting, new principles added. | Keeps working manual current. |

---

## Environment Variables

| Variable | Required | Source |
|----------|----------|--------|
| `DATABASE_URL` | Yes | Supabase → Settings → Database → Connection Pooling → Transaction mode (replace `[YOUR-PASSWORD]`) |
| `SERPAPI_KEY` | No (disables SerpApi source if absent) | serpapi.com account dashboard |
