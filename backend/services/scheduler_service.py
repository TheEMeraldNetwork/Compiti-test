"""
Scheduler Service for Automated Math Solver
FOR TESTING PURPOSES ONLY

This module handles the scheduling and orchestration of the math solving pipeline:
- Monitors GitHub repository for new files every 30 minutes
- Coordinates file processing workflow
- Manages retries and error handling
- Provides manual trigger capability for testing
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import traceback

import schedule
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from .github_service import GitHubService
from .math_solver import MathematicalSolver
from .email_service import EmailService
from ..utils.config_manager import ConfigManager
from ..utils.validators import ContentValidator


class SchedulerService:
    """
    Main scheduler service that orchestrates the automated math solving pipeline.
    
    Coordinates between GitHub monitoring, problem solving, and notification services.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize scheduler service with all required components.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Initialize services
        self.github_service = GitHubService(config_path)
        self.math_solver = MathematicalSolver()
        self.email_service = EmailService(config_path)
        self.validator = ContentValidator()
        
        # Scheduler configuration
        self.check_interval = self.config['scheduler']['check_interval_minutes']
        self.max_retries = self.config['scheduler']['max_retries']
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'problems_solved': 0,
            'problems_failed': 0,
            'last_run': None,
            'last_success': None,
            'last_error': None
        }
        
        # Callbacks for external monitoring
        self.callbacks = {
            'on_new_problem': [],
            'on_solution_complete': [],
            'on_error': []
        }
        
        logger.info(f"Scheduler initialized with {self.check_interval} minute intervals")
    
    def start_scheduler(self) -> None:
        """
        Start the automated scheduler.
        
        Begins monitoring GitHub repository at configured intervals.
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Add the main job
            self.scheduler.add_job(
                func=self.check_and_process_new_problems,
                trigger=IntervalTrigger(minutes=self.check_interval),
                id='main_check_job',
                name='Check for new math problems',
                max_instances=1,  # Prevent overlapping runs
                coalesce=True     # Combine missed runs
            )
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"Scheduler started - checking every {self.check_interval} minutes")
            
            # Run initial check
            self.check_and_process_new_problems()
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def stop_scheduler(self) -> None:
        """Stop the automated scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Scheduler stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def check_and_process_new_problems(self) -> Dict[str, any]:
        """
        Main method that checks for new problems and processes them.
        
        This is the core method called by the scheduler.
        
        Returns:
            Dictionary with processing results
        """
        run_start_time = datetime.now()
        self.stats['total_runs'] += 1
        self.stats['last_run'] = run_start_time
        
        logger.info("Starting scheduled check for new problems")
        
        try:
            # Check for new files
            new_files = self.github_service.get_new_files_since()
            
            if not new_files:
                logger.info("No new files found")
                return {
                    'success': True,
                    'new_files': 0,
                    'processed': 0,
                    'errors': 0,
                    'message': 'No new files to process'
                }
            
            logger.info(f"Found {len(new_files)} new files to process")
            
            # Process each new file
            processed_count = 0
            error_count = 0
            results = []
            
            for file_info in new_files:
                try:
                    result = self.process_single_problem(file_info)
                    results.append(result)
                    
                    if result['success']:
                        processed_count += 1
                        self.stats['problems_solved'] += 1
                        self._trigger_callbacks('on_solution_complete', result)
                    else:
                        error_count += 1
                        self.stats['problems_failed'] += 1
                        self._trigger_callbacks('on_error', result)
                        
                except Exception as e:
                    error_count += 1
                    self.stats['problems_failed'] += 1
                    error_result = {
                        'success': False,
                        'file_name': file_info.get('name', 'unknown'),
                        'error': str(e)
                    }
                    results.append(error_result)
                    self._trigger_callbacks('on_error', error_result)
                    logger.error(f"Error processing {file_info.get('name')}: {e}")
            
            # Update statistics
            if error_count == 0:
                self.stats['successful_runs'] += 1
                self.stats['last_success'] = run_start_time
            else:
                self.stats['failed_runs'] += 1
            
            processing_time = (datetime.now() - run_start_time).total_seconds()
            
            summary = {
                'success': True,
                'new_files': len(new_files),
                'processed': processed_count,
                'errors': error_count,
                'processing_time': f"{processing_time:.2f}s",
                'results': results
            }
            
            logger.info(f"Completed processing: {processed_count} successful, {error_count} errors")
            return summary
            
        except Exception as e:
            self.stats['failed_runs'] += 1
            self.stats['last_error'] = str(e)
            
            logger.error(f"Error in scheduled check: {e}")
            logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': str(e),
                'new_files': 0,
                'processed': 0,
                'errors': 1
            }
    
    def process_single_problem(self, file_info: Dict) -> Dict[str, any]:
        """
        Process a single mathematical problem file.
        
        Args:
            file_info: File information from GitHub service
            
        Returns:
            Processing result dictionary
        """
        file_name = file_info['name']
        logger.info(f"Processing problem file: {file_name}")
        
        try:
            # Trigger callback for new problem
            self._trigger_callbacks('on_new_problem', file_info)
            
            # Download file to temporary location
            temp_file_path = f"temp_files/{file_name}"
            download_success = self.github_service.download_file(file_info, temp_file_path)
            
            if not download_success:
                return {
                    'success': False,
                    'file_name': file_name,
                    'error': 'Failed to download file from GitHub'
                }
            
            # Validate file safety and mathematical content
            is_safe, safety_reason = self.validator.validate_file_safety(temp_file_path)
            if not is_safe:
                return {
                    'success': False,
                    'file_name': file_name,
                    'error': f'File safety validation failed: {safety_reason}'
                }
            
            is_math, math_reason = self.validator.validate_mathematical_content(temp_file_path)
            if not is_math:
                return {
                    'success': False,
                    'file_name': file_name,
                    'error': f'Mathematical content validation failed: {math_reason}'
                }
            
            # Extract text content for solving
            text_content = self._extract_text_from_file(temp_file_path)
            if not text_content:
                return {
                    'success': False,
                    'file_name': file_name,
                    'error': 'Could not extract text content from file'
                }
            
            # Solve the mathematical problem
            solution_result = self.math_solver.solve_problem(text_content, file_name)
            
            if not solution_result['success']:
                return {
                    'success': False,
                    'file_name': file_name,
                    'error': solution_result.get('error_message', 'Unknown solving error'),
                    'solution_attempt': solution_result
                }
            
            # Format solution for upload
            solution_content = self._format_solution_for_upload(solution_result)
            
            # Upload solution to GitHub
            upload_success = self.github_service.upload_solution(
                file_name, solution_content, 'md'
            )
            
            if not upload_success:
                return {
                    'success': False,
                    'file_name': file_name,
                    'error': 'Failed to upload solution to GitHub',
                    'solution_data': solution_result
                }
            
            # Update main page with new solution
            solution_info = {
                'problem_name': file_name,
                'status': 'Solved Successfully',
                'solution_url': f"solutions/solution_{file_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                'processing_time': solution_result['processing_time']
            }
            
            self.github_service.update_main_page(solution_info)
            
            # Send email notification
            self.email_service.send_solution_notification(
                file_name, solution_result, solution_info['solution_url']
            )
            
            logger.info(f"Successfully processed problem: {file_name}")
            
            return {
                'success': True,
                'file_name': file_name,
                'solution_result': solution_result,
                'solution_info': solution_info,
                'message': 'Problem solved and solution uploaded successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing problem {file_name}: {e}")
            logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'file_name': file_name,
                'error': f'Processing error: {str(e)}'
            }
    
    def manual_trigger(self) -> Dict[str, any]:
        """
        Manually trigger the problem checking and processing.
        
        Useful for testing and immediate processing.
        
        Returns:
            Processing result dictionary
        """
        logger.info("Manual trigger initiated")
        return self.check_and_process_new_problems()
    
    def _extract_text_from_file(self, file_path: str) -> Optional[str]:
        """
        Extract text content from file using the validator.
        
        Args:
            file_path: Path to file
            
        Returns:
            Extracted text content or None
        """
        try:
            from pathlib import Path
            file_ext = Path(file_path).suffix.lower()
            return self.validator._extract_text_content(file_path, file_ext)
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None
    
    def _format_solution_for_upload(self, solution_result: Dict) -> str:
        """
        Format solution result for GitHub upload.
        
        Args:
            solution_result: Result from math solver
            
        Returns:
            Formatted solution content
        """
        content = f"""# Mathematical Problem Solution

**FOR TESTING PURPOSES ONLY**

## Original Problem
```
{solution_result.get('original_text', 'N/A')}
```

## Problem Type
{solution_result.get('problem_type', 'Unknown')}

## Solution
{solution_result.get('solution', 'No solution available')}

## Solution Steps
"""
        
        steps = solution_result.get('steps', [])
        if steps:
            for i, step in enumerate(steps, 1):
                content += f"{i}. {step}\n"
        else:
            content += "No detailed steps available.\n"
        
        content += f"""
## Processing Information
- **Processing Time**: {solution_result.get('processing_time', 'N/A')}
- **Timestamp**: {solution_result.get('timestamp', 'N/A')}
- **File Name**: {solution_result.get('file_name', 'N/A')}
- **Success**: {'✅ Yes' if solution_result.get('success') else '❌ No'}

"""
        
        if solution_result.get('error_message'):
            content += f"""## Error Information
{solution_result['error_message']}

"""
        
        content += """---
*Generated by Automated Math Solver - FOR TESTING PURPOSES ONLY*
"""
        
        return content
    
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """
        Add callback for specific events.
        
        Args:
            event_type: Type of event ('on_new_problem', 'on_solution_complete', 'on_error')
            callback: Function to call when event occurs
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.debug(f"Added callback for {event_type}")
        else:
            logger.warning(f"Unknown callback event type: {event_type}")
    
    def _trigger_callbacks(self, event_type: str, data: Dict) -> None:
        """Trigger all callbacks for a specific event type."""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in callback for {event_type}: {e}")
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get scheduler statistics.
        
        Returns:
            Dictionary with scheduler statistics
        """
        return self.stats.copy()
    
    def get_status(self) -> Dict[str, any]:
        """
        Get current scheduler status.
        
        Returns:
            Dictionary with current status information
        """
        return {
            'is_running': self.is_running,
            'check_interval_minutes': self.check_interval,
            'next_run': self._get_next_run_time(),
            'stats': self.get_stats(),
            'services_status': {
                'github': self._check_github_status(),
                'email': self._check_email_status(),
                'math_solver': True  # Always available
            }
        }
    
    def _get_next_run_time(self) -> Optional[str]:
        """Get next scheduled run time."""
        if not self.is_running:
            return None
        
        try:
            jobs = self.scheduler.get_jobs()
            if jobs:
                return jobs[0].next_run_time.isoformat()
        except:
            pass
        
        return None
    
    def _check_github_status(self) -> bool:
        """Check if GitHub service is accessible."""
        try:
            self.github_service.get_repository_stats()
            return True
        except:
            return False
    
    def _check_email_status(self) -> bool:
        """Check if email service is configured."""
        try:
            return self.email_service.is_configured()
        except:
            return False
