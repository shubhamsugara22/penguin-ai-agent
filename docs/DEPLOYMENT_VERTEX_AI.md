# Deployment Guide: Vertex AI Agent Engine

This guide explains how to deploy the GitHub Maintainer Agent to Google Cloud Vertex AI Agent Engine.

## Overview

Vertex AI Agent Engine provides a managed platform for deploying and running AI agents with built-in orchestration, monitoring, and scaling capabilities. This deployment option is ideal for production workloads requiring enterprise-grade reliability and observability.

## Prerequisites

1. **Google Cloud Account**: Active GCP account with billing enabled
2. **gcloud CLI**: Install and configure the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
3. **Vertex AI API**: Enable Vertex AI API in your project
4. **API Keys**:
   - GitHub Personal Access Token
   - Google Gemini API Key (or use Vertex AI models directly)

## Setup Steps

### 1. Enable Required APIs

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Create Service Account

```bash
# Create service account for the agent
gcloud iam service-accounts create github-maintainer-agent \
    --display-name="GitHub Maintainer Agent" \
    --description="Service account for GitHub Maintainer Agent on Vertex AI"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-maintainer-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-maintainer-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-maintainer-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

### 3. Store Credentials in Secret Manager

```bash
# Create GitHub token secret
echo -n "your_github_token_here" | gcloud secrets create github-token \
    --data-file=- \
    --replication-policy="automatic"

# Create Gemini API key secret (if using AI Studio)
echo -n "your_gemini_api_key_here" | gcloud secrets create gemini-api-key \
    --data-file=- \
    --replication-policy="automatic"

# Grant service account access to secrets
gcloud secrets add-iam-policy-binding github-token \
    --member="serviceAccount:github-maintainer-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:github-maintainer-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 4. Prepare Agent Package

Create an agent configuration file `agent_config.yaml`:

```yaml
# Vertex AI Agent Configuration
name: github-maintainer-agent
display_name: "GitHub Maintainer Agent"
description: "AI-powered multi-agent system for GitHub repository maintenance"

# Agent specification
agent_spec:
  # LLM configuration
  llm:
    model: "gemini-1.5-pro"
    temperature: 0.7
    max_output_tokens: 8192
  
  # Tools configuration
  tools:
    - name: "list_repos"
      description: "List GitHub repositories for a user"
      
    - name: "get_repo_overview"
      description: "Get repository overview including README and structure"
      
    - name: "get_repo_history"
      description: "Get repository commit and issue history"
      
    - name: "create_issue"
      description: "Create a GitHub issue"
  
  # Agent instructions
  instructions: |
    You are the Coordinator Agent for the GitHub Maintainer system.
    Your role is to orchestrate repository analysis, health assessment,
    and maintenance task generation.
    
    Follow these steps:
    1. Retrieve repositories for the specified user
    2. Analyze each repository's structure and health
    3. Generate actionable maintenance suggestions
    4. Create GitHub issues for approved suggestions
    
    Always provide clear, actionable recommendations with proper context.

# Runtime configuration
runtime:
  service_account: "github-maintainer-agent@PROJECT_ID.iam.gserviceaccount.com"
  
  environment_variables:
    LOG_LEVEL: "INFO"
    MAX_PARALLEL_REPOS: "5"
  
  secrets:
    - name: "GITHUB_TOKEN"
      secret_name: "github-token"
      version: "latest"
    
    - name: "GEMINI_API_KEY"
      secret_name: "gemini-api-key"
      version: "latest"
  
  resources:
    cpu: "2"
    memory: "4Gi"
    timeout: "3600s"

# Monitoring configuration
monitoring:
  enable_logging: true
  enable_tracing: true
  log_level: "INFO"
```

### 5. Package and Upload Agent

```bash
# Create agent package directory
mkdir -p agent-package
cd agent-package

# Copy application files
cp -r ../src .
cp -r ../main.py .
cp -r ../requirements.txt .
cp ../agent_config.yaml .

# Create package archive
tar -czf github-maintainer-agent.tar.gz *

# Upload to Cloud Storage
gsutil mb gs://$PROJECT_ID-agent-packages
gsutil cp github-maintainer-agent.tar.gz gs://$PROJECT_ID-agent-packages/

cd ..
```

### 6. Deploy Agent to Vertex AI

#### Using gcloud CLI

```bash
# Deploy the agent
gcloud ai agents deploy github-maintainer-agent \
    --region=us-central1 \
    --package-uri=gs://$PROJECT_ID-agent-packages/github-maintainer-agent.tar.gz \
    --config=agent_config.yaml \
    --service-account=github-maintainer-agent@$PROJECT_ID.iam.gserviceaccount.com
```

#### Using Python SDK

Create `deploy_agent.py`:

```python
from google.cloud import aiplatform

# Initialize Vertex AI
aiplatform.init(
    project="your-project-id",
    location="us-central1"
)

# Deploy agent
agent = aiplatform.Agent.create(
    display_name="GitHub Maintainer Agent",
    description="AI-powered repository maintenance agent",
    agent_package_uri="gs://your-project-id-agent-packages/github-maintainer-agent.tar.gz",
    service_account="github-maintainer-agent@your-project-id.iam.gserviceaccount.com",
    environment_variables={
        "LOG_LEVEL": "INFO",
        "MAX_PARALLEL_REPOS": "5"
    }
)

print(f"Agent deployed: {agent.resource_name}")
```

Run deployment:

```bash
python deploy_agent.py
```

### 7. Create Agent Endpoint

```bash
# Create endpoint for the agent
gcloud ai endpoints create \
    --region=us-central1 \
    --display-name=github-maintainer-endpoint

# Get endpoint ID
ENDPOINT_ID=$(gcloud ai endpoints list \
    --region=us-central1 \
    --filter="displayName:github-maintainer-endpoint" \
    --format="value(name)")

# Deploy agent to endpoint
gcloud ai endpoints deploy-model $ENDPOINT_ID \
    --region=us-central1 \
    --model=github-maintainer-agent \
    --display-name=github-maintainer-v1 \
    --traffic-split=0=100
```

## Usage

### Invoke Agent via API

#### Using REST API

```bash
# Get access token
ACCESS_TOKEN=$(gcloud auth print-access-token)

# Invoke agent
curl -X POST \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    https://us-central1-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/us-central1/endpoints/$ENDPOINT_ID:predict \
    -d '{
      "instances": [{
        "username": "myusername",
        "filters": {
          "language": "Python",
          "updated_after": "2024-01-01"
        },
        "preferences": {
          "automation_level": "manual",
          "focus_areas": ["tests", "docs"]
        }
      }]
    }'
```

#### Using Python SDK

```python
from google.cloud import aiplatform

# Initialize
aiplatform.init(project="your-project-id", location="us-central1")

# Get endpoint
endpoint = aiplatform.Endpoint(endpoint_name=ENDPOINT_ID)

# Make prediction
response = endpoint.predict(
    instances=[{
        "username": "myusername",
        "filters": {
            "language": "Python"
        },
        "preferences": {
            "automation_level": "auto"
        }
    }]
)

print(response.predictions)
```

### Schedule Periodic Runs

Create Cloud Function to trigger agent:

```python
# cloud_function/main.py
from google.cloud import aiplatform
import functions_framework

@functions_framework.http
def trigger_analysis(request):
    """HTTP Cloud Function to trigger agent analysis."""
    
    # Initialize Vertex AI
    aiplatform.init(
        project="your-project-id",
        location="us-central1"
    )
    
    # Get request parameters
    request_json = request.get_json(silent=True)
    username = request_json.get('username', 'default-user')
    
    # Get endpoint
    endpoint = aiplatform.Endpoint(endpoint_name="ENDPOINT_ID")
    
    # Invoke agent
    response = endpoint.predict(
        instances=[{
            "username": username,
            "filters": request_json.get('filters', {}),
            "preferences": request_json.get('preferences', {})
        }]
    )
    
    return {
        "status": "success",
        "results": response.predictions
    }
```

Deploy Cloud Function:

```bash
gcloud functions deploy trigger-github-maintainer \
    --runtime python311 \
    --trigger-http \
    --entry-point trigger_analysis \
    --region us-central1 \
    --service-account github-maintainer-agent@$PROJECT_ID.iam.gserviceaccount.com
```

Schedule with Cloud Scheduler:

```bash
gcloud scheduler jobs create http github-maintainer-weekly \
    --schedule="0 9 * * 1" \
    --uri="https://us-central1-$PROJECT_ID.cloudfunctions.net/trigger-github-maintainer" \
    --http-method=POST \
    --message-body='{"username":"myusername"}' \
    --time-zone="America/New_York"
```

## Monitoring and Observability

### View Agent Logs

```bash
# View logs in Cloud Logging
gcloud logging read "resource.type=aiplatform.googleapis.com/Agent AND resource.labels.agent_id=github-maintainer-agent" \
    --limit 50 \
    --format json
```

### Set Up Monitoring Dashboard

1. Navigate to [Cloud Monitoring](https://console.cloud.google.com/monitoring)
2. Create custom dashboard for agent metrics:
   - Request count
   - Latency
   - Error rate
   - Token usage
   - Success rate

### Configure Alerts

```bash
# Create alert policy for high error rate
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="GitHub Maintainer Agent Errors" \
    --condition-display-name="High Error Rate" \
    --condition-threshold-value=5 \
    --condition-threshold-duration=300s
```

## Advanced Configuration

### Using Vertex AI Models

Modify agent to use Vertex AI models instead of AI Studio:

```python
# src/llm/vertex_client.py
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

class VertexAIClient:
    def __init__(self, project_id: str, location: str = "us-central1"):
        aiplatform.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-1.5-pro")
    
    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text
```

### Enable Private Networking

For GitHub Enterprise or private repositories:

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create github-connector \
    --region=us-central1 \
    --subnet=default \
    --subnet-project=$PROJECT_ID

# Update agent configuration to use VPC
gcloud ai agents update github-maintainer-agent \
    --region=us-central1 \
    --vpc-connector=github-connector
```

### Implement Custom Tools

Register custom tools with Vertex AI:

```python
from google.cloud.aiplatform import Tool

# Define custom tool
github_tool = Tool(
    name="github_api",
    description="GitHub API integration tool",
    parameters={
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "repository": {"type": "string"}
        }
    }
)

# Register tool with agent
agent.add_tool(github_tool)
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Problem**: Agent cannot access GitHub API

**Solution**: Verify secret configuration:

```bash
gcloud secrets versions access latest --secret=github-token
```

#### 2. Timeout Issues

**Problem**: Agent execution times out

**Solution**: Increase timeout in agent config:

```yaml
runtime:
  resources:
    timeout: "7200s"  # 2 hours
```

#### 3. Memory Issues

**Problem**: Out of memory errors

**Solution**: Increase memory allocation:

```yaml
runtime:
  resources:
    memory: "8Gi"
```

## Cost Optimization

### Estimated Monthly Costs

- **Vertex AI Agent Runtime**: $0.10 per hour
- **Gemini API Calls**: $0.00025 per 1K characters
- **Secret Manager**: $0.06 per secret
- **Cloud Storage**: $0.02 per GB
- **Cloud Logging**: First 50GB free

### Cost Reduction Tips

1. Use batch processing for multiple repositories
2. Implement caching for repository profiles
3. Use Vertex AI models (included in runtime cost)
4. Schedule runs during off-peak hours
5. Set appropriate timeout values

## Security Best Practices

1. **Use Service Accounts**: Dedicated service account with minimal permissions
2. **Secret Manager**: Store all credentials securely
3. **VPC Service Controls**: Restrict API access
4. **Audit Logging**: Enable Cloud Audit Logs
5. **Regular Updates**: Keep dependencies updated
6. **Network Policies**: Use VPC for private resources

## Next Steps

- Implement [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines) for complex workflows
- Set up [Vertex AI Experiments](https://cloud.google.com/vertex-ai/docs/experiments) for A/B testing
- Configure [Vertex AI Feature Store](https://cloud.google.com/vertex-ai/docs/featurestore) for caching
- Implement [Vertex AI Model Monitoring](https://cloud.google.com/vertex-ai/docs/model-monitoring)

## Additional Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Vertex AI Agent Engine Guide](https://cloud.google.com/vertex-ai/docs/agents)
- [Vertex AI Python SDK](https://cloud.google.com/python/docs/reference/aiplatform/latest)
- [Best Practices for Vertex AI](https://cloud.google.com/vertex-ai/docs/best-practices)
