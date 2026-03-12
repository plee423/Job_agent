from matcher import build_profile, score_posting


def test_build_profile_merges_manual_keywords_first():
    resume = "Python engineer with Django and AWS experience"
    profile = build_profile(resume, "https://linkedin.com/in/example", ["backend", "python"])
    assert profile.keywords[0] == "backend"
    assert "python" in profile.keywords


def test_score_posting_increases_with_keyword_overlap():
    resume = "Python backend engineer with aws"
    profile = build_profile(resume, "https://linkedin.com/in/example", ["fastapi"])

    low = score_posting("Marketing Intern", "social media campaigns", profile)
    high = score_posting("Senior Python Backend Engineer", "Build APIs with FastAPI and AWS", profile)

    assert high > low
    assert high > 0
