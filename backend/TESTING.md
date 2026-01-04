# DesignSensei Unit Tests

## Overview
Unit tests for SoftwareDesignSensei chatbot system covering all major components.

## Test Structure

```
backend/
├── core/
│   └── tests/
│       ├── __init__.py
│       ├── test_chatbot_views.py    # Chatbot API and message processing
│       ├── test_auth_views.py       # Authentication and password reset
│       ├── test_feedback_views.py   # Feedback submission and admin
│       └── test_models.py           # Database models
└── prompt_engine/
    └── tests.py                      # Intent classification
```

## Running Tests

### Run All Tests
```bash
cd backend
python manage.py test
```

### Run Specific Test Module
```bash
# Test chatbot views only
python manage.py test core.tests.test_chatbot_views

# Test authentication only
python manage.py test core.tests.test_auth_views

# Test intent classifier
python manage.py test prompt_engine.tests
```

## Test Coverage

### Core Module Tests

#### 1. Chatbot Views (`test_chatbot_views.py`)
- Authentication requirements
- Message content validation
- New conversation creation
- Existing conversation message handling
- Out-of-scope question detection
- Response regeneration
- Conversation title generation
- Intent classification (explanation, comparison, application, analysis, troubleshooting)
- Topic detection (design patterns, SOLID, architecture, DDD)
- LLM_ONLY mode processing

#### 2. Authentication Views (`test_auth_views.py`)
- User registration
- Password validation (mismatch, weak password)
- Duplicate username/email handling
- User login
- Invalid credentials
- User logout
- Password reset token creation
- Token expiry validation
- Token usage tracking

#### 3. Feedback Views (`test_feedback_views.py`)
- Authenticated feedback submission
- Anonymous feedback submission
- Feedback type choices (bug, feature, general)
- Missing comment validation
- Rating system (0-5 stars)
- Admin access control
- Regular user access denial
- Feedback deletion (admin only)
- Feedback display format
- CSV export data format

#### 4. Models (`test_models.py`)
- Conversation creation and updates
- Message creation (user/bot)
- Message metadata storage
- Feedback with user/anonymous
- Evaluation record creation
- Ground truth management
- Password reset token lifecycle
- Model string representations
- Timestamp auto-updates

### Prompt Engine Tests

#### Intent Classifier (`tests.py`)
- Explanation questions ("What is...", "Explain...")
- Comparison questions ("difference", "vs", "compare")
- Application questions ("How to...", "example")
- Analysis questions ("pros/cons", "evaluate")
- Troubleshooting questions ("error", "fix", "problem")
- Greeting detection ("Hi", "Hello")
- Out-of-scope detection (food, weather, entertainment)
- Topic classification (patterns, principles, architecture, DDD)
- Confidence score calculation
- Keyword extraction
- Search parameters generation
- Fallback handling

## Test Data Setup

Tests use Django's TestCase which:
- Creates a test database
- Runs each test in a transaction
- Rolls back after each test (clean slate)
- No impact on production/development data

## Mocking External Services

Tests mock external dependencies:
- **OpenAI API**: Mocked for LLM responses
- **Neo4j Database**: Mocked for graph searches
- **Email Service**: Mocked for password reset
- **File System**: Mocked for file operations

Example:
```python
@patch('core.views.chatbot_views.client')
def test_llm_response(self, mock_client):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='Test'))]
    mock_client.chat.completions.create.return_value = mock_response
    # ... test code
```