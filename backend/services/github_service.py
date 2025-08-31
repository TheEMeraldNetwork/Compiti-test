"""
GitHub Service for Automated Math Solver
FOR TESTING PURPOSES ONLY

This module handles all GitHub API interactions including:
- Monitoring repository for new files
- Downloading mathematical problem files
- Uploading solution files
- Managing repository content
"""

import os
import base64
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import requests
from github import Github, GithubException
from loguru import logger
import yaml
from dotenv import load_dotenv

from ..utils.config_manager import ConfigManager
from ..utils.validators import ContentValidator

# Load environment variables
load_dotenv()


class GitHubService:
    """
    Service class for GitHub API operations.
    
    Handles repository monitoring, file downloads, and uploads
    with proper error handling and validation.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize GitHub service with configuration.
        
        Args:
            config_path: Path to configuration file
            
        Raises:
            ValueError: If GitHub token is not provided
            GithubException: If GitHub authentication fails
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Get GitHub token from environment
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError(
                "GitHub token not found. Please set GITHUB_TOKEN environment variable."
            )
        
        try:
            self.github = Github(github_token)
            self.repo_name = self.config['github']['repository']
            self.repository = self.github.get_repo(self.repo_name)
            self.branch = self.config['github']['branch']
            
            # Test authentication
            self.github.get_user().login
            logger.info(f"Successfully authenticated with GitHub for repo: {self.repo_name}")
            
        except GithubException as e:
            logger.error(f"GitHub authentication failed: {e}")
            raise
        
        self.validator = ContentValidator()
        self.last_check_time = None
        
    def get_new_files_since(self, since_time: Optional[datetime] = None) -> List[Dict]:
        """
        Get list of new files uploaded since specified time.
        
        Args:
            since_time: Check for files since this time. If None, checks last hour.
            
        Returns:
            List of file information dictionaries
            
        Raises:
            GithubException: If GitHub API call fails
        """
        try:
            if since_time is None:
                since_time = self.last_check_time or datetime.now(timezone.utc)
            
            # Get commits since specified time
            commits = self.repository.get_commits(
                sha=self.branch,
                since=since_time
            )
            
            new_files = []
            upload_folder = self.config['github']['upload_folder']
            
            for commit in commits:
                # Check each file in the commit
                for file in commit.files:
                    file_path = file.filename
                    
                    # Only process files in upload folder
                    if file_path.startswith(upload_folder + "/"):
                        # Check if file was added or modified
                        if file.status in ['added', 'modified']:
                            # Validate file format
                            if self._is_supported_format(file_path):
                                file_info = {
                                    'path': file_path,
                                    'name': os.path.basename(file_path),
                                    'sha': commit.sha,
                                    'commit_date': commit.commit.author.date,
                                    'size': file.additions + file.deletions,
                                    'download_url': self._get_download_url(file_path)
                                }
                                new_files.append(file_info)
                                logger.info(f"Found new file: {file_path}")
            
            self.last_check_time = datetime.now(timezone.utc)
            return new_files
            
        except GithubException as e:
            logger.error(f"Error getting new files from GitHub: {e}")
            raise
    
    def download_file(self, file_info: Dict, local_path: str) -> bool:
        """
        Download a file from GitHub repository to local path.
        
        Args:
            file_info: File information dictionary from get_new_files_since()
            local_path: Local path to save the file
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Get file content from repository
            file_content = self.repository.get_contents(
                file_info['path'], 
                ref=self.branch
            )
            
            # Decode and save file
            if file_content.encoding == 'base64':
                content = base64.b64decode(file_content.content)
                mode = 'wb'
            else:
                content = file_content.content
                mode = 'w'
            
            with open(local_path, mode) as f:
                f.write(content)
            
            # Validate file size
            max_size_mb = self.config['security']['max_file_size_mb']
            file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
            
            if file_size_mb > max_size_mb:
                os.remove(local_path)
                logger.warning(f"File {file_info['name']} exceeds size limit ({file_size_mb:.1f}MB)")
                return False
            
            logger.info(f"Successfully downloaded: {file_info['name']} ({file_size_mb:.1f}MB)")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file {file_info['name']}: {e}")
            return False
    
    def upload_solution(self, problem_file: str, solution_content: str, 
                       solution_format: str = "md") -> bool:
        """
        Upload solution file to GitHub repository.
        
        Args:
            problem_file: Original problem file name
            solution_content: Solution content as string
            solution_format: Format of solution file (md, txt, pdf)
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            # Generate solution filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            problem_name = Path(problem_file).stem
            solution_filename = f"solution_{problem_name}_{timestamp}.{solution_format}"
            
            solutions_folder = self.config['github']['solutions_folder']
            solution_path = f"{solutions_folder}/{solution_filename}"
            
            # Prepare commit message
            commit_message = f"Add solution for {problem_file} - {timestamp}"
            
            # Check if file already exists
            try:
                existing_file = self.repository.get_contents(solution_path, ref=self.branch)
                # Update existing file
                self.repository.update_file(
                    path=solution_path,
                    message=commit_message,
                    content=solution_content,
                    sha=existing_file.sha,
                    branch=self.branch
                )
                logger.info(f"Updated existing solution file: {solution_filename}")
                
            except GithubException:
                # Create new file
                self.repository.create_file(
                    path=solution_path,
                    message=commit_message,
                    content=solution_content,
                    branch=self.branch
                )
                logger.info(f"Created new solution file: {solution_filename}")
            
            return True
            
        except GithubException as e:
            logger.error(f"Error uploading solution: {e}")
            return False
    
    def update_main_page(self, new_solution: Dict) -> bool:
        """
        Update the main GitHub Pages with new solution notification.
        
        Args:
            new_solution: Dictionary containing solution information
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Get current README.md or index.md
            readme_files = ['README.md', 'index.md', 'index.html']
            main_file = None
            main_content = None
            
            for filename in readme_files:
                try:
                    main_file = self.repository.get_contents(filename, ref=self.branch)
                    main_content = base64.b64decode(main_file.content).decode('utf-8')
                    break
                except GithubException:
                    continue
            
            if main_file is None:
                # Create new index.md file
                main_content = self._create_initial_page()
                filename = 'index.md'
            
            # Add new solution to the content
            updated_content = self._add_solution_to_page(main_content, new_solution)
            
            # Update or create the file
            commit_message = f"Update main page with new solution: {new_solution['problem_name']}"
            
            if main_file:
                self.repository.update_file(
                    path=main_file.path,
                    message=commit_message,
                    content=updated_content,
                    sha=main_file.sha,
                    branch=self.branch
                )
            else:
                self.repository.create_file(
                    path='index.md',
                    message=commit_message,
                    content=updated_content,
                    branch=self.branch
                )
            
            logger.info("Successfully updated main page with new solution")
            return True
            
        except Exception as e:
            logger.error(f"Error updating main page: {e}")
            return False
    
    def _is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported."""
        supported_formats = self.config['math_solver']['supported_formats']
        file_extension = Path(file_path).suffix.lower()
        return file_extension in supported_formats
    
    def _get_download_url(self, file_path: str) -> str:
        """Generate download URL for file."""
        return f"https://api.github.com/repos/{self.repo_name}/contents/{file_path}"
    
    def _create_initial_page(self) -> str:
        """Create initial main page content."""
        return f"""# Automated Math Solver

**FOR TESTING PURPOSES ONLY**

This is an automated mathematical problem solving system that:
- Monitors GitHub repository for new mathematical problems
- Processes and solves problems automatically
- Publishes solutions with timestamps
- Sends email notifications

## Recent Solutions

*No solutions yet. Upload a mathematical problem to get started!*

---
*Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}*
"""
    
    def _add_solution_to_page(self, current_content: str, solution_info: Dict) -> str:
        """Add new solution information to main page."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Create solution entry
        solution_entry = f"""
### 🔢 {solution_info['problem_name']}
- **Solved**: {timestamp}
- **Status**: ✅ {solution_info['status']}
- **Solution**: [View Solution]({solution_info['solution_url']})
- **Processing Time**: {solution_info.get('processing_time', 'N/A')}

"""
        
        # Insert after "## Recent Solutions" section
        if "## Recent Solutions" in current_content:
            parts = current_content.split("## Recent Solutions")
            if len(parts) == 2:
                header = parts[0] + "## Recent Solutions\n"
                # Remove the old "No solutions yet" message if present
                rest = parts[1].replace("*No solutions yet. Upload a mathematical problem to get started!*", "")
                updated_content = header + solution_entry + rest
            else:
                updated_content = current_content + solution_entry
        else:
            updated_content = current_content + "\n## Recent Solutions\n" + solution_entry
        
        # Update timestamp
        if "*Last updated:" in updated_content:
            import re
            updated_content = re.sub(
                r'\*Last updated:.*?\*',
                f'*Last updated: {timestamp}*',
                updated_content
            )
        else:
            updated_content += f"\n---\n*Last updated: {timestamp}*\n"
        
        return updated_content
    
    def validate_mathematical_content(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if file contains mathematical content.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        return self.validator.validate_mathematical_content(file_path)
    
    def get_repository_stats(self) -> Dict:
        """Get repository statistics."""
        try:
            return {
                'name': self.repository.name,
                'description': self.repository.description,
                'stars': self.repository.stargazers_count,
                'forks': self.repository.forks_count,
                'issues': self.repository.open_issues_count,
                'last_updated': self.repository.updated_at,
                'size': self.repository.size
            }
        except Exception as e:
            logger.error(f"Error getting repository stats: {e}")
            return {}
