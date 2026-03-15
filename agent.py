from __future__ import annotations

import argparse
import time
from typing import Iterable

from matcher import build_profile, read_resume_text
from sources import default_sources, JobPosting
from storage import Storage


def _parse_keywords(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]


def _print_alert(posting: JobPosting) -> None:
    print("-" * 100)
    print(f"[{posting.source}] {posting.title} | {posting.company} | score={posting.score}")
    print(f"Location: {posting.location}")
    print(f"URL: {posting.url}")
    if posting.snippet:
        print(f"Snippet: {posting.snippet[:220]}")


def run_cycle(store: Storage, resume_text: str, linkedin_url: str, keywords: Iterable[str], location: str | None, min_score: float, llm_profile: dict | None = None) -> tuple[int, int]:
    profile = build_profile(
        resume_text=resume_text,
        linkedin_url=linkedin_url,
        user_keywords=keywords,
        location=location,
        llm_profile=llm_profile,
    )

    discovered = 0
    inserted = 0
    for source in default_sources():
        try:
            results = source.search(profile, min_score=min_score)
        except Exception as exc:
            print(f"[WARN] source={source.name} failed: {exc}")
            continue

        discovered += len(results)
        for job in results:
            if not job.url:
                continue
            if store.add_if_new(job):
                inserted += 1
                _print_alert(job)

    return discovered, inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Periodic job discovery agent")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run periodic search")
    run.add_argument("--resume", required=True, help="Path to plain-text resume file")
    run.add_argument("--linkedin-url", help="LinkedIn profile URL")
    run.add_argument("--keywords", help="Comma-separated keywords")
    run.add_argument("--location", help="Preferred location, e.g., 'remote' or 'NYC'")
    run.add_argument("--interval", type=int, default=1800, help="Polling interval in seconds")
    run.add_argument("--db", default="job_agent.db", help="SQLite database path")
    run.add_argument("--min-score", type=float, default=0.15, help="Min relevance score [0..1]")
    run.add_argument("--once", action="store_true", help="Run only one cycle")

    args = parser.parse_args()
    if args.command != "run":
        raise ValueError("Unsupported command")

    linkedin_url = args.linkedin_url or input("LinkedIn profile URL: ").strip()
    if not linkedin_url:
        raise SystemExit("LinkedIn URL is required.")

    resume_text = read_resume_text(args.resume)
    keywords = _parse_keywords(args.keywords)

    store = Storage(args.db)
    try:
        while True:
            run_id = store.begin_run()
            errors = ""
            try:
                discovered, inserted = run_cycle(
                    store,
                    resume_text=resume_text,
                    linkedin_url=linkedin_url,
                    keywords=keywords,
                    location=args.location,
                    min_score=args.min_score,
                )
                print(f"Cycle complete: discovered={discovered}, new={inserted}")
            except Exception as exc:
                discovered = inserted = 0
                errors = str(exc)
                print(f"[ERROR] cycle failed: {exc}")
            finally:
                store.end_run(run_id, discovered, inserted, errors)

            if args.once:
                break
            time.sleep(max(30, args.interval))
    finally:
        store.close()


if __name__ == "__main__":
    main()
