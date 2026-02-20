import os
import yaml
import logging

logger = logging.getLogger(__name__)

class PromptLoader:
    def __init__(self, config_path=None, prompts_dir=None):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.config_path = config_path or os.path.join(base_dir, "src/config/agents.yaml")
        # Handle absolute path if it was passed as relative to project root
        if not os.path.isabs(self.config_path):
             self.config_path = os.path.join(os.getcwd(), self.config_path)
             
        self.prompts_dir = prompts_dir or os.path.join(base_dir, "src/prompts")
        if not os.path.isabs(self.prompts_dir):
            self.prompts_dir = os.path.join(os.getcwd(), self.prompts_dir)
            
        self.config = self._load_yaml(self.config_path)

    def _load_yaml(self, path):
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load agent config from {path}: {e}")
            return {"issue_types": {}, "parallel_rewriters": {}}

    def get_agent_config(self, issue_type):
        agent_cfg = self.config.get('issue_types', {}).get(issue_type)
        if not agent_cfg:
            return None
        
        prompt_data = self._load_prompt_file(agent_cfg['prompt_file'])
        return {
            "system": prompt_data['content'],
            "prefix": prompt_data['metadata'].get('prefix', "")
        }

    def get_parallel_configs(self):
        configs = {}
        for name, cfg in self.config.get('parallel_rewriters', {}).items():
            prompt_data = self._load_prompt_file(cfg['prompt_file'])
            configs[name] = {
                "system": prompt_data['content'],
                "prefix": prompt_data['metadata'].get('prefix', "")
            }
        return configs

    def _load_prompt_file(self, filename):
        path = os.path.join(self.prompts_dir, filename)
        try:
            with open(path, 'r') as f:
                raw_content = f.read()
            
            # Simple metadata parser for markdown frontmatter
            metadata = {}
            content = raw_content
            if raw_content.startswith('---'):
                parts = raw_content.split('---', 2)
                if len(parts) >= 3:
                    metadata = yaml.safe_load(parts[1])
                    content = parts[2].strip()
            
            return {"metadata": metadata, "content": content}
        except Exception as e:
            logger.error(f"Failed to load prompt file {path}: {e}")
            return {"metadata": {}, "content": ""}
