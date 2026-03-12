from pathlib import Path

from writer import ensure_acting_principles, generate_message, save_guidelines, load_guidelines


def test_guideline_roundtrip(tmp_path: Path):
    path = tmp_path / "g.md"
    save_guidelines(path, "# Style\n- concise")
    assert "concise" in load_guidelines(path)


def test_generate_message_creates_principles_file(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    output = generate_message(
        message_type="cover_letter",
        profile={"name": "Alex", "linkedin_url": "https://linkedin.com/in/alex", "extra_experience": "Built APIs"},
        role="Backend Engineer",
        company="Acme",
        context="Prefer remote",
        guidelines="Use short paragraphs",
    )
    assert "Backend Engineer" in output
    assert (tmp_path / "data" / "AGENT_ACTING_PRINCIPLES.md").exists()


def test_ensure_acting_principles(tmp_path: Path):
    path = tmp_path / "AGENT_ACTING_PRINCIPLES.md"
    ensure_acting_principles(path)
    assert "Agent Acting Principles" in path.read_text(encoding="utf-8")
