# Atlassian Mind

Atlassian Mind is an AI-powered facilitation system for Jira, designed to enhance the quality and completeness of Jira issues within enterprise environments. It automates the review process, providing quality scores, actionable suggestions, and intelligent rewrites.

## Features

- **Automated Issue Validation**: Evaluates Tasks, Stories, Incidents, and Service Requests against industry-standard rubrics.
- **Quality Scoring**: Assigns a score from 0-100 based on clarity, scope, business value, technical detail, and risk definition.
- **Intelligent Suggestions**: Provides specific feedback to improve issue descriptions and requirements.
- **Parallel AI Rewrites**: For Stories with low quality scores (<60), the system automatically generates high-quality rewrites using Claude, Gemini, and OpenAI models.
- **Actionable Feedback**: Posts scores and suggestions directly to Jira issues as comments.
- **Customizable Workflows**: Based on a flexible n8n-inspired architecture (defined in `atlassian-mind.json`).

## Project Structure

- `src/`: Core application logic.
  - `app.py`: Flask-based webhook receiver.
  - `workflow.py`: The "brain" of the project, implementing the workflow nodes and logic.
  - `jira_client.py`: Interface for interacting with Jira Cloud API.
  - `ollama_client.py`: Interface for local LLM processing via Ollama.
  - `prompt_loader.py`: Utility for configuration-driven prompt management.
- `tests/`: Comprehensive test suite including integration and unit tests.
- `atlassian-mind.json`: The latest n8n workflow definition that this project implements.

## Getting Started

### Prerequisites

- Python 3.14+
- Ollama (running locally with the required models)
- Jira Cloud credentials (API Token)

### Installation

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables in `.env`:
   ```env
   JIRA_BASE_URL=https://your-domain.atlassian.net
   JIRA_EMAIL=your-email@company.com
   JIRA_API_TOKEN=your-api-token
   FORGE_WEBHOOK_URL=your-forge-webhook-url
   JWT_SECRET=your-secret
   OLLAMA_MODEL=llama3
   ```

### Running the App

```bash
env/bin/python main.py
```

### Running Tests

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
env/bin/pytest --ignore=.vscode --ignore=env --ignore=venv
```

## How It Works

1. **Trigger**: A Jira Cloud event (via Atlassian Forge) sends a webhook to this application.
2. **Analysis**: The `WorkflowManager` routes the issue based on its type to specific AI agents.
3. **Evaluation**: The AI agent evaluates the issue and returns a structured JSON analysis.
4. **Action**:
   - For standard issues, a quality score and suggestion are posted back to Jira.
   - For low-quality Stories, parallel rewrites are triggered and sent to a specialized Forge UI panel.

## License

MIT
