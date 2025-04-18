"""
Main module for the Email2Jira framework.
This module provides the main application logic for reading emails and creating Jira stories.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, List, Optional

from .config_manager import ConfigManager
from .email_reader import EmailReader
from .jira_client import JiraClient
from .email_parser import EmailParser

logger = logging.getLogger(__name__)

class Email2Jira:
    """
    Main class for the Email2Jira application.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the Email2Jira application.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_manager = ConfigManager(config_dir)
        self.email_reader = None
        self.jira_client = None
        self.email_parser = None
        
    def initialize(self) -> bool:
        """
        Initialize the application components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        # Load configuration
        if not self.config_manager.load_config():
            logger.error("Failed to load configuration")
            return False
            
        # Initialize components
        try:
            # Get configurations
            email_config = self.config_manager.get_email_config()
            jira_config = self.config_manager.get_jira_config()
            parser_config = self.config_manager.get_parser_config()
            
            # Initialize components
            self.email_reader = EmailReader(email_config)
            self.jira_client = JiraClient(jira_config)
            self.email_parser = EmailParser(parser_config)
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    def run(self, max_emails: int = 10, dry_run: bool = False) -> bool:
        """
        Run the Email2Jira process.
        
        Args:
            max_emails: Maximum number of emails to process
            dry_run: If True, don't actually create Jira issues
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Connect to email server
            logger.info("Connecting to email server...")
            if not self.email_reader.connect():
                logger.error("Failed to connect to email server")
                return False
                
            # Select mailbox
            if not self.email_reader.select_mailbox():
                logger.error("Failed to select mailbox")
                self.email_reader.disconnect()
                return False
                
            # Get unread emails
            logger.info(f"Fetching up to {max_emails} unread emails...")
            emails = self.email_reader.get_unread_emails(limit=max_emails)
            
            if not emails:
                logger.info("No unread emails found")
                self.email_reader.disconnect()
                return True
                
            logger.info(f"Found {len(emails)} unread emails")
            
            # Connect to Jira if not in dry run mode
            if not dry_run:
                logger.info("Connecting to Jira server...")
                if not self.jira_client.connect():
                    logger.error("Failed to connect to Jira server")
                    self.email_reader.disconnect()
                    return False
            
            # Process emails
            successful_count = 0
            for email_data in emails:
                try:
                    # Parse email
                    jira_data = self.email_parser.parse_email(email_data)
                    
                    # Log the parsed data
                    logger.info(f"Parsed email: {jira_data['summary']}")
                    
                    if dry_run:
                        # In dry run mode, just log what would be done
                        logger.info(f"[DRY RUN] Would create Jira issue: {jira_data['summary']}")
                        successful_count += 1
                    else:
                        # Create Jira issue
                        issue_key = self.jira_client.create_issue(
                            summary=jira_data['summary'],
                            description=jira_data['description'],
                            issue_type=jira_data['issue_type'],
                            priority=jira_data['priority'],
                            labels=jira_data['labels'],
                            components=jira_data['components'],
                            assignee=jira_data['assignee']
                        )
                        
                        if not issue_key:
                            logger.error(f"Failed to create Jira issue for email: {jira_data['summary']}")
                            continue
                            
                        logger.info(f"Created Jira issue: {issue_key}")
                        
                        # Add attachments
                        for attachment in jira_data['attachments']:
                            self.jira_client.add_attachment(
                                issue_key=issue_key,
                                attachment_data=attachment['content'],
                                filename=attachment['filename']
                            )
                        
                        successful_count += 1
                    
                    # Mark email as read
                    self.email_reader.mark_as_read(email_data['id'])
                    
                except Exception as e:
                    logger.error(f"Error processing email: {e}")
            
            # Disconnect
            self.email_reader.disconnect()
            if not dry_run:
                self.jira_client.disconnect()
                
            logger.info(f"Successfully processed {successful_count} out of {len(emails)} emails")
            return True
            
        except Exception as e:
            logger.error(f"Error running Email2Jira: {e}")
            return False

def setup_logging(level: str = 'INFO', log_file: Optional[str] = None):
    """
    Set up logging configuration.
    
    Args:
        level: Logging level
        log_file: Path to log file (if None, log to console only)
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler if log file specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )

def main():
    """
    Main entry point for the Email2Jira application.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Email2Jira - Convert emails to Jira stories')
    parser.add_argument('--config-dir', help='Path to configuration directory')
    parser.add_argument('--max-emails', type=int, default=10, help='Maximum number of emails to process')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (don\'t create Jira issues)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Logging level')
    parser.add_argument('--log-file', help='Path to log file')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level, args.log_file)
    
    # Create and run the application
    app = Email2Jira(args.config_dir)
    
    if not app.initialize():
        logger.error("Failed to initialize Email2Jira")
        sys.exit(1)
        
    if not app.run(args.max_emails, args.dry_run):
        logger.error("Failed to run Email2Jira")
        sys.exit(1)
        
    logger.info("Email2Jira completed successfully")

if __name__ == '__main__':
    main()
