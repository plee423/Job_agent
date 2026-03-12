from storage import Storage


def test_profile_create_and_fetch(tmp_path):
    db = tmp_path / "test.db"
    store = Storage(str(db))
    try:
        pid = store.create_or_update_profile(
            name="Jane",
            linkedin_url="https://linkedin.com/in/jane",
            resume_text="Python engineer",
            extra_experience="Shipped SaaS",
        )
        profile = store.get_profile(pid)
        assert profile is not None
        assert profile["name"] == "Jane"
        all_profiles = store.list_profiles()
        assert len(all_profiles) == 1
    finally:
        store.close()
