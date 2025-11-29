# Deployment Guide: Google Cloud Run

This guide explains how to deploy the GitHub Maintainer Agent to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**: Active GCP account with billing enabled
2. **gcloud CLI**: Install and configure the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install [Docker](https://docs.docker.com/get-docker/) for local testing
4. **API Keys**: 
   - GitHub Personal Access Token
   - Google Gemini API Key

## Setup Steps

### 1. Configure gcloud CLI

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 2. Build and Push Docker Image

#### Option A: Using Google Cloud Build

```bash
# Navigate to project directory
cd penguin-ai-agent

# Build and push using Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/github-maintainer-agent:latest

# Or use Artifact Registry (recommended)
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/github-maintainer/agent:latest
```

#### Option B: Using Local Docker

```bash
# Build image locally
docker build -t github-maintainer-agent:latest .

# Tag for GCR
docker tag github-maintainer-agent:latest gcr.io/YOUR_PROJECT_ID/github-maintainer-agent:latest

# Configure Docker to use gcloud credentials
gcloud auth configure-docker

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/github-maintainer-agent:latest
```

### 3. Create Secret Manager Secrets

Store sensitive credentials in Google Secret Manager:

```bash
# Create GitHub token secret
echo -n "your_github_token_here" | gcloud secrets create github-token --data-file=-

# Create Gemini API key secret
echo -n "your_gemini_api_key_here" | gcloud secrets create gemini-api-key --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding github-token \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 4. Deploy to Cloud Run

#### Interactive Deployment

```bash
gcloud run deploy github-maintainer-agent \
    --image gcr.io/YOUR_PROJECT_ID/github-maintainer-agent:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-secrets="GITHUB_TOKEN=github-token:latest,GEMINI_API_KEY=gemini-api-key:latest" \
    --set-env-vars="LOG_LEVEL=INFO,MAX_PARALLEL_REPOS=5" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 10 \
    --min-instances 0
```

#### Using YAML Configuration

Create `cloud-run-service.yaml`:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: github-maintainer-agent
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: '10'
        autoscaling.knative.dev/minScale: '0'
    spec:
      containerConcurrency: 1
      timeoutSeconds: 3600
      containers:
      - image: gcr.io/YOUR_PROJECT_ID/github-maintainer-agent:latest
        resources:
          limits:
            memory: 2Gi
            cpu: '2'
        env:
        - name: LOG_LEVEL
          value: INFO
        - name: MAX_PARALLEL_REPOS
          value: '5'
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: github-token
              key: latest
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-api-key
              key: latest
```

Deploy using YAML:

```bash
gcloud run services replace cloud-run-service.yaml --region us-central1
```

### 5. Invoke the Service

#### Using gcloud CLI

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe github-maintainer-agent \
    --region us-central1 \
    --format 'value(status.url)')

# Invoke analysis (if you've added HTTP endpoint)
curl -X POST $SERVICE_URL/analyze \
    -H "Content-Type: application/json" \
    -d '{"username": "myusername", "filters": {"language": "Python"}}'
```

#### Using Cloud Scheduler (Scheduled Runs)

```bash
# Create a Cloud Scheduler job for periodic analysis
gcloud scheduler jobs create http github-maintainer-weekly \
    --schedule="0 9 * * 1" \
    --uri="$SERVICE_URL/analyze" \
    --http-method=POST \
    --message-body='{"username":"myusername"}' \
    --time-zone="America/New_York"
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Required |
| `GEMINI_API_KEY` | Google Gemini API Key | Required |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `MAX_PARALLEL_REPOS` | Maximum repositories to process in parallel | 5 |
| `GITHUB_API_BASE_URL` | GitHub API base URL | https://api.github.com |

### Resource Configuration

- **Memory**: 2Gi recommended (adjust based on repository size)
- **CPU**: 2 vCPU recommended for parallel processing
- **Timeout**: 3600s (1 hour) for large analyses
- **Concurrency**: 1 (one request per container instance)

## Monitoring and Logging

### View Logs

```bash
# Stream logs
gcloud run services logs tail github-maintainer-agent --region us-central1

# View recent logs
gcloud run services logs read github-maintainer-agent --region us-central1 --limit 50
```

### Set Up Monitoring

1. Navigate to [Cloud Monitoring](https://console.cloud.google.com/monitoring)
2. Create alerts for:
   - High error rates
   - Long execution times
   - Memory usage
   - Request failures

### Enable Cloud Trace

```bash
gcloud run services update github-maintainer-agent \
    --region us-central1 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID"
```

## Troubleshooting

### Common Issues

#### 1. Container Exits Immediately

**Problem**: Container starts but exits without processing

**Solution**: Ensure you're passing the correct command arguments:

```bash
gcloud run services update github-maintainer-agent \
    --region us-central1 \
    --args="analyze,myusername,--automation,auto"
```

#### 2. Secret Access Denied

**Problem**: Cannot access secrets from Secret Manager

**Solution**: Verify IAM permissions:

```bash
# Check service account
gcloud run services describe github-maintainer-agent \
    --region us-central1 \
    --format="value(spec.template.spec.serviceAccountName)"

# Grant secret access
gcloud secrets add-iam-policy-binding github-token \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
```

#### 3. Timeout Errors

**Problem**: Analysis times out before completion

**Solution**: Increase timeout and optimize:

```bash
gcloud run services update github-maintainer-agent \
    --region us-central1 \
    --timeout 3600 \
    --set-env-vars="MAX_PARALLEL_REPOS=10"
```

#### 4. Memory Issues

**Problem**: Container runs out of memory

**Solution**: Increase memory allocation:

```bash
gcloud run services update github-maintainer-agent \
    --region us-central1 \
    --memory 4Gi
```

## Cost Optimization

### Tips to Reduce Costs

1. **Use Minimum Instances**: Set `--min-instances 0` to scale to zero when idle
2. **Optimize Memory**: Start with 1Gi and increase only if needed
3. **Use Artifact Registry**: More cost-effective than Container Registry
4. **Schedule Wisely**: Use Cloud Scheduler for off-peak analysis
5. **Set Request Limits**: Configure `--max-instances` to control costs

### Estimated Costs

Based on typical usage (monthly):

- **Cloud Run**: $5-20 (depends on execution time)
- **Secret Manager**: $0.06 per secret per month
- **Container Registry/Artifact Registry**: $0.10 per GB
- **Cloud Logging**: First 50GB free, then $0.50/GB

## Security Best Practices

1. **Use Secret Manager**: Never hardcode credentials
2. **Limit IAM Permissions**: Grant minimum required permissions
3. **Enable VPC Connector**: For private GitHub Enterprise
4. **Use Service Accounts**: Create dedicated service account
5. **Enable Binary Authorization**: Ensure only trusted images run
6. **Regular Updates**: Keep base images and dependencies updated

## Next Steps

- Set up [Cloud Monitoring alerts](https://cloud.google.com/monitoring/alerts)
- Configure [Cloud Logging sinks](https://cloud.google.com/logging/docs/export)
- Implement [Cloud Armor](https://cloud.google.com/armor) for DDoS protection
- Set up [CI/CD pipeline](https://cloud.google.com/build/docs/deploying-builds/deploy-cloud-run) for automated deployments

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
