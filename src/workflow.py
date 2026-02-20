import logging
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from src.config import Config
from src.jira_client import JiraClient
from src.ollama_client import OllamaClient
from src.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

class WorkflowManager:
    def __init__(self):
        self.jira = JiraClient()
        self.llm = OllamaClient()
        self.prompt_loader = PromptLoader()

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
        
        cfg = self.prompt_loader.get_agent_config(issue_type)
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
        """The specialized Story branch (Dr. Jira Quality Agent) with parallel rewrites"""
        issue_data = self.jira.get_issue(issue_key)
        
        cfg = self.prompt_loader.get_agent_config("Story")
        if not cfg:
            logger.error("Story Agent configuration missing")
            return {"quality_score": 0}

        prompt = f"{cfg['prefix']}\n{json.dumps(issue_data.get('fields', {}))}"
        result = self.llm.call_agent(cfg['system'], prompt)
        
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
        def rewrite(name, cfg):
            prefix = cfg['prefix']
            system_msg = cfg['system']
            prompt = f"{prefix}\nIssue Key: {issue_key}\nCurrent Summary: {issue_data['fields'].get('summary')}\nCurrent Description: {issue_data['fields'].get('description')}"
            return self.llm.call_agent(system_msg, prompt)

        configs = self.prompt_loader.get_parallel_configs()

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_name = {executor.submit(rewrite, name, cfg): name for name, cfg in configs.items()}
            results = []
            for future in future_to_name:
                name = future_to_name[future]
                try:
                    res = future.result()
                    results.append({"llm": name, "content": res})
                except Exception as exc:
                    logger.error(f'{name} generated an exception: {exc}')

        payload = {
            "key": issue_key,
            "suggestions": results
        }
        
        # HTTP Request node
        requests.post(Config.FORGE_WEBHOOK_URL, json=payload)

