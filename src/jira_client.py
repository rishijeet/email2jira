"""
Jira client module for the Email2Jira framework.
This module handles connecting to Jira and creating issues.
"""
__author__ = "Rishijeet"

import logging
from typing import Dict, Any, Optional, List
from jira import JIRA

logger = logging.getLogger(__name__)

class JiraClient:
    """
    A class to handle Jira operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the JiraClient with configuration.
        
        Args:
            config: A dictionary containing Jira configuration:
                - server: Jira server URL (required)
                - username: Jira username (required)
                - password: Jira password or API token (required)
                - project_key: Default Jira project key (required)
                - issue_type: Default issue type (default: 'Story')
        """
        required_fields = ['server', 'username', 'password', 'project_key']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required configuration field: {field}")
                
        self.server = config['server']
        self.username = config['username']
        self.password = config['password']
        self.project_key = config['project_key']
        self.issue_type = config.get('issue_type', 'Story')
        self.client = None
        
    def connect(self) -> bool:
        """
        Connect to the Jira server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = JIRA(
                server=self.server,
                basic_auth=(self.username, self.password)
            )
            # Validate project exists
            self.client.project(self.project_key)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Jira server: {e}")
            return False
    
    def disconnect(self) -> None:
        """
        Disconnect from the Jira server.
        """
        self.client = None
    
    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Create a Jira issue.
        
        Args:
            custom_fields: Dictionary of custom field IDs to values.
                          Example: {'customfield_123': 'High'}
        """
        if not self.client:
            logger.error("Not connected to Jira server")
            return None
            
        try:
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type or self.issue_type},
                **kwargs
            }
            if custom_fields:
                issue_dict.update(custom_fields)
                
            issue = self.client.create_issue(fields=issue_dict)
            return issue.key
        except Exception as e:
            logger.error(f"Failed to create Jira issue: {e}")
            return None
    
    def add_attachment(self, issue_key: str, attachment_data: bytes, filename: str) -> bool:
        """
        Add an attachment to a Jira issue.
        
        Args:
            issue_key: Key of the Jira issue (e.g., 'PROJ-123')
            attachment_data: Binary content of the attachment
            filename: Name of the attachment file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            logger.error("Not connected to Jira server")
            return False
            
        try:
            self.client.add_attachment(issue_key, attachment=attachment_data, filename=filename)
            return True
        except Exception as e:
            logger.error(f"Failed to add attachment to {issue_key}: {e}")
            return False
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """
        Add a comment to a Jira issue.
        
        Args:
            issue_key: Key of the issue to add the comment to
            comment: Comment text
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            logger.error("Not connected to Jira server")
            return False
            
        try:
            self.client.add_comment(issue_key, comment)
            logger.info(f"Added comment to issue {issue_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to add comment to issue {issue_key}: {e}")
            return False
    
    def get_project_keys(self) -> List[str]:
        """
        Get a list of available project keys.
        
        Returns:
            List of project keys
        """
        if not self.client:
            logger.error("Not connected to Jira server")
            return []
            
        try:
            projects = self.client.projects()
            return [project.key for project in projects]
        except Exception as e:
            logger.error(f"Failed to get project keys: {e}")
            return []
    
    def get_issue_types(self) -> List[str]:
        """
        Get a list of available issue types.
        
        Returns:
            List of issue type names
        """
        if not self.client:
            logger.error("Not connected to Jira server")
            return []
            
        try:
            issue_types = self.client.issue_types()
            return [issue_type.name for issue_type in issue_types]
        except Exception as e:
            logger.error(f"Failed to get issue types: {e}")
            return []
