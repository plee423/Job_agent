from __future__ import annotations


def generate_message(
    message_type: str,
    profile: dict,
    role: str,
    company: str,
    context: str,
    guidelines: str,
) -> str:
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
