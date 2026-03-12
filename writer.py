from __future__ import annotations

from pathlib import Path

ACTING_PRINCIPLES = """# Agent Acting Principles

- Be truthful and avoid inventing facts about a candidate.
- Prefer concise, impact-focused writing with measurable outcomes.
- Keep tone professional, respectful, and specific to the role/company.
- Avoid scraping protected pages without permission or compliant APIs.
- Preserve user writing guidelines unless they conflict with safety/legal constraints.
"""


def ensure_acting_principles(path: Path) -> None:
    if not path.exists():
        path.write_text(ACTING_PRINCIPLES, encoding="utf-8")


def save_guidelines(path: Path, markdown: str) -> None:
    path.write_text(markdown.strip() + "\n", encoding="utf-8")


def load_guidelines(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def generate_message(
    message_type: str,
    profile: dict,
    role: str,
    company: str,
    context: str,
    guidelines: str,
) -> str:
    principles_path = Path("data") / "AGENT_ACTING_PRINCIPLES.md"
    principles_path.parent.mkdir(exist_ok=True)
    ensure_acting_principles(principles_path)

    opening = {
        "cover_letter": f"Dear Hiring Team at {company or '[Company]'},",
        "cold_linkedin": f"Hi, I came across your work at {company or '[Company]'} and wanted to connect.",
        "linkedin_inmail": f"Hi there — I'm reaching out regarding potential {role or '[Role]'} opportunities.",
        "slack_message": f"Hey team, sharing my interest in {role or '[Role]'} at {company or '[Company]'}.",
    }.get(message_type, "Hello,")

    return "\n".join(
        [
            opening,
            "",
            f"I am interested in the {role or '[Role]'} role and believe my background aligns well.",
            f"LinkedIn: {profile.get('linkedin_url', '')}",
            "",
            "Relevant experience highlights:",
            profile.get("extra_experience", "(add experience stories in your profile)"),
            "",
            "Additional context:",
            context or "(none provided)",
            "",
            "Writing guidelines to preserve:",
            guidelines or "(none provided)",
            "",
            "Best regards,",
            profile.get("name", "Candidate"),
        ]
    )
