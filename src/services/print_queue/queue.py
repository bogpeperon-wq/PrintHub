"""
Print Queue Service - manages print job queue and execution.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from src.domain.models.base import Order, PrintJob, PrintAgent
from src.domain.enums.order_enums import OrderStatus, PrintJobStatus, PrinterStatus


class PrintQueueService:
    """Service for managing the print queue."""
    
    def __init__(self, session: AsyncSession, redis_client: redis.Redis):
        self.session = session
        self.redis = redis_client
        self.queue_key = "print_queue"
        self.lock_prefix = "lock:print_job:"
    
    async def add_to_queue(self, print_job: PrintJob) -> None:
        """Add a print job to the queue."""
        print_job.status = PrintJobStatus.QUEUED
        await self.session.flush()
        
        # Add to Redis queue
        await self.redis.lpush(self.queue_key, str(print_job.id))
    
    async def get_next_job(self) -> Optional[PrintJob]:
        """Get next job from queue."""
        result = await self.redis.rpop(self.queue_key)
        if not result:
            return None
        
        job_id = int(result)
        stmt = select(PrintJob).where(PrintJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def acquire_job_lock(self, job_id: int, ttl: int = 60) -> bool:
        """Acquire lock on a job to prevent duplicate processing."""
        lock_key = f"{self.lock_prefix}{job_id}"
        return await self.redis.set(lock_key, "1", nx=True, ex=ttl)
    
    async def release_job_lock(self, job_id: int) -> None:
        """Release lock on a job."""
        lock_key = f"{self.lock_prefix}{job_id}"
        await self.redis.delete(lock_key)
    
    async def create_print_job(
        self,
        order: Order,
        pdf_path: str,
        pages: int,
        copies: int,
        color: bool,
    ) -> PrintJob:
        """Create a new print job for an order."""
        print_job = PrintJob(
            order_id=order.id,
            agent_id=None,  # Will be assigned when agent picks up job
            pdf_path=pdf_path,
            total_pages=pages,
            copies=copies,
            is_color=color,
            status=PrintJobStatus.PREPARING,
            started_from_page=1,
        )
        self.session.add(print_job)
        await self.session.flush()
        return print_job
    
    async def assign_job_to_agent(
        self, 
        job_id: int, 
        agent_id: int
    ) -> bool:
        """Assign a job to a specific print agent."""
        stmt = select(PrintJob).where(PrintJob.id == job_id)
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job or job.status != PrintJobStatus.QUEUED:
            return False
        
        job.agent_id = agent_id
        job.status = PrintJobStatus.PRINTING
        await self.session.flush()
        return True
    
    async def complete_job(self, job_id: int) -> None:
        """Mark a job as completed."""
        stmt = select(PrintJob).where(PrintJob.id == job_id)
        result = await self.session.execute(stmt)
        job = result.scalar_one()
        
        job.status = PrintJobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        await self.session.flush()
    
    async def fail_job(
        self, 
        job_id: int, 
        error_reason: str,
        needs_admin: bool = False,
    ) -> None:
        """Mark a job as failed."""
        stmt = select(PrintJob).where(PrintJob.id == job_id)
        result = await self.session.execute(stmt)
        job = result.scalar_one()
        
        if needs_admin:
            job.status = PrintJobStatus.NEEDS_ADMIN_ACTION
        else:
            job.status = PrintJobStatus.FAILED
        
        job.error_reason = error_reason
        await self.session.flush()
    
    async def pause_job(self, job_id: int, reason: str) -> None:
        """Pause a print job."""
        stmt = select(PrintJob).where(PrintJob.id == job_id)
        result = await self.session.execute(stmt)
        job = result.scalar_one()
        
        job.status = PrintJobStatus.PAUSED
        job.error_reason = reason
        await self.session.flush()
    
    async def resume_job(
        self, 
        job_id: int, 
        from_page: Optional[int] = None,
    ) -> None:
        """Resume a paused job."""
        stmt = select(PrintJob).where(PrintJob.id == job_id)
        result = await self.session.execute(stmt)
        job = result.scalar_one()
        
        job.status = PrintJobStatus.QUEUED
        job.error_reason = None
        if from_page:
            job.started_from_page = from_page
        
        # Re-add to queue
        await self.redis.lpush(self.queue_key, str(job.id))
        await self.session.flush()
    
    async def get_queue_status(self) -> dict:
        """Get current queue status."""
        queue_length = await self.redis.llen(self.queue_key)
        
        stmt = select(PrintJob).where(
            PrintJob.status.in_([
                PrintJobStatus.QUEUED,
                PrintJobStatus.PRINTING,
                PrintJobStatus.PREPARING,
            ])
        )
        result = await self.session.execute(stmt)
        active_jobs = result.scalars().all()
        
        return {
            "queue_length": queue_length,
            "active_jobs": [
                {
                    "id": j.id,
                    "order_id": j.order_id,
                    "status": j.status.value,
                    "pages": j.total_pages,
                    "copies": j.copies,
                }
                for j in active_jobs
            ],
        }
    
    async def cancel_job(self, job_id: int) -> bool:
        """Cancel a print job (only if not yet printing)."""
        stmt = select(PrintJob).where(PrintJob.id == job_id)
        result = await self.session.execute(stmt)
        job = result.scalar_one()
        
        if job.status in [PrintJobStatus.PRINTING, PrintJobStatus.COMPLETED]:
            return False  # Cannot cancel already printing jobs
        
        job.status = PrintJobStatus.CANCELLED
        await self.session.flush()
        
        # Remove from queue if present
        await self.redis.lrem(self.queue_key, 0, str(job_id))
        return True
