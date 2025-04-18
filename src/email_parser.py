"""
Email parser module for the Email2Jira framework.
This module handles parsing email content and converting it to Jira story format.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class EmailParser:
    """
    A class to handle email parsing and conversion to Jira story format.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the EmailParser with configuration.
        
        Args:
            config: A dictionary containing parser configuration:
                - subject_prefix: Prefix to add to the Jira issue summary (default: '')
                - default_issue_type: Default issue type if not detected (default: 'Story')
                - default_priority: Default priority if not detected (default: 'Medium')
                - custom_patterns: Dictionary of custom regex patterns for extracting fields
                - field_mappings: Dictionary mapping email fields to Jira fields
        """
        self.subject_prefix = config.get('subject_prefix', '')
        self.default_issue_type = config.get('default_issue_type', 'Story')
        self.default_priority = config.get('default_priority', 'Medium')
        self.custom_patterns = config.get('custom_patterns', {})
        self.field_mappings = config.get('field_mappings', {})
        
        # Default patterns for extracting information from emails
        self.default_patterns = {
            'issue_type': r'(?i)type:\s*(\w+)',
            'priority': r'(?i)priority:\s*(\w+)',
            'components': r'(?i)components?:\s*([\w\s,]+)',
            'labels': r'(?i)labels?:\s*([\w\s,\-]+)',
            'assignee': r'(?i)assignee:\s*([\w\.\-@]+)'
        }
        
        # Combine default patterns with custom patterns
        self.patterns = {**self.default_patterns, **self.custom_patterns}
    
    def parse_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse an email and convert it to Jira issue data.
        
        Args:
            email_data: Email data dictionary from EmailReader
            
        Returns:
            Dictionary containing Jira issue data
        """
        # Initialize Jira issue data
        jira_data = {
            'summary': self._get_summary(email_data),
            'description': self._get_description(email_data),
            'issue_type': self.default_issue_type,
            'priority': self.default_priority,
            'labels': [],
            'components': [],
            'assignee': None,
            'attachments': email_data.get('attachments', [])
        }
        
        # Extract fields from email body
        body = email_data.get('body', '')
        
        # Extract issue type
        issue_type = self._extract_field(body, 'issue_type')
        if issue_type:
            jira_data['issue_type'] = issue_type
            
        # Extract priority
        priority = self._extract_field(body, 'priority')
        if priority:
            jira_data['priority'] = priority
            
        # Extract components
        components = self._extract_list_field(body, 'components')
        if components:
            jira_data['components'] = components
            
        # Extract labels
        labels = self._extract_list_field(body, 'labels')
        if labels:
            jira_data['labels'] = labels
            
        # Extract assignee
        assignee = self._extract_field(body, 'assignee')
        if assignee:
            jira_data['assignee'] = assignee
            
        # Apply any custom field mappings
        jira_data = self._apply_field_mappings(email_data, jira_data)
        
        return jira_data
    
    def _get_summary(self, email_data: Dict[str, Any]) -> str:
        """
        Get the Jira issue summary from the email subject.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Jira issue summary
        """
        subject = email_data.get('subject', 'No Subject')
        if self.subject_prefix:
            return f"{self.subject_prefix} {subject}"
        return subject
    
    def _get_description(self, email_data: Dict[str, Any]) -> str:
        """
        Get the Jira issue description from the email body.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Jira issue description
        """
        # Prefer plain text body, fall back to HTML if needed
        body = email_data.get('body', '')
        if not body and email_data.get('html_body'):
            # TODO: Convert HTML to plain text if needed
            body = email_data.get('html_body', '')
            
        # Clean up the body
        body = self._clean_body(body)
        
        # Add sender information
        sender = email_data.get('sender', 'Unknown')
        date = email_data.get('date', 'Unknown')
        
        description = f"""
From: {sender}
Date: {date}

{body}
"""
        return description
    
    def _clean_body(self, body: str) -> str:
        """
        Clean up the email body for use in a Jira description.
        
        Args:
            body: Email body text
            
        Returns:
            Cleaned body text
        """
        # Remove any field markers that we've extracted
        for pattern_name, pattern in self.patterns.items():
            body = re.sub(pattern, '', body)
            
        # Remove email signature (simple heuristic)
        signature_markers = [
            '\n-- \n',
            '\nRegards,',
            '\nBest regards,',
            '\nThanks,',
            '\nThank you,',
            '\nCheers,'
        ]
        
        for marker in signature_markers:
            if marker in body:
                body = body.split(marker)[0]
                
        # Remove quoted replies (simple heuristic)
        quoted_markers = [
            '\nOn ',
            '\n> ',
            '\n-----Original Message-----'
        ]
        
        for marker in quoted_markers:
            if marker in body:
                body = body.split(marker)[0]
                
        # Remove extra whitespace
        body = re.sub(r'\n{3,}', '\n\n', body)
        body = body.strip()
        
        return body
    
    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Extract a field value from text using regex.
        
        Args:
            text: Text to extract from
            field_name: Name of the field to extract
            
        Returns:
            Extracted field value or None if not found
        """
        if not text:
            return None
            
        pattern = self.patterns.get(field_name)
        if not pattern:
            return None
            
        match = re.search(pattern, text)
        if match and match.group(1):
            return match.group(1).strip()
            
        return None
    
    def _extract_list_field(self, text: str, field_name: str) -> List[str]:
        """
        Extract a comma-separated list field from text.
        
        Args:
            text: Text to extract from
            field_name: Name of the field to extract
            
        Returns:
            List of extracted values
        """
        value = self._extract_field(text, field_name)
        if not value:
            return []
            
        # Split by comma and strip whitespace
        items = [item.strip() for item in value.split(',')]
        # Remove empty items
        items = [item for item in items if item]
        
        return items
    
    def _apply_field_mappings(self, email_data: Dict[str, Any], jira_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply custom field mappings from email data to Jira data.
        
        Args:
            email_data: Email data dictionary
            jira_data: Jira data dictionary
            
        Returns:
            Updated Jira data dictionary
        """
        for email_field, jira_field in self.field_mappings.items():
            if email_field in email_data and email_data[email_field]:
                jira_data[jira_field] = email_data[email_field]
        
        return jira_data
