# Deployment Guide

This document provides an overview of deployment options for the GitHub Maintainer Agent.

## Quick Start

### Local Development with Docker

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your credentials
# Add your GITHUB_TOKEN and GEMINI_API_KEY

# 3. Build and run with Docker Compose
docker-compose up

# 4. Or build and run manually
docker build -t github-maintainer-agent .
docker run -it --rm \
  --env-file .env \
  github-maintainer-agent \
  analyze myusername --automation manual
```

## Deployment Options

### 1. Docker (Local/Self-Hosted)

**Best for**: Development, testing, self-hosted environments

**Files**:
- `Dockerfile` - Multi-stage build for optimized image
- `docker-compose.yml` - Local development setup
- `.dockerignore` - Build optimization

**Quick Start**:
```bash
docker-compose up
```

See `docker-compose.yml` for configuration options.

---

### 2. Google Cloud Run

**Best for**: Serverless deployment, automatic scaling, pay-per-use

**Documentation**: [`docs/DEPLOYMENT_CLOUD_RUN.md`](docs/DEPLOYMENT_CLOUD_RUN.md)

**Key Features**:
- Automatic scaling to zero
- Built-in HTTPS
- Secret Manager integration
- Cloud Scheduler for periodic runs

**Quick Deploy**:
```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/github-maintainer-agent

# Deploy
gcloud run deploy github-maintainer-agent \
  --image gcr.io/PROJECT_ID/github-maintainer-agent \
  --set-secrets="GITHUB_TOKEN=github-token:latest,GEMINI_API_KEY=gemini-api-key:latest"
```

---

### 3. Vertex AI Agent Engine

**Best for**: Enterprise deployments, advanced AI workflows, managed infrastructure

**Documentation**: [`docs/DEPLOYMENT_VERTEX_AI.md`](docs/DEPLOYMENT_VERTEX_AI.md)

**Key Features**:
- Managed agent runtime
- Built-in monitoring and tracing
- Vertex AI model integration
- Enterprise security features

**Quick Deploy**:
```bash
# Package and upload
tar -czf agent.tar.gz src/ main.py requirements.txt
gsutil cp agent.tar.gz gs://PROJECT_ID-agents/

# Deploy
gcloud ai agents deploy github-maintainer-agent \
  --package-uri=gs://PROJECT_ID-agents/agent.tar.gz \
  --config=agent_config.yaml
```

---

### 4. Kubernetes

**Best for**: Multi-cloud, on-premises, complex orchestration needs

**Documentation**: [`k8s/README.md`](k8s/README.md)

**Files**:
- `k8s/deployment.yaml` - Main deployment
- `k8s/configmap.yaml` - Configuration
- `k8s/secrets.yaml` - Credentials (template)
- `k8s/cronjob.yaml` - Scheduled runs
- `k8s/pvc.yaml` - Persistent storage
- `k8s/serviceaccount.yaml` - RBAC configuration

**Quick Deploy**:
```bash
# Update secrets and config
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# Deploy
kubectl apply -f k8s/
```

---

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxx` |
| `GEMINI_API_KEY` | Google Gemini API Key | `AIzaxxxxxxxxxx` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_PARALLEL_REPOS` | Parallel processing limit | `5` |
| `GITHUB_API_BASE_URL` | GitHub API endpoint | `https://api.github.com` |

### Creating API Keys

**GitHub Token**:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:user`
4. Copy the token

**Gemini API Key**:
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create or select a project
4. Copy the API key

---

## Deployment Comparison

| Feature | Docker | Cloud Run | Vertex AI | Kubernetes |
|---------|--------|-----------|-----------|------------|
| **Complexity** | Low | Low | Medium | High |
| **Cost** | Infrastructure | Pay-per-use | Managed | Infrastructure |
| **Scaling** | Manual | Automatic | Automatic | Manual/Auto |
| **Monitoring** | Basic | Built-in | Advanced | Configurable |
| **Best For** | Dev/Test | Serverless | Enterprise | Multi-cloud |

---

## Security Best Practices

1. **Never commit credentials**: Use `.env` files (gitignored) or secret managers
2. **Use Secret Manager**: For Cloud Run and Vertex AI deployments
3. **Rotate tokens regularly**: Update GitHub and API tokens periodically
4. **Limit permissions**: Use minimal required scopes for tokens
5. **Enable audit logging**: Track all API calls and agent actions
6. **Use HTTPS**: Always use secure connections
7. **Run as non-root**: Container runs as user `agent` (UID 1000)

---

## Monitoring and Observability

### Logs

**Docker**:
```bash
docker-compose logs -f
```

**Cloud Run**:
```bash
gcloud run services logs tail github-maintainer-agent
```

**Kubernetes**:
```bash
kubectl logs -l app=github-maintainer-agent --follow
```

### Metrics

The agent tracks:
- Repositories analyzed
- Suggestions generated
- Issues created
- API calls made
- Token usage
- Execution time
- Error rates

Metrics are logged in structured format and can be exported to monitoring systems.

---

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Error: Bad credentials
```
**Solution**: Verify `GITHUB_TOKEN` is valid and has required scopes

**2. Rate Limiting**
```
Error: API rate limit exceeded
```
**Solution**: Wait for rate limit reset or use authenticated token

**3. Memory Issues**
```
Error: Container killed (OOMKilled)
```
**Solution**: Increase memory limits in deployment configuration

**4. Timeout Errors**
```
Error: Execution timeout
```
**Solution**: Increase timeout or reduce `MAX_PARALLEL_REPOS`

### Getting Help

1. Check logs for detailed error messages
2. Review deployment documentation for your platform
3. Verify environment variables are set correctly
4. Test with a small number of repositories first

---

## Testing Deployment

### Verify Docker Build

```bash
# Build image
docker build -t github-maintainer-agent:test .

# Test with help command
docker run --rm github-maintainer-agent:test --help

# Test with environment variables
docker run --rm \
  -e GITHUB_TOKEN=test \
  -e GEMINI_API_KEY=test \
  github-maintainer-agent:test \
  python -c "import os; print(f'Env vars loaded: {bool(os.getenv(\"GITHUB_TOKEN\"))}')"
```

### Run Deployment Tests

```bash
# Run all deployment tests
pytest tests/test_deployment.py -v

# Run specific test class
pytest tests/test_deployment.py::TestDockerBuild -v

# Skip Docker-dependent tests
pytest tests/test_deployment.py -v -m "not docker"
```

---

## Cost Estimation

### Cloud Run (Monthly)

- **Compute**: $0.10 per hour of execution
- **Requests**: First 2M free, then $0.40 per million
- **Typical usage**: $5-20/month for weekly runs

### Vertex AI (Monthly)

- **Agent Runtime**: $0.10 per hour
- **Gemini API**: $0.00025 per 1K characters
- **Storage**: $0.02 per GB
- **Typical usage**: $20-50/month for weekly runs

### Kubernetes (Monthly)

- **Cluster**: $70-200/month (GKE standard)
- **Storage**: $0.10 per GB-month
- **Egress**: $0.12 per GB
- **Typical usage**: $80-250/month (shared cluster)

---

## Next Steps

1. Choose your deployment platform
2. Follow the detailed guide for your platform
3. Set up monitoring and alerts
4. Schedule periodic runs
5. Review and iterate on suggestions

For detailed platform-specific instructions, see:
- [Cloud Run Deployment](docs/DEPLOYMENT_CLOUD_RUN.md)
- [Vertex AI Deployment](docs/DEPLOYMENT_VERTEX_AI.md)
- [Kubernetes Deployment](k8s/README.md)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review platform-specific documentation
3. Check application logs for detailed errors
4. Verify all environment variables are set correctly
