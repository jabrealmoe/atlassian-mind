import pytest
import jwt
from src.app import create_app
from src.config import Config

@pytest.fixture
def client():
    app = create_app()
    return app.test_client()

@pytest.fixture
def auth_header():
    token = jwt.encode({"user": "admin"}, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

def test_story_rewrite_integration(client, auth_header, mocker):
    """
    Integration Test: Story flow with quality score < 60 triggering parallel rewrites.
    """
    # 1. Mock Jira GET (Return a story issue)
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "fields": {"summary": "Vague Story", "description": "Too short"}
    }

    # 2. Mock Ollama Agent responses
    mock_ollama = mocker.patch('ollama.chat')
    mock_ollama.side_effect = [
        # First call: Story analysis (low score)
        {'message': {'content': '{"quality_score": 45}'}},
        # Following 3 calls: Parallel rewrites (Claude, Gemini, GPT)
        {'message': {'content': '{"llm": "Claude", "summary": "Better"} '}},
        {'message': {'content': '{"llm": "Gemini", "summary": "Best"} '}},
        {'message': {'content': '{"llm": "OpenAI", "summary": "Great"} '}}
    ]

    # 3. Mock outgoing Webhook to Forge
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200

    payload = {
        "issueKey": "STORY-99",
        "body": {"issueType": {"name": "Story"}, "issueKey": "STORY-99"}
    }

    response = client.post(
        '/webhook/3a386c57-e834-4b90-81d9-02ddf5bb027d',
        json=payload,
        headers=auth_header
    )

    assert response.status_code == 200
    
    # Verify that we hit the final HTTP Request node (Forge Webhook)
    # This only happens if quality_score < 59
    any_post_is_forge = any(
        Config.FORGE_WEBHOOK_URL in str(call) 
        for call in mock_post.call_args_list
    )
    assert any_post_is_forge, "Forge webhook should have been triggered for low score story"
    
    # Check that parallel rewrites happened (4 total ollama calls: 1 initial + 3 rewrites)
    assert mock_ollama.call_count == 4
