"""
Email reader module for the Email2Jira framework.
This module handles connecting to email servers and retrieving emails.
"""

import imaplib
import email
from email.header import decode_header
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmailReader:
    """
    A class to handle email reading operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the EmailReader with configuration.
        
        Args:
            config: A dictionary containing email configuration:
                - server: IMAP server address
                - port: IMAP server port
                - username: Email account username
                - password: Email account password
                - use_ssl: Whether to use SSL for connection
                - mailbox: Mailbox to read from (default: 'INBOX')
        """
        self.server = config.get('server')
        self.port = config.get('port', 993)
        self.username = config.get('username')
        self.password = config.get('password')
        self.use_ssl = config.get('use_ssl', True)
        self.mailbox = config.get('mailbox', 'INBOX')
        self.connection = None
        
    def connect(self) -> bool:
        """
        Connect to the email server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.server, self.port)
            else:
                self.connection = imaplib.IMAP4(self.server, self.port)
                
            self.connection.login(self.username, self.password)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False
    
    def disconnect(self) -> None:
        """
        Disconnect from the email server.
        """
        if self.connection:
            try:
                self.connection.logout()
            except Exception as e:
                logger.error(f"Error during logout: {e}")
            finally:
                self.connection = None
    
    def select_mailbox(self, mailbox: Optional[str] = None) -> bool:
        """
        Select a mailbox to read from.
        
        Args:
            mailbox: Name of the mailbox to select. If None, uses the default mailbox.
            
        Returns:
            bool: True if mailbox selection successful, False otherwise
        """
        if not self.connection:
            logger.error("Not connected to email server")
            return False
            
        try:
            mailbox_to_select = mailbox or self.mailbox
            status, data = self.connection.select(mailbox_to_select)
            return status == 'OK'
        except Exception as e:
            logger.error(f"Failed to select mailbox {mailbox_to_select}: {e}")
            return False
    
    def get_unread_emails(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get unread emails from the selected mailbox.
        
        Args:
            limit: Maximum number of emails to retrieve
            
        Returns:
            List of email dictionaries with keys:
                - id: Email ID
                - subject: Email subject
                - sender: Email sender
                - date: Email date
                - body: Email body (text)
                - html_body: Email HTML body (if available)
                - attachments: List of attachments
        """
        if not self.connection:
            logger.error("Not connected to email server")
            return []
            
        try:
            status, data = self.connection.search(None, 'UNSEEN')
            if status != 'OK':
                logger.error("Failed to search for unread emails")
                return []
                
            email_ids = data[0].split()
            if not email_ids:
                logger.info("No unread emails found")
                return []
                
            # Limit the number of emails to process
            email_ids = email_ids[:limit]
            
            emails = []
            for email_id in email_ids:
                status, data = self.connection.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    logger.error(f"Failed to fetch email {email_id}")
                    continue
                    
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                # Parse email
                email_data = self._parse_email(email_message)
                email_data['id'] = email_id.decode('utf-8')
                emails.append(email_data)
                
            return emails
        except Exception as e:
            logger.error(f"Error retrieving unread emails: {e}")
            return []
    
    def mark_as_read(self, email_id: str) -> bool:
        """
        Mark an email as read.
        
        Args:
            email_id: ID of the email to mark as read
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection:
            logger.error("Not connected to email server")
            return False
            
        try:
            status, data = self.connection.store(email_id.encode(), '+FLAGS', '\\Seen')
            return status == 'OK'
        except Exception as e:
            logger.error(f"Error marking email {email_id} as read: {e}")
            return False
    
    def _parse_email(self, email_message: email.message.Message) -> Dict[str, Any]:
        """
        Parse an email message into a dictionary.
        
        Args:
            email_message: The email message to parse
            
        Returns:
            Dictionary containing email data
        """
        email_data = {
            'subject': '',
            'sender': '',
            'date': '',
            'body': '',
            'html_body': '',
            'attachments': []
        }
        
        # Get subject
        subject = email_message.get('Subject', '')
        if subject:
            # Decode subject if needed
            decoded_subject = decode_header(subject)
            if decoded_subject[0][1]:
                # If the subject is encoded
                email_data['subject'] = decoded_subject[0][0].decode(decoded_subject[0][1])
            else:
                # If the subject is not encoded
                if isinstance(decoded_subject[0][0], bytes):
                    email_data['subject'] = decoded_subject[0][0].decode('utf-8', errors='ignore')
                else:
                    email_data['subject'] = decoded_subject[0][0]
        
        # Get sender
        sender = email_message.get('From', '')
        if sender:
            email_data['sender'] = sender
        
        # Get date
        date = email_message.get('Date', '')
        if date:
            email_data['date'] = date
        
        # Get body and attachments
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))
                
                # Skip multipart containers
                if content_type == 'multipart/alternative':
                    continue
                
                # Handle attachments
                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        # Decode filename if needed
                        decoded_filename = decode_header(filename)
                        if decoded_filename[0][1]:
                            filename = decoded_filename[0][0].decode(decoded_filename[0][1])
                        elif isinstance(decoded_filename[0][0], bytes):
                            filename = decoded_filename[0][0].decode('utf-8', errors='ignore')
                        
                        attachment_data = {
                            'filename': filename,
                            'content': part.get_payload(decode=True)
                        }
                        email_data['attachments'].append(attachment_data)
                # Handle text body
                elif content_type == 'text/plain':
                    body = part.get_payload(decode=True)
                    if body:
                        charset = part.get_content_charset() or 'utf-8'
                        email_data['body'] = body.decode(charset, errors='ignore')
                # Handle HTML body
                elif content_type == 'text/html':
                    html_body = part.get_payload(decode=True)
                    if html_body:
                        charset = part.get_content_charset() or 'utf-8'
                        email_data['html_body'] = html_body.decode(charset, errors='ignore')
        else:
            # Not multipart - get the content
            content_type = email_message.get_content_type()
            body = email_message.get_payload(decode=True)
            if body:
                charset = email_message.get_content_charset() or 'utf-8'
                decoded_body = body.decode(charset, errors='ignore')
                if content_type == 'text/plain':
                    email_data['body'] = decoded_body
                elif content_type == 'text/html':
                    email_data['html_body'] = decoded_body
        
        return email_data
