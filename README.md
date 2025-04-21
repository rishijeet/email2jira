# Email2Jira

![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)
![Tests](https://github.com/rishijeet/email2jira/actions/workflows/test.yml/badge.svg)
![Coverage](https://codecov.io/gh/rishijeet/email2jira/branch/main/graph/badge.svg)

A Python tool to automatically convert emails into Jira tickets with attachment handling.

## Features
- 📧 IMAP email reading with SSL support
- 🛠️ Configurable email parsing rules
- 🎫 Jira ticket creation with custom fields
- 📎 Attachment handling (saved to disk)
- ⚙️ YAML/ENV configuration

## Installation
```bash
git clone https://github.com/rishijeet/email2jira.git
cd email2jira
pip install -r requirements.txt
```

## Configuration
1. Copy the example config files:
```bash
cp config/email.yaml.example config/email.yaml
cp config/jira.yaml.example config/jira.yaml
```
2. Update with your credentials and settings

## Usage
```python
from email2jira import Email2Jira

app = Email2Jira()
if app.initialize():
    app.run(max_emails=5)  # Process 5 unread emails
```

## Testing
Run the test suite with coverage:
```bash
pytest tests/ --cov=src -v
```

## Workflow
1. Connects to email server
2. Fetches unread emails
3. Parses into Jira ticket format
4. Creates tickets with attachments
5. Marks emails as read

## Requirements
- Python 3.8+
- Jira API access
- IMAP-enabled email account 