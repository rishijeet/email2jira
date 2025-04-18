"""
Jira client module for the Email2Jira framework.
This module handles connecting to Jira and creating issues.
"""

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
                - server: Jira server URL
                - username: Jira username
                - password: Jira password or API token
                - project_key: Default Jira project key
                - issue_type: Default issue type (default: 'Story')
        """
        self.server = config.get('server')
        self.username = config.get('username')
        self.password = config.get('password')
        self.project_key = config.get('project_key')
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
            # Test connection by getting server info
            self.client.server_info()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Jira server: {e}")
            return False
    
    def disconnect(self) -> None:
        """
        Disconnect from the Jira server.
        """
        # JIRA library doesn't have an explicit disconnect method
        # Just set the client to None
        self.client = None
    
    def create_issue(self, 
                     summary: str, 
                     description: str, 
                     project_key: Optional[str] = None,
                     issue_type: Optional[str] = None,
                     labels: Optional[List[str]] = None,
                     components: Optional[List[str]] = None,
                     priority: Optional[str] = None,
                     assignee: Optional[str] = None,
                     additional_fields: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a Jira issue.
        
        Args:
            summary: Issue summary
            description: Issue description
            project_key: Project key (if None, uses default)
            issue_type: Issue type (if None, uses default)
            labels: List of labels to add to the issue
            components: List of component names to add to the issue
            priority: Priority name
            assignee: Username of the assignee
            additional_fields: Additional fields to set on the issue
            
        Returns:
            str: Issue key if successful, None otherwise
        """
        if not self.client:
            logger.error("Not connected to Jira server")
            return None
            
        try:
            # Prepare issue fields
            fields = {
                'project': {'key': project_key or self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type or self.issue_type}
            }
            
            # Add optional fields if provided
            if labels:
                fields['labels'] = labels
                
            if components:
                fields['components'] = [{'name': component} for component in components]
                
            if priority:
                fields['priority'] = {'name': priority}
                
            if assignee:
                fields['assignee'] = {'name': assignee}
                
            # Add any additional fields
            if additional_fields:
                fields.update(additional_fields)
            
            # Create the issue
            issue = self.client.create_issue(fields=fields)
            logger.info(f"Created Jira issue {issue.key}")
            return issue.key
        except Exception as e:
            logger.error(f"Failed to create Jira issue: {e}")
            return None
    
    def add_attachment(self, issue_key: str, attachment_data: bytes, filename: str) -> bool:
        """
        Add an attachment to a Jira issue.
        
        Args:
            issue_key: Key of the issue to add the attachment to
            attachment_data: Binary data of the attachment
            filename: Name of the attachment file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            logger.error("Not connected to Jira server")
            return False
            
        try:
            self.client.add_attachment(issue_key, attachment_data, filename)
            logger.info(f"Added attachment {filename} to issue {issue_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to add attachment to issue {issue_key}: {e}")
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
