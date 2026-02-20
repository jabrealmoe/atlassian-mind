import requests
from src.config import Config

class JiraClient:
    def __init__(self):
        self.auth = (Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
        self.base_url = Config.JIRA_BASE_URL

    def get_issue(self, issue_key):
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        params = {'expand': 'changelog,renderedFields,names,schema'}
        response = requests.get(url, auth=self.auth, params=params)
        response.raise_for_status()
        return response.json()

    def add_comment(self, issue_key, comment_text):
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        payload = {
            "body": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment_text}]
                    }
                ]
            }
        }
        response = requests.post(url, json=payload, auth=self.auth)
        response.raise_for_status()
        return response.json()
