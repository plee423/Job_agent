from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Lock, Thread
import time

from agent import run_cycle
from storage import Storage
from writer import generate_message, load_guidelines


@dataclass
class ServiceConfig:
    db_path: str = "job_agent.db"
    data_dir: Path = Path("data")
    poll_interval_seconds: int = 1800
    min_score: float = 0.15


class TwoAgentService:
    """Coordinates two background agents:

    1) Discovery agent: periodically searches jobs for each profile.
    2) Writer agent: generates default cover letters for newly discovered jobs.
    """

    def __init__(self, config: ServiceConfig | None = None) -> None:
        self.config = config or ServiceConfig()
        self._stop = Event()
        self._discovery_thread: Thread | None = None
        self._writer_thread: Thread | None = None
        self._write_queue: Queue[tuple[int, int]] = Queue()  # (profile_id, job_id)
        self._state_lock = Lock()
        self._status = "stopped"

    def start(self) -> None:
        if self.is_running:
            return
        self._stop.clear()
        with self._state_lock:
            self._status = "running"
        self._discovery_thread = Thread(target=self._discovery_loop, name="discovery-agent", daemon=True)
        self._writer_thread = Thread(target=self._writer_loop, name="writer-agent", daemon=True)
        self._discovery_thread.start()
        self._writer_thread.start()

    def stop(self) -> None:
        if not self.is_running:
            return
        self._stop.set()
        if self._discovery_thread:
            self._discovery_thread.join(timeout=3)
        if self._writer_thread:
            self._writer_thread.join(timeout=3)
        with self._state_lock:
            self._status = "stopped"

    @property
    def is_running(self) -> bool:
        return self._discovery_thread is not None and self._discovery_thread.is_alive()

    def status(self) -> dict:
        with self._state_lock:
            status = self._status
        return {
            "status": status,
            "queue_depth": self._write_queue.qsize(),
            "poll_interval_seconds": self.config.poll_interval_seconds,
            "min_score": self.config.min_score,
        }

    def _discovery_loop(self) -> None:
        while not self._stop.is_set():
            store = Storage(self.config.db_path)
            try:
                profiles = store.list_profiles()
                for profile in profiles:
                    run_id = store.begin_run()
                    try:
                        discovered, inserted = run_cycle(
                            store=store,
                            resume_text=profile["resume_text"],
                            linkedin_url=profile["linkedin_url"],
                            keywords=[profile.get("extra_experience", "")],
                            location=None,
                            min_score=self.config.min_score,
                            on_new_job=lambda job, pid=profile["id"]: self._enqueue_for_writing(pid, job.url),
                        )
                        store.end_run(run_id, discovered, inserted, "")
                    except Exception as exc:
                        store.end_run(run_id, 0, 0, str(exc))
            finally:
                store.close()
            self._stop.wait(max(30, self.config.poll_interval_seconds))

    def _enqueue_for_writing(self, profile_id: int, url: str) -> None:
        store = Storage(self.config.db_path)
        try:
            job_id = store.get_job_id_by_url(url)
            if job_id is not None:
                self._write_queue.put((profile_id, job_id))
        finally:
            store.close()

    def _writer_loop(self) -> None:
        while not self._stop.is_set():
            try:
                profile_id, job_id = self._write_queue.get(timeout=1)
            except Empty:
                continue

            store = Storage(self.config.db_path)
            try:
                profile = store.get_profile(profile_id)
                job = store.get_job(job_id)
                if not profile or not job:
                    continue
                guidelines = load_guidelines(self.config.data_dir / f"profile_{profile_id}_guidelines.md")
                content = generate_message(
                    message_type="cover_letter",
                    profile=profile,
                    role=job.get("title", ""),
                    company=job.get("company", ""),
                    context=f"Auto-generated for {job.get('url', '')}",
                    guidelines=guidelines,
                )
                store.create_or_update_draft(
                    profile_id=profile_id,
                    job_id=job_id,
                    message_type="cover_letter",
                    content=content,
                    status="generated",
                )
            finally:
                store.close()
                self._write_queue.task_done()
