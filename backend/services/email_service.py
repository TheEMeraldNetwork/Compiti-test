"""
Email Service for Automated Math Solver
FOR TESTING PURPOSES ONLY

This module handles email notifications for the math solving system:
- Sends confirmation emails when problems are solved
- Provides error notifications
- Supports both HTML and plain text formats
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import traceback

from loguru import logger
from email_validator import validate_email, EmailNotValidError
from dotenv import load_dotenv

from ..utils.config_manager import ConfigManager

# Load environment variables
load_dotenv()


class EmailService:
    """
    Email service for sending notifications about mathematical problem solutions.
    
    Supports multiple email formats and attachment capabilities.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize email service with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Email configuration
        self.email_config = self.config['email']
        self.smtp_server = self.email_config.get('smtp_server')
        self.smtp_port = self.email_config.get('smtp_port', 587)
        self.sender_email = os.getenv('EMAIL_SENDER') or self.email_config.get('sender_email')
        self.sender_password = os.getenv('EMAIL_PASSWORD') or self.email_config.get('sender_password')
        
        # Validate configuration
        self.is_configured_flag = self._validate_configuration()
        
        if self.is_configured_flag:
            logger.info("Email service configured successfully")
        else:
            logger.warning("Email service not properly configured - notifications disabled")
    
    def _validate_configuration(self) -> bool:
        """
        Validate email configuration.
        
        Returns:
            True if properly configured, False otherwise
        """
        if not self.smtp_server:
            logger.warning("SMTP server not configured")
            return False
        
        if not self.sender_email:
            logger.warning("Sender email not configured")
            return False
        
        if not self.sender_password:
            logger.warning("Sender password not configured")
            return False
        
        # Validate email format
        try:
            validate_email(self.sender_email)
        except EmailNotValidError:
            logger.warning(f"Invalid sender email format: {self.sender_email}")
            return False
        
        return True
    
    def is_configured(self) -> bool:
        """
        Check if email service is properly configured.
        
        Returns:
            True if configured, False otherwise
        """
        return self.is_configured_flag
    
    def send_solution_notification(self, problem_file: str, solution_result: Dict, 
                                 solution_url: str, recipient_email: str = None) -> bool:
        """
        Send email notification about a solved mathematical problem.
        
        Args:
            problem_file: Name of the original problem file
            solution_result: Result dictionary from math solver
            solution_url: URL to the solution on GitHub
            recipient_email: Optional recipient email (uses sender if not provided)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured_flag:
            logger.warning("Email service not configured - cannot send notification")
            return False
        
        try:
            # Use sender email as recipient if not specified
            recipient = recipient_email or self.sender_email
            
            # Validate recipient email
            try:
                validate_email(recipient)
            except EmailNotValidError:
                logger.error(f"Invalid recipient email: {recipient}")
                return False
            
            # Create email content
            subject = f"Math Problem Solved: {problem_file}"
            html_content = self._create_solution_html(problem_file, solution_result, solution_url)
            text_content = self._create_solution_text(problem_file, solution_result, solution_url)
            
            # Send email
            success = self._send_email(recipient, subject, text_content, html_content)
            
            if success:
                logger.info(f"Solution notification sent for {problem_file}")
            else:
                logger.error(f"Failed to send notification for {problem_file}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending solution notification: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def send_error_notification(self, problem_file: str, error_message: str, 
                              recipient_email: str = None) -> bool:
        """
        Send email notification about a processing error.
        
        Args:
            problem_file: Name of the problem file that failed
            error_message: Error message to include
            recipient_email: Optional recipient email
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured_flag:
            logger.warning("Email service not configured - cannot send error notification")
            return False
        
        try:
            recipient = recipient_email or self.sender_email
            
            # Validate recipient email
            try:
                validate_email(recipient)
            except EmailNotValidError:
                logger.error(f"Invalid recipient email: {recipient}")
                return False
            
            # Create email content
            subject = f"Math Problem Processing Error: {problem_file}"
            html_content = self._create_error_html(problem_file, error_message)
            text_content = self._create_error_text(problem_file, error_message)
            
            # Send email
            success = self._send_email(recipient, subject, text_content, html_content)
            
            if success:
                logger.info(f"Error notification sent for {problem_file}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False
    
    def send_status_report(self, stats: Dict, recipient_email: str = None) -> bool:
        """
        Send periodic status report email.
        
        Args:
            stats: Statistics dictionary from scheduler service
            recipient_email: Optional recipient email
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured_flag:
            return False
        
        try:
            recipient = recipient_email or self.sender_email
            
            subject = f"Math Solver Status Report - {datetime.now().strftime('%Y-%m-%d')}"
            html_content = self._create_status_html(stats)
            text_content = self._create_status_text(stats)
            
            return self._send_email(recipient, subject, text_content, html_content)
            
        except Exception as e:
            logger.error(f"Error sending status report: {e}")
            return False
    
    def _send_email(self, recipient: str, subject: str, text_content: str, 
                   html_content: str = None, attachments: List[str] = None) -> bool:
        """
        Send email with text and optional HTML content.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            text_content: Plain text content
            html_content: Optional HTML content
            attachments: Optional list of file paths to attach
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add text content
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML content if provided
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(msg, file_path)
            
            # Connect to server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable encryption
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed - check email credentials")
            return False
        except smtplib.SMTPConnectError:
            logger.error(f"Could not connect to SMTP server: {self.smtp_server}:{self.smtp_port}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str) -> None:
        """Add file attachment to email message."""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {e}")
    
    def _create_solution_html(self, problem_file: str, solution_result: Dict, 
                            solution_url: str) -> str:
        """Create HTML content for solution notification."""
        success_status = "✅ Successfully Solved" if solution_result.get('success') else "❌ Failed to Solve"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .success {{ color: #28a745; }}
        .error {{ color: #dc3545; }}
        .info {{ background-color: #e9ecef; padding: 10px; border-radius: 3px; }}
        .solution {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; }}
        .disclaimer {{ font-size: 12px; color: #666; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Mathematical Problem Solved</h2>
        <p class="disclaimer">FOR TESTING PURPOSES ONLY</p>
    </div>
    
    <div class="content">
        <h3>Problem Details</h3>
        <div class="info">
            <p><strong>File:</strong> {problem_file}</p>
            <p><strong>Status:</strong> <span class="{'success' if solution_result.get('success') else 'error'}">{success_status}</span></p>
            <p><strong>Processing Time:</strong> {solution_result.get('processing_time', 'N/A')}</p>
            <p><strong>Timestamp:</strong> {solution_result.get('timestamp', 'N/A')}</p>
        </div>
        
        <h3>Problem Type</h3>
        <p>{solution_result.get('problem_type', 'Unknown')}</p>
        
        <h3>Solution</h3>
        <div class="solution">
            <pre>{solution_result.get('solution', 'No solution available')}</pre>
        </div>
        
        <h3>View Full Solution</h3>
        <p><a href="{solution_url}" target="_blank">Click here to view the complete solution on GitHub</a></p>
        
        <hr>
        <p class="disclaimer">
            This email was generated automatically by the Math Solver system.<br>
            FOR TESTING PURPOSES ONLY - Do not use for production or critical applications.
        </p>
    </div>
</body>
</html>
"""
        return html
    
    def _create_solution_text(self, problem_file: str, solution_result: Dict, 
                            solution_url: str) -> str:
        """Create plain text content for solution notification."""
        success_status = "Successfully Solved" if solution_result.get('success') else "Failed to Solve"
        
        text = f"""Mathematical Problem Solved
FOR TESTING PURPOSES ONLY

Problem Details:
- File: {problem_file}
- Status: {success_status}
- Processing Time: {solution_result.get('processing_time', 'N/A')}
- Timestamp: {solution_result.get('timestamp', 'N/A')}

Problem Type: {solution_result.get('problem_type', 'Unknown')}

Solution:
{solution_result.get('solution', 'No solution available')}

View Full Solution:
{solution_url}

---
This email was generated automatically by the Math Solver system.
FOR TESTING PURPOSES ONLY - Do not use for production or critical applications.
"""
        return text
    
    def _create_error_html(self, problem_file: str, error_message: str) -> str:
        """Create HTML content for error notification."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #f8d7da; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .error {{ color: #721c24; }}
        .error-box {{ background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; }}
        .disclaimer {{ font-size: 12px; color: #666; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h2 class="error">Mathematical Problem Processing Error</h2>
        <p class="disclaimer">FOR TESTING PURPOSES ONLY</p>
    </div>
    
    <div class="content">
        <h3>Error Details</h3>
        <p><strong>File:</strong> {problem_file}</p>
        <p><strong>Timestamp:</strong> {datetime.now().isoformat()}</p>
        
        <h3>Error Message</h3>
        <div class="error-box">
            <pre>{error_message}</pre>
        </div>
        
        <h3>Next Steps</h3>
        <ul>
            <li>Check if the file contains valid mathematical content</li>
            <li>Ensure the file format is supported</li>
            <li>Review the problem text for clarity</li>
            <li>Check system logs for additional details</li>
        </ul>
        
        <hr>
        <p class="disclaimer">
            This email was generated automatically by the Math Solver system.<br>
            FOR TESTING PURPOSES ONLY - Do not use for production or critical applications.
        </p>
    </div>
</body>
</html>
"""
        return html
    
    def _create_error_text(self, problem_file: str, error_message: str) -> str:
        """Create plain text content for error notification."""
        text = f"""Mathematical Problem Processing Error
FOR TESTING PURPOSES ONLY

Error Details:
- File: {problem_file}
- Timestamp: {datetime.now().isoformat()}

Error Message:
{error_message}

Next Steps:
- Check if the file contains valid mathematical content
- Ensure the file format is supported
- Review the problem text for clarity
- Check system logs for additional details

---
This email was generated automatically by the Math Solver system.
FOR TESTING PURPOSES ONLY - Do not use for production or critical applications.
"""
        return text
    
    def _create_status_html(self, stats: Dict) -> str:
        """Create HTML content for status report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #d4edda; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; }}
        .stats {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
        .disclaimer {{ font-size: 12px; color: #666; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Math Solver Status Report</h2>
        <p class="disclaimer">FOR TESTING PURPOSES ONLY</p>
    </div>
    
    <div class="content">
        <div class="stats">
            <h3>System Statistics</h3>
            <p><strong>Total Runs:</strong> {stats.get('total_runs', 0)}</p>
            <p><strong>Successful Runs:</strong> {stats.get('successful_runs', 0)}</p>
            <p><strong>Failed Runs:</strong> {stats.get('failed_runs', 0)}</p>
            <p><strong>Problems Solved:</strong> {stats.get('problems_solved', 0)}</p>
            <p><strong>Problems Failed:</strong> {stats.get('problems_failed', 0)}</p>
            <p><strong>Last Run:</strong> {stats.get('last_run', 'Never')}</p>
            <p><strong>Last Success:</strong> {stats.get('last_success', 'Never')}</p>
        </div>
        
        <hr>
        <p class="disclaimer">
            This email was generated automatically by the Math Solver system.<br>
            FOR TESTING PURPOSES ONLY - Do not use for production or critical applications.
        </p>
    </div>
</body>
</html>
"""
        return html
    
    def _create_status_text(self, stats: Dict) -> str:
        """Create plain text content for status report."""
        text = f"""Math Solver Status Report
FOR TESTING PURPOSES ONLY

System Statistics:
- Total Runs: {stats.get('total_runs', 0)}
- Successful Runs: {stats.get('successful_runs', 0)}
- Failed Runs: {stats.get('failed_runs', 0)}
- Problems Solved: {stats.get('problems_solved', 0)}
- Problems Failed: {stats.get('problems_failed', 0)}
- Last Run: {stats.get('last_run', 'Never')}
- Last Success: {stats.get('last_success', 'Never')}

---
This email was generated automatically by the Math Solver system.
FOR TESTING PURPOSES ONLY - Do not use for production or critical applications.
"""
        return text
    
    def test_email_connection(self) -> Tuple[bool, str]:
        """
        Test email connection and configuration.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.is_configured_flag:
            return False, "Email service not properly configured"
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
            
            return True, "Email connection test successful"
            
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP authentication failed - check credentials"
        except smtplib.SMTPConnectError:
            return False, f"Could not connect to SMTP server: {self.smtp_server}:{self.smtp_port}"
        except Exception as e:
            return False, f"Email connection test failed: {str(e)}"
