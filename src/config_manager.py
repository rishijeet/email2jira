"""
Configuration manager module for the Email2Jira framework.
This module handles loading and managing configuration.
"""
__author__ = "Rishijeet"

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    A class to handle configuration loading and management.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_dir: Directory containing configuration files (default: './config')
        """
        self.config_dir = config_dir or os.path.join(os.getcwd(), 'config')
        self.config = {
            'email': {},
            'jira': {},
            'parser': {},
            'general': {}
        }
        
    def load_config(self) -> bool:
        """
        Load configuration from files.
        
        Returns:
            bool: True if configuration loaded successfully, False otherwise
        """
        try:
            # Load environment variables from .env file
            load_dotenv()
            
            # Load configuration files
            self._load_config_file('email.yaml', 'email')
            self._load_config_file('jira.yaml', 'jira')
            self._load_config_file('parser.yaml', 'parser')
            self._load_config_file('config.yaml', 'general')
            
            # Override with environment variables
            self._load_from_env()
            
            return True
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def get_email_config(self) -> Dict[str, Any]:
        """
        Get email configuration.
        
        Returns:
            Dictionary containing email configuration
        """
        return self.config.get('email', {})
    
    def get_jira_config(self) -> Dict[str, Any]:
        """
        Get Jira configuration.
        
        Returns:
            Dictionary containing Jira configuration
        """
        return self.config.get('jira', {})
    
    def get_parser_config(self) -> Dict[str, Any]:
        """
        Get parser configuration.
        
        Returns:
            Dictionary containing parser configuration
        """
        return self.config.get('parser', {})
    
    def get_general_config(self) -> Dict[str, Any]:
        """
        Get general configuration.
        
        Returns:
            Dictionary containing general configuration
        """
        return self.config.get('general', {})
    
    def _load_config_file(self, filename: str, config_section: str) -> None:
        """
        Load configuration from a file.
        
        Args:
            filename: Name of the configuration file
            config_section: Section in the config dictionary to update
        """
        file_path = os.path.join(self.config_dir, filename)
        if not os.path.exists(file_path):
            logger.warning(f"Configuration file {file_path} not found")
            return
            
        try:
            with open(file_path, 'r') as f:
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    config_data = yaml.safe_load(f)
                elif filename.endswith('.json'):
                    config_data = json.load(f)
                else:
                    logger.warning(f"Unsupported configuration file format: {filename}")
                    return
                    
                if config_data and isinstance(config_data, dict):
                    self.config[config_section].update(config_data)
                    logger.info(f"Loaded configuration from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
    
    def _load_from_env(self) -> None:
        """
        Load configuration from environment variables.
        
        Environment variables should be in the format:
        - EMAIL2JIRA_EMAIL_* for email configuration
        - EMAIL2JIRA_JIRA_* for Jira configuration
        - EMAIL2JIRA_PARSER_* for parser configuration
        - EMAIL2JIRA_* for general configuration
        """
        for key, value in os.environ.items():
            if key.startswith('EMAIL2JIRA_EMAIL_'):
                env_key = key[len('EMAIL2JIRA_EMAIL_'):].lower()
                self._set_nested_config('email', env_key, value)
            elif key.startswith('EMAIL2JIRA_JIRA_'):
                env_key = key[len('EMAIL2JIRA_JIRA_'):].lower()
                self._set_nested_config('jira', env_key, value)
            elif key.startswith('EMAIL2JIRA_PARSER_'):
                env_key = key[len('EMAIL2JIRA_PARSER_'):].lower()
                self._set_nested_config('parser', env_key, value)
            elif key.startswith('EMAIL2JIRA_'):
                env_key = key[len('EMAIL2JIRA_'):].lower()
                self._set_nested_config('general', env_key, value)
    
    def _set_nested_config(self, section: str, key: str, value: str) -> None:
        """
        Set a nested configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key (can be nested with dots)
            value: Configuration value
        """
        # Try to convert value to appropriate type
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
            value = float(value)
        
        # Handle nested keys
        if '.' in key:
            parts = key.split('.')
            current = self.config[section]
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            self.config[section][key] = value
    
    def create_default_config_files(self) -> bool:
        """
        Create default configuration files if they don't exist.
        
        Returns:
            bool: True if files created successfully, False otherwise
        """
        try:
            # Create config directory if it doesn't exist
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Create default email config
            email_config = {
                'server': 'imap.example.com',
                'port': 993,
                'username': 'your-email@example.com',
                'password': 'your-password',
                'use_ssl': True,
                'mailbox': 'INBOX'
            }
            self._create_config_file('email.yaml', email_config)
            
            # Create default Jira config
            jira_config = {
                'server': 'https://your-jira-instance.atlassian.net',
                'username': 'your-username',
                'password': 'your-api-token',
                'project_key': 'PROJ',
                'issue_type': 'Story'
            }
            self._create_config_file('jira.yaml', jira_config)
            
            # Create default parser config
            parser_config = {
                'subject_prefix': '[Email2Jira]',
                'default_issue_type': 'Story',
                'default_priority': 'Medium',
                'custom_patterns': {
                    'epic_link': r'(?i)epic:\s*(\w+-\d+)'
                },
                'field_mappings': {
                    'sender': 'reporter'
                }
            }
            self._create_config_file('parser.yaml', parser_config)
            
            # Create default general config
            general_config = {
                'log_level': 'INFO',
                'max_emails': 10,
                'polling_interval': 300,  # 5 minutes
                'mark_as_read': True
            }
            self._create_config_file('config.yaml', general_config)
            
            return True
        except Exception as e:
            logger.error(f"Failed to create default configuration files: {e}")
            return False
    
    def _create_config_file(self, filename: str, config_data: Dict[str, Any]) -> None:
        """
        Create a configuration file with the given data.
        
        Args:
            filename: Name of the configuration file
            config_data: Configuration data to write
        """
        file_path = os.path.join(self.config_dir, filename)
        if os.path.exists(file_path):
            logger.info(f"Configuration file {file_path} already exists, skipping")
            return
            
        try:
            with open(file_path, 'w') as f:
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    yaml.dump(config_data, f, default_flow_style=False)
                elif filename.endswith('.json'):
                    json.dump(config_data, f, indent=2)
                else:
                    logger.warning(f"Unsupported configuration file format: {filename}")
                    return
                    
            logger.info(f"Created configuration file {file_path}")
        except Exception as e:
            logger.error(f"Failed to create configuration file {file_path}: {e}")
