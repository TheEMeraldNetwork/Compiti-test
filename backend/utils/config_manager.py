"""
Configuration Manager for Automated Math Solver
FOR TESTING PURPOSES ONLY

Handles loading and validation of configuration settings
from YAML files and environment variables.
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path
from loguru import logger


class ConfigManager:
    """
    Configuration manager for loading and validating settings.
    
    Supports YAML configuration files with environment variable overrides.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If configuration file is invalid
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
        logger.info(f"Configuration loaded from: {self.config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Override with environment variables
            config = self._apply_env_overrides(config)
            
            return config
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Args:
            config: Base configuration dictionary
            
        Returns:
            Configuration with environment overrides applied
        """
        # GitHub token override
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            config['github']['token'] = github_token
        
        # Email configuration overrides
        email_sender = os.getenv('EMAIL_SENDER')
        if email_sender:
            config['email']['sender_email'] = email_sender
        
        email_password = os.getenv('EMAIL_PASSWORD')
        if email_password:
            config['email']['sender_password'] = email_password
        
        # Flask configuration overrides
        flask_env = os.getenv('FLASK_ENV')
        if flask_env:
            if 'flask' not in config:
                config['flask'] = {}
            config['flask']['environment'] = flask_env
        
        flask_debug = os.getenv('FLASK_DEBUG', '').lower() == 'true'
        if flask_debug:
            if 'flask' not in config:
                config['flask'] = {}
            config['flask']['debug'] = flask_debug
        
        return config
    
    def _validate_config(self) -> None:
        """
        Validate required configuration settings.
        
        Raises:
            ValueError: If required settings are missing
        """
        required_sections = ['github', 'scheduler', 'email', 'math_solver', 'logging', 'security']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Required configuration section missing: {section}")
        
        # Validate GitHub settings
        github_config = self.config['github']
        required_github_keys = ['repository', 'branch', 'upload_folder', 'solutions_folder']
        for key in required_github_keys:
            if not github_config.get(key):
                raise ValueError(f"Required GitHub configuration missing: {key}")
        
        # Validate scheduler settings
        scheduler_config = self.config['scheduler']
        if scheduler_config.get('check_interval_minutes', 0) <= 0:
            raise ValueError("Scheduler check interval must be positive")
        
        # Validate email settings (if email notifications are enabled)
        email_config = self.config['email']
        if not email_config.get('smtp_server'):
            logger.warning("Email SMTP server not configured - email notifications disabled")
        
        # Validate math solver settings
        math_config = self.config['math_solver']
        if not math_config.get('supported_formats'):
            raise ValueError("No supported file formats specified")
        
        # Validate security settings
        security_config = self.config['security']
        if security_config.get('max_file_size_mb', 0) <= 0:
            raise ValueError("Maximum file size must be positive")
        
        logger.info("Configuration validation passed")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a specific configuration section.
        
        Args:
            section: Section name to retrieve
            
        Returns:
            Section configuration dictionary
            
        Raises:
            KeyError: If section doesn't exist
        """
        if section not in self.config:
            raise KeyError(f"Configuration section not found: {section}")
        
        return self.config[section].copy()
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            return self.config[section][key]
        except KeyError:
            if default is not None:
                return default
            raise KeyError(f"Configuration value not found: {section}.{key}")
    
    def update_value(self, section: str, key: str, value: Any) -> None:
        """
        Update a configuration value at runtime.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            value: New value to set
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        logger.debug(f"Updated configuration: {section}.{key} = {value}")
    
    def save_config(self, output_path: str = None) -> None:
        """
        Save current configuration to YAML file.
        
        Args:
            output_path: Path to save configuration (defaults to original path)
        """
        output_path = output_path or self.config_path
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def reload_config(self) -> None:
        """
        Reload configuration from file.
        
        Useful for picking up configuration changes at runtime.
        """
        try:
            old_config = self.config.copy()
            self.config = self._load_config()
            self._validate_config()
            logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            self.config = old_config
            logger.error(f"Error reloading configuration, reverted to previous: {e}")
            raise
    
    def get_log_config(self) -> Dict[str, Any]:
        """
        Get logging configuration for loguru setup.
        
        Returns:
            Logging configuration dictionary
        """
        log_config = self.get_section('logging')
        
        # Ensure log directory exists
        log_file = log_config.get('log_file', 'logs/math_solver.log')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            'level': log_config.get('level', 'INFO'),
            'file': log_file,
            'rotation': log_config.get('max_file_size', '10MB'),
            'retention': log_config.get('backup_count', 5),
            'format': "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
        }
