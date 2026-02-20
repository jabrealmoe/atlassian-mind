import pytest
from src.workflow import WorkflowManager

def test_workflow_task_routing(mocker):
    # Setup mocks
    mock_jira = mocker.patch('src.workflow.JiraClient')
    mock_llm = mocker.patch('src.workflow.OllamaClient.call_agent')
    mock_llm.return_value = {"quality_score": 85}
    
    manager = WorkflowManager()
    
    data = {
        "issueKey": "BT-1",
        "body": {
            "issueType": {"name": "Task"},
            "summary": "Fix login bug",
            "issueKey": "BT-1"
        }
    }
    
    manager.run(data)
    
    # Verify LLM was called with Task prompt
    assert "enterprise" in mock_llm.call_args[0][0].lower()
    # Verify Jira comment was added
    mock_jira.return_value.add_comment.assert_called_with("BT-1", "Quality Score: 85/100")

def test_story_flow_low_score_triggers_parallel(mocker):
    mock_jira = mocker.patch('src.workflow.JiraClient')
    mock_jira.return_value.get_issue.return_value = {"fields": {"summary": "Bad story"}}
    
    # Story agent returns low score
    mock_llm = mocker.patch('src.workflow.OllamaClient.call_agent')
    mock_llm.return_value = {"quality_score": 30}
    
    # Parallel rewrite trigger
    mock_parallel = mocker.patch('src.workflow.WorkflowManager.execute_parallel_rewrites')
    
    manager = WorkflowManager()
    data = {"body": {"issueType": {"name": "Story"}, "issueKey": "STORY-1"}}
    
    manager.run(data)
    
    mock_parallel.assert_called_once()
