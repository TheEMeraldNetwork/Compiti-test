#!/usr/bin/env python3
"""
Main Application for Automated Math Solver
FOR TESTING PURPOSES ONLY

This is the main entry point for the automated math solving system.
It provides both a command-line interface and a Flask web API.
"""

import os
import sys
import argparse
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from loguru import logger
import yaml

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from backend.services.scheduler_service import SchedulerService
from backend.services.github_service import GitHubService
from backend.services.math_solver import MathematicalSolver
from backend.services.email_service import EmailService
from backend.utils.config_manager import ConfigManager


class MathSolverApp:
    """
    Main application class for the Automated Math Solver.
    
    Provides both CLI and web API interfaces.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize services
        self.scheduler_service = None
        self.github_service = None
        self.math_solver = None
        self.email_service = None
        
        # Flask app
        self.app = Flask(__name__, 
                        template_folder='frontend',
                        static_folder='frontend')
        CORS(self.app)
        
        self._setup_routes()
        
        logger.info("Math Solver Application initialized")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_config = self.config_manager.get_log_config()
        
        # Remove default logger
        logger.remove()
        
        # Add console logger
        logger.add(
            sys.stdout,
            level=log_config['level'],
            format=log_config['format'],
            colorize=True
        )
        
        # Add file logger
        logger.add(
            log_config['file'],
            level=log_config['level'],
            format=log_config['format'],
            rotation=log_config['rotation'],
            retention=log_config['retention'],
            compression="zip"
        )
        
        logger.info("Logging configured successfully")
    
    def _initialize_services(self) -> None:
        """Initialize all services."""
        try:
            logger.info("Initializing services...")
            
            self.scheduler_service = SchedulerService(self.config_path)
            self.github_service = GitHubService(self.config_path)
            self.math_solver = MathematicalSolver()
            self.email_service = EmailService(self.config_path)
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            raise
    
    def _setup_routes(self) -> None:
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Serve the main web interface."""
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def api_status():
            """Get system status."""
            try:
                if not self.scheduler_service:
                    self._initialize_services()
                
                status = self.scheduler_service.get_status()
                return jsonify({
                    'success': True,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/trigger', methods=['POST'])
        def api_trigger():
            """Manually trigger problem checking."""
            try:
                if not self.scheduler_service:
                    self._initialize_services()
                
                result = self.scheduler_service.manual_trigger()
                return jsonify({
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in manual trigger: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/solutions')
        def api_solutions():
            """Get recent solutions."""
            try:
                if not self.github_service:
                    self._initialize_services()
                
                # Get recent solutions from GitHub
                # This is a placeholder - implement based on your GitHub structure
                solutions = []
                
                return jsonify({
                    'success': True,
                    'solutions': solutions,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting solutions: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/test-email', methods=['POST'])
        def api_test_email():
            """Test email configuration."""
            try:
                if not self.email_service:
                    self._initialize_services()
                
                success, message = self.email_service.test_email_connection()
                
                return jsonify({
                    'success': success,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error testing email: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/upload', methods=['POST'])
        def api_upload():
            """Handle file upload and processing."""
            try:
                if not self.scheduler_service:
                    self._initialize_services()
                
                if 'file' not in request.files:
                    return jsonify({'success': False, 'error': 'No file provided'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'success': False, 'error': 'No file selected'}), 400
                
                # Save file temporarily
                import tempfile
                import os
                temp_path = os.path.join('temp_files', file.filename)
                file.save(temp_path)
                
                # Process the file directly
                with open(temp_path, 'r') as f:
                    content = f.read()
                
                # Solve the problem
                result = self.math_solver.solve_problem(content, file.filename)
                
                # Clean up temp file
                os.remove(temp_path)
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in file upload: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/config')
        def api_config():
            """Get public configuration information."""
            try:
                public_config = {
                    'github': {
                        'repository': self.config['github']['repository'],
                        'upload_folder': self.config['github']['upload_folder'],
                        'solutions_folder': self.config['github']['solutions_folder']
                    },
                    'scheduler': {
                        'check_interval_minutes': self.config['scheduler']['check_interval_minutes']
                    },
                    'supported_formats': self.config['math_solver']['supported_formats']
                }
                
                return jsonify({
                    'success': True,
                    'config': public_config,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting config: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def start_scheduler(self) -> None:
        """Start the automated scheduler."""
        try:
            if not self.scheduler_service:
                self._initialize_services()
            
            self.scheduler_service.start_scheduler()
            logger.info("Scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop_scheduler(self) -> None:
        """Stop the automated scheduler."""
        try:
            if self.scheduler_service:
                self.scheduler_service.stop_scheduler()
                logger.info("Scheduler stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def run_web_server(self, host: str = '127.0.0.1', port: int = 5000, debug: bool = False) -> None:
        """
        Run the Flask web server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        try:
            logger.info(f"Starting web server on {host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
            
        except Exception as e:
            logger.error(f"Error running web server: {e}")
            raise
    
    def manual_trigger(self) -> Dict[str, Any]:
        """Manually trigger problem processing."""
        try:
            if not self.scheduler_service:
                self._initialize_services()
            
            return self.scheduler_service.manual_trigger()
            
        except Exception as e:
            logger.error(f"Error in manual trigger: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        try:
            if not self.scheduler_service:
                self._initialize_services()
            
            return self.scheduler_service.get_status()
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, cleaning up...")
    sys.exit(0)


def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(
        description='Automated Math Solver - FOR TESTING PURPOSES ONLY'
    )
    
    parser.add_argument(
        '--config', 
        default='config.yaml',
        help='Path to configuration file'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the scheduler')
    start_parser.add_argument('--web', action='store_true', help='Also start web server')
    start_parser.add_argument('--host', default='127.0.0.1', help='Web server host')
    start_parser.add_argument('--port', type=int, default=5000, help='Web server port')
    start_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Web command
    web_parser = subparsers.add_parser('web', help='Start web server only')
    web_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    web_parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    web_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Trigger command
    trigger_parser = subparsers.add_parser('trigger', help='Manually trigger processing')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test system components')
    test_parser.add_argument('--email', action='store_true', help='Test email configuration')
    test_parser.add_argument('--github', action='store_true', help='Test GitHub connection')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create app instance
    app = MathSolverApp(args.config)
    
    try:
        if args.command == 'start':
            app.start_scheduler()
            
            if args.web:
                app.run_web_server(args.host, args.port, args.debug)
            else:
                logger.info("Scheduler running. Press Ctrl+C to stop.")
                # Keep the main thread alive
                import time
                while True:
                    time.sleep(1)
        
        elif args.command == 'web':
            app.run_web_server(args.host, args.port, args.debug)
        
        elif args.command == 'trigger':
            result = app.manual_trigger()
            print(yaml.dump(result, default_flow_style=False))
        
        elif args.command == 'status':
            status = app.get_status()
            print(yaml.dump(status, default_flow_style=False))
        
        elif args.command == 'test':
            app._initialize_services()
            
            if args.email:
                success, message = app.email_service.test_email_connection()
                print(f"Email test: {'✅ PASS' if success else '❌ FAIL'} - {message}")
            
            if args.github:
                try:
                    stats = app.github_service.get_repository_stats()
                    print(f"GitHub test: ✅ PASS - Connected to {stats.get('name', 'repository')}")
                except Exception as e:
                    print(f"GitHub test: ❌ FAIL - {e}")
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        app.stop_scheduler()


if __name__ == '__main__':
    main()
