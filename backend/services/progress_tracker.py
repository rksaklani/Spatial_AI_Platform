"""
Training Progress Tracker Service

Tracks training progress for Gaussian Splatting jobs, calculates time estimates,
and manages progress persistence to MongoDB.
"""

import time
from collections import deque
from datetime import datetime
from typing import Optional, Deque
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class TrainingProgressTracker:
    """
    Tracks training progress and calculates estimates.
    
    Monitors iteration progress, calculates rolling average iteration speed,
    and determines when to broadcast progress updates via WebSocket.
    """
    
    def __init__(
        self,
        scene_id: str,
        job_id: str,
        total_iterations: int,
        mongodb_url: str,
        database_name: str
    ):
        """
        Initialize progress tracker.
        
        Args:
            scene_id: Scene UUID
            job_id: Processing job UUID
            total_iterations: Total number of training iterations
            mongodb_url: MongoDB connection URL
            database_name: Database name
        """
        self.scene_id = scene_id
        self.job_id = job_id
        self.total_iterations = total_iterations
        self.current_iteration = 0
        
        # Rolling window of iteration times (last 500)
        self.iteration_times: Deque[float] = deque(maxlen=500)
        
        # Timing
        self.started_at: Optional[datetime] = None
        self.last_update_time: Optional[float] = None
        self.last_persist_time: float = 0.0
        self.last_broadcast_percent: float = 0.0
        
        # Database connection
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        
        logger.info(
            f"Initialized TrainingProgressTracker for scene {scene_id}, "
            f"job {job_id}, {total_iterations} iterations"
        )
    
    async def update_iteration(self, iteration: int) -> None:
        """
        Update current iteration and record timing.
        
        Args:
            iteration: Current iteration number
        """
        current_time = time.time()
        
        # Initialize timing on first iteration
        if self.started_at is None:
            self.started_at = datetime.utcnow()
            self.last_update_time = current_time
        
        # Record iteration time
        if self.last_update_time is not None:
            iteration_time = current_time - self.last_update_time
            self.iteration_times.append(iteration_time)
        
        self.current_iteration = iteration
        self.last_update_time = current_time
        
        # Persist to database at most once per second
        if current_time - self.last_persist_time >= 1.0:
            await self.persist_progress()
            self.last_persist_time = current_time
    
    def calculate_progress_percent(self) -> float:
        """
        Calculate progress percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        if self.total_iterations == 0:
            return 0.0
        
        progress = (self.current_iteration / self.total_iterations) * 100
        return min(100.0, max(0.0, progress))
    
    def calculate_estimated_seconds_remaining(self) -> Optional[float]:
        """
        Calculate estimated time remaining based on rolling average.
        
        Returns:
            Estimated seconds remaining, or None if insufficient data
        """
        # Need at least 10 iterations for reasonable estimate
        if not self.iteration_times or len(self.iteration_times) < 10:
            return None
        
        # Calculate average time per iteration
        avg_time_per_iteration = sum(self.iteration_times) / len(self.iteration_times)
        
        if avg_time_per_iteration <= 0:
            return None
        
        # Calculate remaining iterations
        remaining_iterations = self.total_iterations - self.current_iteration
        
        # Estimate remaining time
        estimate = remaining_iterations * avg_time_per_iteration
        
        # Ensure non-negative
        return max(0.0, estimate)
    
    def calculate_average_iterations_per_second(self) -> Optional[float]:
        """
        Calculate average iterations per second.
        
        Returns:
            Average iterations per second, or None if insufficient data
        """
        if not self.iteration_times or len(self.iteration_times) < 10:
            return None
        
        avg_time_per_iteration = sum(self.iteration_times) / len(self.iteration_times)
        
        if avg_time_per_iteration <= 0:
            return None
        
        return 1.0 / avg_time_per_iteration
    
    def should_broadcast(self) -> bool:
        """
        Determine if progress change warrants a WebSocket broadcast.
        
        Broadcasts when progress changes by >= 1%.
        
        Returns:
            True if should broadcast, False otherwise
        """
        current_percent = self.calculate_progress_percent()
        percent_change = abs(current_percent - self.last_broadcast_percent)
        
        if percent_change >= 1.0:
            self.last_broadcast_percent = current_percent
            return True
        
        return False
    
    async def persist_progress(self) -> None:
        """Save progress to MongoDB."""
        client = AsyncIOMotorClient(self.mongodb_url)
        db = client[self.database_name]
        
        try:
            progress_percent = self.calculate_progress_percent()
            estimated_seconds = self.calculate_estimated_seconds_remaining()
            avg_iter_per_sec = self.calculate_average_iterations_per_second()
            
            update_data = {
                "current_iteration": self.current_iteration,
                "total_iterations": self.total_iterations,
                "progress_percent": progress_percent,
                "estimated_seconds_remaining": estimated_seconds,
                "average_iterations_per_second": avg_iter_per_sec,
                "iteration_times": list(self.iteration_times),
                "last_progress_update": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            await db.processing_jobs.update_one(
                {"_id": self.job_id},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"Failed to persist progress: {e}")
        finally:
            client.close()
    
    def get_elapsed_seconds(self) -> Optional[float]:
        """
        Get elapsed time since training started.
        
        Returns:
            Elapsed seconds, or None if not started
        """
        if self.started_at is None:
            return None
        
        elapsed = datetime.utcnow() - self.started_at
        return elapsed.total_seconds()
