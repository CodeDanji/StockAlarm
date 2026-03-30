from app.workers.scheduler import build_jobs


def test_scheduler_builds_required_jobs() -> None:
    jobs = build_jobs()
    names = {job["name"] for job in jobs}
    assert "ingest-15m-market-hours" in names
    assert "evaluate-15m-market-hours" in names
    assert "ingest-1h-off-hours" in names
    assert "digest-morning" in names
