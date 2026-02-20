import pytest
import jwt
import json
from src.app import create_app
from src.config import Config

@pytest.fixture
def client():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_header():
    token = jwt.encode({"user": "test_user"}, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

def test_task_flow_integration(client, auth_header, mocker):
    """
    Integration Test: Webhook -> Auth -> Workflow -> LLM -> Jira
    Tests the actual interaction between modules while mocking target APIs.
    """
    # 1. Mock External Layer: Ollama
    mock_ollama = mocker.patch('ollama.chat')
    mock_ollama.return_value = {
        'message': {
            'content': '{"is_valid": true, "quality_score": 92, "suggestions": {"description": "Looks great"}}'
        }
    }

    # 2. Mock External Layer: Jira (Requests)
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 201

    # 3. Simulate Incoming Webhook (The trigger)
    webhook_payload = {
        "issueKey": "PROJ-101",
        "body": {
            "issueType": {"name": "Task"},
            "summary": "Implement feature X",
            "description": "Ensure feature X is scalable",
            "issueKey": "PROJ-101"
        }
    }

    response = client.post(
        '/webhook/3a386c57-e834-4b90-81d9-02ddf5bb027d',
        json=webhook_payload,
        headers=auth_header
    )

    # ASSERTIONS:
    # Check Flask response
    assert response.status_code == 200
    
    # Verify LLM was called with Task prompt
    args, kwargs = mock_ollama.call_args
    assert "enterprise" in kwargs['messages'][0]['content'].lower()
    assert "feature x" in kwargs['messages'][1]['content'].lower()

    # Verify Forge webhook was called with analysis
    forge_call_args = mock_post.call_args
    payload = forge_call_args.kwargs['json']
    assert payload['key'] == "PROJ-101"
    assert payload['analysis']['quality_score'] == 92
