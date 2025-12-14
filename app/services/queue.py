"""Async job queue service.

This is an in-process async worker queue suitable for development.
For production, the same interface can be backed by Redis/SQS + container workers.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.core.config import settings
from app.db.database import engine
from app.models.job_models import Job, JobEvent, JobStatus, ProcessingStage, WorkerStatus
from app.services.media_pipeline import MediaProcessingPipeline
from app.services.simple_db import update_job

logger = logging.getLogger(__name__)


class JobQueue:
    """Asynchronous job queue service."""

    def __init__(self) -> None:
        self.is_running: bool = False
        self.workers: dict[str, asyncio.Task[None]] = {}
        self.active_jobs: set[str] = set()
        self.job_subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}
        self._lock = asyncio.Lock()
        self.pipeline: MediaProcessingPipeline | None = None

    async def start(self) -> None:
        if self.is_running:
            return

        self.is_running = True
        logger.info("Starting job queue service...")

        # Initialize media pipeline
        self.pipeline = MediaProcessingPipeline(output_dir=settings.output_dir)

        for i in range(settings.max_concurrent_jobs):
            worker_id = f"worker-{i}"
            self.workers[worker_id] = asyncio.create_task(self._worker_loop(worker_id))

    async def stop(self) -> None:
        if not self.is_running:
            return

        self.is_running = False
        for task in self.workers.values():
            task.cancel()

        if self.workers:
            await asyncio.gather(*self.workers.values(), return_exceptions=True)

        self.workers.clear()
        self.active_jobs.clear()

    async def enqueue_job(self, job_id: str) -> None:
        """Mark a job as queued (workers poll the DB for queued jobs)."""

        update_job(job_id, status=JobStatus.QUEUED, progress=0.0)
        await self._notify_subscribers(job_id)

    async def get_next_job(self, worker_id: str) -> Job | None:
        """Pick the next queued job by (priority desc, created_at asc)."""

        with Session(engine) as session:
            statement = (
                select(Job)
                .where(Job.status == JobStatus.QUEUED)
                .order_by(Job.priority.desc(), Job.created_at.asc())
                .limit(1)
            )
            job = session.exec(statement).first()
            if not job:
                return None

            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            job.worker_id = worker_id
            job.updated_at = datetime.utcnow()
            session.add(job)
            session.commit()
            session.refresh(job)

        async with self._lock:
            self.active_jobs.add(job.id)

        await self._notify_subscribers(job.id)
        return job

    async def _worker_loop(self, worker_id: str) -> None:
        logger.info("Worker %s started", worker_id)
        await self._update_worker_status(worker_id, "idle")

        try:
            while self.is_running:
                job = await self.get_next_job(worker_id)
                if not job:
                    await asyncio.sleep(settings.queue_poll_interval)
                    continue

                await self._update_worker_status(worker_id, "processing", job.id)
                await self._process_job(worker_id, job.id)
                await self._update_worker_status(worker_id, "idle")

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Worker %s failed", worker_id)
        finally:
            await self._update_worker_status(worker_id, "stopped")

    async def _process_job(self, worker_id: str, job_id: str) -> None:
        """Execute the real media processing pipeline.

        This runs the complete video processing workflow including:
        - URL validation and metadata extraction
        - Video download
        - Audio extraction
        - Transcription (Whisper)
        - NLP analysis
        - Segment generation
        - Video encoding and cropping
        """

        async def progress_callback(
            stage: ProcessingStage, progress: float, message: str
        ) -> None:
            """Callback for pipeline progress updates."""
            with Session(engine) as session:
                job = session.get(Job, job_id)
                if not job:
                    return

                job.progress = progress
                job.updated_at = datetime.utcnow()
                session.add(job)
                session.commit()

                session.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="progress",
                        stage=stage.value,
                        message=message,
                        progress=progress,
                        data={"stage": stage.value, "worker_id": worker_id},
                    )
                )
                session.commit()

            await self._notify_subscribers(job_id)

        try:
            with Session(engine) as session:
                job = session.get(Job, job_id)
                if not job:
                    return
                if job.status == JobStatus.CANCELLED:
                    return

            if not self.pipeline:
                raise RuntimeError("Media pipeline not initialized")

            # Execute pipeline
            result = await self.pipeline.process_job(
                job_id=job_id,
                youtube_url=job.youtube_url,
                job_type=job.job_type.value,
                options=job.options or {},
                progress_callback=progress_callback,
            )

            # Update job with results
            with Session(engine) as session:
                job = session.get(Job, job_id)
                if job:
                    job.video_title = result.get("video_title")
                    job.video_duration = result.get("video_duration")
                    job.video_uploader = result.get("uploader")
                    job.transcript = result.get("transcript")
                    job.transcript_segments = result.get("transcript_segments")
                    job.generated_clips = result.get("generated_clips")
                    job.output_files = result.get("output_files")
                    job.progress = 100.0
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.utcnow()
                    job.updated_at = datetime.utcnow()
                    session.add(job)
                    session.commit()

                    session.add(
                        JobEvent(
                            job_id=job_id,
                            event_type="completed",
                            stage=ProcessingStage.COMPLETED.value,
                            message="Processing complete!",
                            progress=100.0,
                            data={
                                "clips_generated": result.get("clips_generated"),
                                "worker_id": worker_id,
                            },
                        )
                    )
                    session.commit()

        except Exception as e:
            logger.exception("Job %s failed: %s", job_id, str(e))

            with Session(engine) as session:
                job = session.get(Job, job_id)
                current_progress = job.progress if job else 0.0

            update_job(
                job_id,
                status=JobStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.utcnow(),
            )

            with Session(engine) as session:
                session.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="failed",
                        stage=ProcessingStage.FINALIZING.value,
                        message=f"Job failed: {str(e)}",
                        progress=current_progress,
                        data={"error": str(e), "worker_id": worker_id},
                    )
                )
                session.commit()

        finally:
            async with self._lock:
                self.active_jobs.discard(job_id)
            await self._notify_subscribers(job_id)

    async def _update_worker_status(
        self, worker_id: str, status: str, job_id: str | None = None
    ) -> None:
        try:
            with Session(engine) as session:
                statement = select(WorkerStatus).where(WorkerStatus.worker_id == worker_id)
                worker = session.exec(statement).first() or WorkerStatus(worker_id=worker_id)

                worker.status = status
                worker.current_job_id = job_id
                worker.last_heartbeat = datetime.utcnow()

                session.add(worker)
                session.commit()
        except Exception:
            logger.exception("Failed to update worker status")

    def subscribe_to_job(self, job_id: str) -> asyncio.Queue[dict[str, Any]]:
        self.job_subscribers.setdefault(job_id, set())
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.job_subscribers[job_id].add(queue)
        return queue

    def unsubscribe_from_job(self, job_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subscribers = self.job_subscribers.get(job_id)
        if not subscribers:
            return

        subscribers.discard(queue)
        if not subscribers:
            del self.job_subscribers[job_id]

    async def _notify_subscribers(self, job_id: str) -> None:
        subscribers = self.job_subscribers.get(job_id)
        if not subscribers:
            return

        with Session(engine) as session:
            job = session.get(Job, job_id)
            if not job:
                return

            message = {
                "type": "job_update",
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        for queue in subscribers.copy():
            try:
                await queue.put(message)
            except Exception:
                subscribers.discard(queue)

    async def cancel_job(self, job_id: str, reason: str | None = None) -> bool:
        async with self._lock:
            with Session(engine) as session:
                job = session.get(Job, job_id)
                if not job:
                    return False

                if job.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
                    return False

                job.status = JobStatus.CANCELLED
                job.error_message = reason
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                session.add(job)
                session.commit()

            self.active_jobs.discard(job_id)

        await self._notify_subscribers(job_id)
        return True

    async def get_queue_status(self) -> dict[str, Any]:
        with Session(engine) as session:
            total_jobs = session.exec(select(Job)).all()
            by_status = {status: 0 for status in JobStatus}
            for job in total_jobs:
                by_status[job.status] += 1

        return {
            "is_running": self.is_running,
            "total_jobs": len(total_jobs),
            "pending_jobs": by_status[JobStatus.PENDING],
            "processing_jobs": by_status[JobStatus.PROCESSING],
            "completed_jobs": by_status[JobStatus.COMPLETED],
            "failed_jobs": by_status[JobStatus.FAILED],
            "cancelled_jobs": by_status[JobStatus.CANCELLED],
            "active_workers": len([t for t in self.workers.values() if not t.done()]),
            "queue_size": by_status[JobStatus.QUEUED],
        }


job_queue = JobQueue()
