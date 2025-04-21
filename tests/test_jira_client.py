"""Tests for jira_client.py"""
import pytest
from unittest.mock import Mock, patch
from src.jira_client import JiraClient

@pytest.fixture
def mock_jira():
    with patch('jira.JIRA') as mock:
        yield mock

@pytest.fixture
def jira_client(mock_jira):
    config = {
        'server': 'https://test.atlassian.net',
        'username': 'test@example.com',
        'password': 'api_token',
        'project_key': 'TEST'
    }
    return JiraClient(config)

# Connection Tests
def test_connect_success(jira_client, mock_jira):
    """Test successful connection with valid project"""
    # Create a mock client instance
    mock_client = Mock()
    mock_client.project.return_value = {"key": "TEST"}
    mock_jira.return_value = mock_client
    
    # Test connection
    assert jira_client.connect() is True
    
    # Verify JIRA was initialized correctly
    mock_jira.assert_called_once_with(
        server=jira_client.server,
        basic_auth=(jira_client.username, jira_client.password)
    )
    mock_client.project.assert_called_once_with(jira_client.project_key)

def test_connect_invalid_credentials(jira_client, mock_jira):
    """Test connection failure with invalid credentials"""
    mock_jira.side_effect = Exception("Invalid credentials")
    assert jira_client.connect() is False

def test_connect_nonexistent_project(jira_client, mock_jira):
    """Test connection failure with nonexistent project"""
    mock_jira.return_value.project.side_effect = Exception("Project not found")
    assert jira_client.connect() is False

# Issue Creation Tests
def test_create_issue_success(jira_client, mock_jira):
    """Test basic issue creation"""
    jira_client.client = mock_jira.return_value
    mock_issue = Mock(key='TEST-123')
    mock_jira.return_value.create_issue.return_value = mock_issue
    
    result = jira_client.create_issue(summary='Test', description='Desc')
    assert result == 'TEST-123'
    mock_jira.return_value.create_issue.assert_called_once()

def test_create_issue_with_custom_fields(jira_client, mock_jira):
    """Test issue creation with custom fields"""
    jira_client.client = mock_jira.return_value
    mock_issue = Mock(key='TEST-123')
    mock_jira.return_value.create_issue.return_value = mock_issue
    
    result = jira_client.create_issue(
        summary='Test',
        description='Desc',
        custom_fields={'customfield_123': 'High'}
    )
    assert result == 'TEST-123'
    call_args = mock_jira.return_value.create_issue.call_args[1]['fields']
    assert call_args['customfield_123'] == 'High'

def test_create_issue_invalid_type(jira_client, mock_jira):
    """Test issue creation with invalid issue type"""
    jira_client.client = mock_jira.return_value
    mock_jira.return_value.create_issue.side_effect = Exception("Invalid issue type")
    
    result = jira_client.create_issue(summary='Test', description='Desc', issue_type='Invalid')
    assert result is None

# Attachment Tests
def test_add_attachment_success(jira_client, mock_jira):
    """Test successful attachment upload"""
    jira_client.client = mock_jira.return_value
    assert jira_client.add_attachment('TEST-123', b'test', 'file.txt') is True
    mock_jira.return_value.add_attachment.assert_called_once()

def test_add_attachment_size_limit(jira_client, mock_jira):
    """Test attachment size validation (mock 11MB file)"""
    jira_client.client = mock_jira.return_value
    oversize_data = b'x' * 11 * 1024 * 1024  # 11MB
    assert jira_client.add_attachment('TEST-123', oversize_data, 'large.txt') is False

# Edge Cases
def test_operations_without_connection(jira_client):
    """Test all operations fail when not connected"""
    assert jira_client.create_issue(summary='Test', description='Desc') is None
    assert jira_client.add_attachment('TEST-123', b'test', 'file.txt') is False

# Comment and Metadata Tests
def test_add_comment_success(jira_client, mock_jira):
    """Test adding a comment"""
    jira_client.client = mock_jira.return_value
    assert jira_client.add_comment('TEST-123', 'Test comment') is True
    mock_jira.return_value.add_comment.assert_called_once_with('TEST-123', 'Test comment')

def test_get_project_keys(jira_client, mock_jira):
    """Test project key retrieval"""
    jira_client.client = mock_jira.return_value
    mock_project = Mock(key='TEST')
    mock_jira.return_value.projects.return_value = [mock_project]
    
    assert jira_client.get_project_keys() == ['TEST']

def test_get_issue_types(jira_client, mock_jira):
    """Test issue type retrieval"""
    # Create and configure mock client
    mock_client = Mock()
    mock_type = Mock()
    mock_type.name = "Bug"
    mock_client.issue_types.return_value = [mock_type]
    
    # Simulate successful connection
    jira_client.client = mock_client
    
    assert jira_client.get_issue_types() == ["Bug"]
    mock_client.issue_types.assert_called_once() 