import logging
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from src.config import Config
from src.jira_client import JiraClient
from src.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class WorkflowManager:
    def __init__(self):
        self.jira = JiraClient()
        self.llm = OllamaClient()

    def run(self, data):
        """Entry point for the workflow logic"""
        # Node: Code4 (Logging)
        logger.info(f"Processing Issue: {data.get('issueKey')}")
        
        body = data.get('body', {})
        issue_type = body.get('issueType', {}).get('name', '')
        
        if issue_type == "Story":
            return self.handle_story_flow(body.get('issueKey'))
        else:
            return self.handle_standard_flow(body)

    def handle_standard_flow(self, body):
        """Handles Task, Incident, and Service Request branches"""
        issue_type = body.get('issueType', {}).get('name', '')
        issue_key = body.get('issueKey')
        
        # Mapping of type to specific system messages from the n8n JSON
        agent_config = {
            "Task": {
                "system": "You are an expert in banking technology... Return VALID JSON ONLY with quality_score and suggestions.",
                "prefix": "Validate this TASK for Financial Industry business software"
            },
            "[System] Incident": {
                "system": "You are an expert in incident management... Return VALID JSON ONLY with quality_score and suggestions.",
                "prefix": "Validate this INCIDENT for WIM"
            },
            "[System] Service request": {
                "system": "You are an expert WIM analyst... Return VALID JSON ONLY with quality_score and suggestions.",
                "prefix": "Validate this SERVICE REQUEST for WIM"
            }
        }

        cfg = agent_config.get(issue_type)
        if not cfg:
            logger.warning(f"Unknown issue_type: {issue_type}")
            return None

        prompt = f"{cfg['prefix']}:\nSummary: {body.get('summary')}\nDescription: {body.get('description', 'None')}"
        result = self.llm.call_agent(cfg['system'], prompt)
        
        # Ensure result is a dict before accessing
        if not isinstance(result, dict):
            logger.error(f"LLM did not return JSON for {issue_type}: {result}")
            result = {"quality_score": "N/A", "suggestions": {}}

        comment = f"Quality Score: {result.get('quality_score', 'N/A')}/100"
        self.jira.add_comment(issue_key, comment)
        return result

    def handle_story_flow(self, issue_key):
        """The specialized Story branch with parallel rewrites"""
        issue_data = self.jira.get_issue(issue_key)
        
        system_msg = "You are a Story Agent. Return VALID JSON ONLY with quality_score."
        prompt = f"Evaluate this Story: {json.dumps(issue_data.get('fields', {}))}"
        
        result = self.llm.call_agent(system_msg, prompt)
        
        # Ensure result is a dict
        if not isinstance(result, dict):
            result = {"quality_score": 0}

        quality_score = result.get('quality_score', 0)
        
        if quality_score < 59:
            self.execute_parallel_rewrites(issue_key, issue_data)
        else:
            self.jira.add_comment(issue_key, f"Story quality score: {quality_score}/100")
            
        return result

    def execute_parallel_rewrites(self, issue_key, issue_data):
        def rewrite(model_name):
            sys = f"Rewrite this issue as {model_name}..."
            return self.llm.call_agent(sys, str(issue_data['fields']))

        with ThreadPoolExecutor(max_workers=3) as executor:
            names = ["Claude", "Gemini", "GPT-Mini"]
            results = list(executor.map(rewrite, names))

        payload = {
            "key": issue_key,
            "suggestions": [{"llm": n, "content": r} for n, r in zip(names, results)]
        }
        
        # HTTP Request node
        requests.post(Config.FORGE_WEBHOOK_URL, json=payload)
