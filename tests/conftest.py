import pytest
import os
from unittest.mock import patch
from src.config import Config

@pytest.fixture(autouse=True)
def mock_config():
    """Ensure all tests use consistent mock configuration values."""
    with patch.object(Config, 'JWT_SECRET', 'testsecret'), \
         patch.object(Config, 'JWT_ALGORITHM', 'HS256'), \
         patch.object(Config, 'FORGE_WEBHOOK_URL', 'https://forge.test.com'), \
         patch.object(Config, 'JIRA_BASE_URL', 'https://test.atlassian.net'):
        yield
