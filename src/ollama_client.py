import json
import logging
import ollama
from src.config import Config

logger = logging.getLogger(__name__)

class OllamaClient:
    @staticmethod
    def call_agent(system_message, user_prompt, model=None):
        model = model or Config.OLLAMA_MODEL
        try:
            response = ollama.chat(model=model, messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': user_prompt},
            ])
            content = response['message']['content']
            
            if "VALID JSON" in system_message.upper():
                return OllamaClient._parse_json(content)
            return content
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise

    @staticmethod
    def _parse_json(content):
        try:
            # Clean markdown formatting if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            logger.warning("Failed to parse JSON from content, returning as-is.")
            return content
