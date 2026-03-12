from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, redirect, render_template, request, url_for

from agent import run_cycle
from service import ServiceConfig, TwoAgentService
from storage import Storage
from writer import generate_message, load_guidelines, save_guidelines

app = Flask(__name__)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
SERVICE = TwoAgentService(ServiceConfig(data_dir=DATA_DIR, db_path="job_agent.db", poll_interval_seconds=900, min_score=0.15))


@app.get("/")
def home() -> str:
    store = Storage()
    try:
        profiles = store.list_profiles()
        jobs = store.recent_jobs(limit=25)
        drafts = store.list_drafts(limit=25)
    finally:
        store.close()
    return render_template("home.html", profiles=profiles, jobs=jobs, drafts=drafts, service_status=SERVICE.status())


@app.post("/service/start")
def start_service() -> Any:
    SERVICE.start()
    return redirect(url_for("home"))


@app.post("/service/stop")
def stop_service() -> Any:
    SERVICE.stop()
    return redirect(url_for("home"))


@app.get("/profiles/new")
def new_profile_form() -> str:
    return render_template("profile_form.html", profile={})


@app.post("/profiles")
def create_profile() -> Any:
    name = request.form.get("name", "").strip()
    linkedin_url = request.form.get("linkedin_url", "").strip()
    resume_text = request.form.get("resume_text", "").strip()
    extra_experience = request.form.get("extra_experience", "").strip()

    if not name or not linkedin_url or not resume_text:
        return "name, linkedin_url, and resume_text are required", 400

    store = Storage()
    try:
        store.create_or_update_profile(
            name=name,
            linkedin_url=linkedin_url,
            resume_text=resume_text,
            extra_experience=extra_experience,
        )
    finally:
        store.close()

    return redirect(url_for("home"))


@app.get("/profiles/<int:profile_id>")
def profile_detail(profile_id: int) -> str:
    store = Storage()
    try:
        profile = store.get_profile(profile_id)
        drafts = store.list_drafts(profile_id=profile_id)
    finally:
        store.close()

    if not profile:
        return "profile not found", 404

    guidelines = load_guidelines(DATA_DIR / f"profile_{profile_id}_guidelines.md")
    return render_template("profile_detail.html", profile=profile, guidelines=guidelines, drafts=drafts)


@app.post("/profiles/<int:profile_id>/guidelines")
def save_profile_guidelines(profile_id: int) -> Any:
    content = request.form.get("guidelines", "")
    save_guidelines(DATA_DIR / f"profile_{profile_id}_guidelines.md", content)
    return redirect(url_for("profile_detail", profile_id=profile_id))


@app.post("/profiles/<int:profile_id>/run")
def run_profile_cycle(profile_id: int) -> Any:
    store = Storage()
    try:
        profile = store.get_profile(profile_id)
        if not profile:
            return "profile not found", 404
        run_id = store.begin_run()
        discovered, inserted = run_cycle(
            store,
            resume_text=profile["resume_text"],
            linkedin_url=profile["linkedin_url"],
            keywords=profile["extra_experience"].split(",") if profile["extra_experience"] else [],
            location=None,
            min_score=0.15,
        )
        store.end_run(run_id, discovered, inserted, "")
    finally:
        store.close()
    return redirect(url_for("home"))


@app.get("/write")
def write_form() -> str:
    store = Storage()
    try:
        profiles = store.list_profiles()
    finally:
        store.close()
    return render_template("writer_form.html", profiles=profiles, output="")


@app.post("/write")
def write_generate() -> str:
    store = Storage()
    try:
        profiles = store.list_profiles()
        profile_id = int(request.form.get("profile_id", "0"))
        profile = store.get_profile(profile_id)
    finally:
        store.close()

    if not profile:
        return "profile not found", 404

    message_type = request.form.get("message_type", "cover_letter")
    role = request.form.get("role", "").strip()
    company = request.form.get("company", "").strip()
    context = request.form.get("context", "").strip()
    guidelines = load_guidelines(DATA_DIR / f"profile_{profile_id}_guidelines.md")

    output = generate_message(
        message_type=message_type,
        profile=profile,
        role=role,
        company=company,
        context=context,
        guidelines=guidelines,
    )

    return render_template("writer_form.html", profiles=profiles, output=output)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
