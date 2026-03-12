from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
from typing import Iterable

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}")
STOPWORDS = {
    "and", "the", "for", "with", "that", "from", "your", "have", "you", "are", "our",
    "job", "work", "will", "this", "about", "their", "they", "into", "been", "using",
    "years", "year", "experience", "skills", "responsible", "role", "team", "build",
    "develop", "developed", "including", "strong", "ability", "remote", "hybrid", "onsite"
}

TITLE_HINT_WORDS = {
    "engineer", "developer", "scientist", "manager", "architect", "analyst", "designer",
    "lead", "principal", "specialist", "consultant", "administrator"
}


@dataclass
class SearchProfile:
    linkedin_url: str
    keywords: list[str]
    title_hints: list[str]
    location: str | None = None


def read_resume_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_keywords(text: str, limit: int = 25) -> list[str]:
    tokens = [t.lower() for t in TOKEN_RE.findall(text)]
    filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    ranked = Counter(filtered).most_common(limit)
    return [t for t, _ in ranked]


def extract_title_hints(text: str) -> list[str]:
    tokens = [t.lower() for t in TOKEN_RE.findall(text)]
    hints = {t for t in tokens if t in TITLE_HINT_WORDS}
    return sorted(hints)


def build_profile(
    resume_text: str,
    linkedin_url: str,
    user_keywords: Iterable[str] | None = None,
    location: str | None = None,
) -> SearchProfile:
    auto_keywords = extract_keywords(resume_text)
    manual = [k.strip().lower() for k in (user_keywords or []) if k.strip()]
    merged = list(dict.fromkeys(manual + auto_keywords))
    title_hints = extract_title_hints(resume_text)
    return SearchProfile(
        linkedin_url=linkedin_url,
        keywords=merged[:35],
        title_hints=title_hints,
        location=location,
    )


def score_posting(title: str, description: str, profile: SearchProfile) -> float:
    haystack = f"{title} {description}".lower()
    if not haystack.strip():
        return 0.0

    keyword_hits = sum(1 for k in profile.keywords if k in haystack)
    title_hits = sum(1 for t in profile.title_hints if t in title.lower())

    # Emphasize title alignment but still reward broader keyword overlap.
    kw_score = keyword_hits / max(1, min(len(profile.keywords), 20))
    title_score = title_hits / max(1, len(profile.title_hints))
    return round((0.65 * kw_score + 0.35 * title_score), 4)
