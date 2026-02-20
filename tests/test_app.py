import pytest
import jwt
from src.app import create_app
from src.config import Config

@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_header():
    token = jwt.encode({"user": "test"}, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

def test_webhook_unauthorized(client):
    response = client.post('/webhook/3a386c57-e834-4b90-81d9-02ddf5bb027d')
    assert response.status_code == 401

def test_webhook_success_routing(client, auth_header, mocker):
    # Mock WorkflowManager to avoid real LLM/Jira calls
    mock_run = mocker.patch('src.workflow.WorkflowManager.run')
    mock_run.return_value = {"status": "mocked"}
    
    payload = {
        "issueKey": "PROJ-123",
        "body": {"issueType": {"name": "Task"}}
    }
    
    response = client.post(
        '/webhook/3a386c57-e834-4b90-81d9-02ddf5bb027d',
        json=payload,
        headers=auth_header
    )
    
    assert response.status_code == 200
    mock_run.assert_called_once()
