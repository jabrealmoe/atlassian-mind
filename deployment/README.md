# Enterprise Deployment Guide: Azure & GCP

Atlassian Mind is designed to run in secure, private VPCs to ensure Jira data and AI processing (via Ollama) remain within your organizational boundary.

## 1. Google Cloud Platform (GCP)

### Recommended: Google Kubernetes Engine (GKE)

- **Architecture**: Deploy the Flask app as a Deployment and Ollama as a separate GPU-enabled Deployment/StatefulSet.
- **Networking**: Use a **Private GKE Cluster** with an **Internal Load Balancer**. Connect Jira webhooks via a **Cloud NAT** or a VPN/Interconnect if using Jira Data Center.
- **Storage**: Use Filestore for sharing LLM model weights across Ollama nodes.
- **Security**: Use **Workload Identity** to manage access to other GCP resources (like Secret Manager for Jira credentials).

### Simple: Compute Engine with Docker Compose

- Create a VM with an L4 or T4 GPU.
- Install Docker and NVIDIA Container Toolkit.
- Use `docker-compose.yml` to run both services.

---

## 2. Microsoft Azure

### Recommended: Azure Kubernetes Service (AKS)

- **Architecture**: Similar to GKE, utilize **Node Pools with GPUs** (N-series VMs) for Ollama.
- **Networking**: Place AKS in a **Private Virtual Network (VNet)**. Use **Azure Application Gateway** with WAF to expose the webhook endpoint securely.
- **Security**: Use **Azure Key Vault** integrated with **Managed Identity** to store `JIRA_API_TOKEN` and `JWT_SECRET`.
- **Logs**: Stream logs to **Azure Log Analytics** for audit compliance.

### Managed: Azure Container Apps

- Ideal for the Flask backend.
- Connect it to an **Ollama** instance running on a specialized Azure VM via **VNet Peering**.

---

## Environment Variables for Production

Ensure these are set in your platform's Secret Manager:

| Variable            | Source                                         |
| ------------------- | ---------------------------------------------- |
| `JIRA_API_TOKEN`    | Jira Account API Token                         |
| `JWT_SECRET`        | 32+ character random string                    |
| `FORGE_WEBHOOK_URL` | The egress URL for the AI-Suggest Custom Panel |
| `OLLAMA_HOST`       | `http://ollama-service:11434` (Internal DNS)   |
