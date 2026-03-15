from __future__ import annotations

import json
import os


_SYSTEM_PROMPT = """You are a career analyst. Given a candidate's resume text, extract structured information
for use in a job search. Return ONLY valid JSON with this exact structure — no markdown, no explanation:

{
  "target_roles": ["list of 3-5 specific job titles this person is best suited for"],
  "skills": ["list of up to 20 technical and professional skills found in the resume"],
  "seniority": "one of: junior, mid, senior, staff, principal, lead, manager, director",
  "industries": ["list of 1-3 industries this person has worked in"],
  "search_keywords": ["list of 15-20 keywords optimized for job board searches based on this resume"]
}"""


def analyze_resume(resume_text: str) -> dict:
    """Send resume to Claude and return structured profile data.

    Returns an empty dict if ANTHROPIC_API_KEY is not set or the call fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Resume:\n\n{resume_text}"}
            ],
        )
        raw = message.content[0].text.strip()
        return json.loads(raw)
    except Exception:
        return {}


def llm_profile_to_json(profile_data: dict) -> str:
    return json.dumps(profile_data)


def llm_profile_from_json(raw: str) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}
