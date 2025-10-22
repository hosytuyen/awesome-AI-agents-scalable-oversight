"""
Task Scheduler

Handles scheduling and automation of paper monitoring tasks.
Supports daily, weekly, and custom scheduling patterns.
"""

import schedule
import time
from datetime import datetime, timedelta
from typing import Callable, Optional
from loguru import logger
import threading
from dataclasses import dataclass


@dataclass
class ScheduleConfig:
    """Configuration for task scheduling."""
    frequency: str  # daily, weekly, custom
    time: str  # HH:MM format
    days: Optional[list] = None  # For weekly scheduling
    custom_interval: Optional[int] = None  # Minutes for custom


class TaskScheduler:
    """Manages scheduled tasks for paper monitoring."""
    
    def __init__(self):
        """Initialize the task scheduler."""
        self.jobs = {}
        self.running = False
        self.scheduler_thread = None
    
    def schedule_daily_task(self, task_func: Callable, time_str: str, task_name: str = "daily_paper_check"):
        """
        Schedule a daily task at a specific time.
        
        Args:
            task_func: Function to execute
            time_str: Time in HH:MM format
            task_name: Name for the scheduled task
        """
        try:
            # Parse time string
            hour, minute = map(int, time_str.split(':'))
            
            # Schedule the task
            job = schedule.every().day.at(time_str).do(task_func)
            self.jobs[task_name] = job
            
            logger.info(f"Scheduled daily task '{task_name}' at {time_str}")
            
        except Exception as e:
            logger.error(f"Error scheduling daily task: {e}")
    
    def schedule_weekly_task(self, task_func: Callable, day: str, time_str: str, task_name: str = "weekly_paper_check"):
        """
        Schedule a weekly task on a specific day and time.
        
        Args:
            task_func: Function to execute
            day: Day of the week (monday, tuesday, etc.)
            time_str: Time in HH:MM format
            task_name: Name for the scheduled task
        """
        try:
            # Get the day method
            day_method = getattr(schedule.every(), day)
            job = day_method.at(time_str).do(task_func)
            self.jobs[task_name] = job
            
            logger.info(f"Scheduled weekly task '{task_name}' on {day} at {time_str}")
            
        except Exception as e:
            logger.error(f"Error scheduling weekly task: {e}")
    
    def schedule_custom_task(self, task_func: Callable, interval_minutes: int, task_name: str = "custom_paper_check"):
        """
        Schedule a task with custom interval.
        
        Args:
            task_func: Function to execute
            interval_minutes: Interval in minutes
            task_name: Name for the scheduled task
        """
        try:
            job = schedule.every(interval_minutes).minutes.do(task_func)
            self.jobs[task_name] = job
            
            logger.info(f"Scheduled custom task '{task_name}' every {interval_minutes} minutes")
            
        except Exception as e:
            logger.error(f"Error scheduling custom task: {e}")
    
    def schedule_from_config(self, task_func: Callable, config: ScheduleConfig, task_name: str = "paper_monitor"):
        """
        Schedule a task based on configuration.
        
        Args:
            task_func: Function to execute
            config: ScheduleConfig object
            task_name: Name for the scheduled task
        """
        try:
            if config.frequency == "daily":
                self.schedule_daily_task(task_func, config.time, task_name)
            elif config.frequency == "weekly":
                if config.days:
                    for day in config.days:
                        self.schedule_weekly_task(task_func, day, config.time, f"{task_name}_{day}")
                else:
                    self.schedule_weekly_task(task_func, "monday", config.time, task_name)
            elif config.frequency == "custom":
                if config.custom_interval:
                    self.schedule_custom_task(task_func, config.custom_interval, task_name)
                else:
                    logger.warning("Custom frequency specified but no interval provided")
            else:
                logger.error(f"Unknown frequency: {config.frequency}")
                
        except Exception as e:
            logger.error(f"Error scheduling from config: {e}")
    
    def start_scheduler(self):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Scheduler stopped")
    
    def run_pending_tasks(self):
        """Run all pending scheduled tasks."""
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Error running pending tasks: {e}")
    
    def get_next_run_times(self) -> dict:
        """
        Get the next run times for all scheduled jobs.
        
        Returns:
            Dictionary of job names and next run times
        """
        next_runs = {}
        for job_name, job in self.jobs.items():
            if hasattr(job, 'next_run'):
                next_runs[job_name] = job.next_run
            else:
                next_runs[job_name] = "Unknown"
        
        return next_runs
    
    def cancel_job(self, task_name: str) -> bool:
        """
        Cancel a scheduled job.
        
        Args:
            task_name: Name of the task to cancel
            
        Returns:
            True if job was cancelled successfully
        """
        try:
            if task_name in self.jobs:
                schedule.cancel_job(self.jobs[task_name])
                del self.jobs[task_name]
                logger.info(f"Cancelled job: {task_name}")
                return True
            else:
                logger.warning(f"Job '{task_name}' not found")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling job {task_name}: {e}")
            return False
    
    def clear_all_jobs(self):
        """Clear all scheduled jobs."""
        try:
            schedule.clear()
            self.jobs.clear()
            logger.info("Cleared all scheduled jobs")
        except Exception as e:
            logger.error(f"Error clearing jobs: {e}")
    
    def _run_scheduler(self):
        """Internal method to run the scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def get_scheduler_status(self) -> dict:
        """
        Get the current status of the scheduler.
        
        Returns:
            Dictionary with scheduler status information
        """
        return {
            "running": self.running,
            "jobs_count": len(self.jobs),
            "job_names": list(self.jobs.keys()),
            "next_runs": self.get_next_run_times()
        }
