"""
Job queue service for managing async job processing.
"""

import asyncio
import logging
from typing import Dict, Set, Optional, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from app.models.job_models import Job, JobStatus, JobEvent, WorkerStatus
from app.services.simple_db import list_jobs, update_job_status
from app.core.config import settings

logger = logging.getLogger(__name__)


class JobQueue:
    """Asynchronous job queue service"""
    
    def __init__(self):
        self.is_running = False
        self.workers: Dict[str, asyncio.Task] = {}
        self.active_jobs: Set[str] = set()
        self.job_subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Start the job queue service"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting job queue service...")
        
        # Start worker tasks
        for i in range(settings.max_concurrent_jobs):
            worker_id = f"worker-{i}"
            worker_task = asyncio.create_task(self._worker_loop(worker_id))
            self.workers[worker_id] = worker_task
        
        logger.info(f"Job queue started with {len(self.workers)} workers")
    
    async def stop(self):
        """Stop the job queue service"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping job queue service...")
        
        # Cancel all worker tasks
        for worker_id, task in self.workers.items():
            logger.info(f"Stopping worker {worker_id}")
            task.cancel()
        
        # Wait for workers to complete
        if self.workers:
            await asyncio.gather(*self.workers.values(), return_exceptions=True)
        
        self.workers.clear()
        self.active_jobs.clear()
        logger.info("Job queue stopped")
    
    async def enqueue_job(self, job_id: str):
        """Add a job to the processing queue"""
        async with self._lock:
            # Update job status to queued
            success = update_job_status(job_id, JobStatus.QUEUED.value)
            if not success:
                logger.error(f"Job {job_id} not found")
                return
            
            logger.info(f"Job {job_id} enqueued")
    
    async def get_next_job(self) -> Optional[Job]:
        """Get the next job from the queue"""
        from app.services.simple_db import get_job
        
        # Get jobs from database and find a queued job
        jobs = list_jobs(limit=100)  # Get recent jobs
        queued_jobs = [job for job in jobs if job.status == JobStatus.QUEUED.value]
        
        if queued_jobs:
            # Sort by priority (highest first) then by created_at (oldest first)
            queued_jobs.sort(key=lambda j: (-j.priority, j.created_at))
            job = queued_jobs[0]
            
            # Update job status to processing
            success = update_job_status(job.id, JobStatus.PROCESSING.value, 
                                      started_at=datetime.utcnow())
            if success:
                async with self._lock:
                    self.active_jobs.add(job.id)
                
                logger.info(f"Job {job.id} assigned for processing")
                return job
        
        return None
    
    async def _worker_loop(self, worker_id: str):
        """Worker loop for processing jobs"""
        logger.info(f"Worker {worker_id} started")
        
        # Update worker status
        await self._update_worker_status(worker_id, "idle")
        
        try:
            while self.is_running:
                job = await self.get_next_job()
                
                if job:
                    await self._update_worker_status(worker_id, "processing", job.id)
                    await self._process_job(worker_id, job)
                    await self._update_worker_status(worker_id, "idle")
                else:
                    # No jobs available, wait a bit
                    await asyncio.sleep(settings.queue_poll_interval)
                    await self._update_worker_status(worker_id, "waiting")
        
        except asyncio.CancelledError:
            logger.info(f"Worker {worker_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
        finally:
            await self._update_worker_status(worker_id, "stopped")
            logger.info(f"Worker {worker_id} stopped")
    
    async def _process_job(self, worker_id: str, job: Job):
        """Process a single job"""
        logger.info(f"Worker {worker_id} processing job {job.id}")
        
        try:
            # Update worker assignment
            job.worker_id = worker_id
            
            # Simulate job processing with progress updates
            stages = [
                ("initializing", 10, "Initializing job..."),
                ("downloading", 30, "Downloading video..."),
                ("extracting_audio", 50, "Extracting audio..."),
                ("transcribing", 70, "Transcribing audio..."),
                ("analyzing", 85, "Analyzing content..."),
                ("finalizing", 95, "Finalizing results..."),
                ("completed", 100, "Job completed successfully!")
            ]
            
            for stage, progress, message in stages:
                if not self.is_running:
                    break
                
                # Add progress event
                await self._add_job_event(
                    job.id, 
                    "progress", 
                    message, 
                    progress=progress,
                    data={"stage": stage}
                )
                
                # Simulate processing time
                await asyncio.sleep(2)
            
            # Mark job as completed
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.completed_at = datetime.utcnow()
            
            # Add sample results
            job.video_title = f"Sample Video - {job.id[:8]}"
            job.transcript = "This is a sample transcript."
            job.analysis_results = {"sentiment": "positive", "topics": ["technology", "tutorial"]}
            job.generated_clips = [
                {"start": 0, "end": 30, "title": "Introduction"},
                {"start": 30, "end": 60, "title": "Main Content"}
            ]
            
        except Exception as e:
            logger.error(f"Job {job.id} processing failed: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            
            await self._add_job_event(job.id, "error", f"Job failed: {str(e)}")
        
        finally:
            # Save job to database
            session = next(get_session())
            try:
                session.add(job)
                session.commit()
            finally:
                session.close()
            
            # Remove from active jobs
            async with self._lock:
                self.active_jobs.discard(job.id)
            
            # Notify subscribers
            await self._notify_subscribers(job.id)
    
    async def _update_worker_status(self, worker_id: str, status: str, job_id: str = None):
        """Update worker status in database"""
        try:
            session = next(get_session())
            # Find or create worker status
            statement = select(WorkerStatus).where(WorkerStatus.worker_id == worker_id)
            worker = session.exec(statement).first()
            
            if not worker:
                worker = WorkerStatus(worker_id=worker_id)
            
            worker.status = status
            worker.current_job_id = job_id
            worker.last_heartbeat = datetime.utcnow()
            
            if status == "idle" and job_id:
                worker.jobs_processed += 1
            
            session.add(worker)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Failed to update worker status: {e}")
    
    async def _add_job_event(self, job_id: str, event_type: str, message: str, 
                           progress: float = None, stage: str = None, data: dict = None):
        """Add a job event to the database"""
        try:
            session = next(get_session())
            event = JobEvent(
                job_id=job_id,
                event_type=event_type,
                stage=stage,
                message=message,
                progress=progress,
                data=data
            )
            session.add(event)
            session.commit()
            session.close()
            
            # Notify subscribers
            await self._notify_subscribers(job_id)
        except Exception as e:
            logger.error(f"Failed to add job event: {e}")
    
    def subscribe_to_job(self, job_id: str) -> asyncio.Queue:
        """Subscribe to job updates"""
        if job_id not in self.job_subscribers:
            self.job_subscribers[job_id] = set()
        
        queue = asyncio.Queue()
        self.job_subscribers[job_id].add(queue)
        return queue
    
    def unsubscribe_from_job(self, job_id: str, queue: asyncio.Queue):
        """Unsubscribe from job updates"""
        if job_id in self.job_subscribers:
            self.job_subscribers[job_id].discard(queue)
            if not self.job_subscribers[job_id]:
                del self.job_subscribers[job_id]
    
    async def _notify_subscribers(self, job_id: str):
        """Notify all subscribers of job updates"""
        if job_id not in self.job_subscribers:
            return
        
        # Get updated job
        with get_session() as session:
            job = session.get(Job, job_id)
            if not job:
                return
        
        # Notify all subscribers
        for queue in self.job_subscribers[job_id].copy():
            try:
                await queue.put({
                    "type": "job_update",
                    "job_id": job_id,
                    "status": job.status,
                    "progress": job.progress,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to notify subscriber: {e}")
    
    async def cancel_job(self, job_id: str, reason: str = None) -> bool:
        """Cancel a job"""
        async with self._lock:
            session = next(get_session())
            try:
                job = session.get(Job, job_id)
                if not job:
                    return False
                
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    return False
                
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow()
                if reason:
                    job.error_message = reason
                
                session.add(job)
                session.commit()
                
                # Remove from active jobs
                self.active_jobs.discard(job_id)
                
                logger.info(f"Job {job_id} cancelled: {reason}")
                return True
            finally:
                session.close()
    
    async def get_queue_status(self) -> Dict:
        """Get current queue status"""
        session = next(get_session())
        try:
            total = len(session.exec(select(Job)).all())
            pending = len(session.exec(select(Job).where(Job.status == JobStatus.QUEUED)).all())
            processing = len(session.exec(select(Job).where(Job.status == JobStatus.PROCESSING)).all())
            completed = len(session.exec(select(Job).where(Job.status == JobStatus.COMPLETED)).all())
            failed = len(session.exec(select(Job).where(Job.status == JobStatus.FAILED)).all())
            cancelled = len(session.exec(select(Job).where(Job.status == JobStatus.CANCELLED)).all())
        finally:
            session.close()
        
        return {
            "is_running": self.is_running,
            "total_jobs": total,
            "pending_jobs": pending,
            "processing_jobs": processing,
            "completed_jobs": completed,
            "failed_jobs": failed,
            "cancelled_jobs": cancelled,
            "active_workers": len([w for w in self.workers.values() if not w.done()]),
            "queue_size": len(self.active_jobs)
        }


# Global job queue instance
job_queue = JobQueue()