from sources import JobPosting
from storage import Storage


def test_draft_upsert_flow(tmp_path):
    db = tmp_path / "test.db"
    store = Storage(str(db))
    try:
        profile_id = store.create_or_update_profile(
            name="Jane",
            linkedin_url="https://linkedin.com/in/jane",
            resume_text="Python engineer",
            extra_experience="Built APIs",
        )

        added = store.add_if_new(
            JobPosting(
                source="test",
                title="Backend Engineer",
                company="Acme",
                location="Remote",
                url="https://example.com/job/1",
                published_at="2026-01-01",
                snippet="snippet",
                score=0.8,
            )
        )
        assert added is True
        job_id = store.get_job_id_by_url("https://example.com/job/1")
        assert job_id is not None

        first_id = store.create_or_update_draft(profile_id, job_id, "cover_letter", "first", "generated")
        second_id = store.create_or_update_draft(profile_id, job_id, "cover_letter", "updated", "generated")

        assert first_id == second_id
        drafts = store.list_drafts(profile_id=profile_id)
        assert len(drafts) == 1
        assert drafts[0]["message_type"] == "cover_letter"
    finally:
        store.close()
