# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the GitHub Maintainer Agent to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured to access your cluster
- Docker image built and pushed to a container registry
- GitHub Personal Access Token
- Gemini API Key

## Quick Start

### 1. Update Configuration

Edit the following files with your values:

**secrets.yaml**:
```yaml
stringData:
  token: "your_github_token_here"
  api-key: "your_gemini_api_key_here"
```

**configmap.yaml**:
```yaml
data:
  username: "your_github_username"
```

**deployment.yaml** and **cronjob.yaml**:
```yaml
image: gcr.io/YOUR_PROJECT_ID/github-maintainer-agent:latest
```

### 2. Deploy to Kubernetes

```bash
# Create namespace (optional)
kubectl create namespace github-maintainer

# Apply all manifests
kubectl apply -f k8s/

# Or apply individually in order
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/cronjob.yaml
```

### 3. Verify Deployment

```bash
# Check deployment status
kubectl get deployments
kubectl get pods

# View logs
kubectl logs -l app=github-maintainer-agent --follow

# Check CronJob
kubectl get cronjobs
```

## Manifest Files

### serviceaccount.yaml
Creates a ServiceAccount with minimal RBAC permissions for the agent.

### configmap.yaml
Contains non-sensitive configuration:
- GitHub username
- Log level
- Performance settings
- Repository filters

### secrets.yaml
Contains sensitive credentials:
- GitHub token
- Gemini API key

**Security Note**: In production, use external secret management like:
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
- [External Secrets Operator](https://external-secrets.io/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [Google Secret Manager](https://cloud.google.com/secret-manager) (for GKE)

### pvc.yaml
Creates a PersistentVolumeClaim for storing:
- Repository profiles
- User preferences
- Session history

### deployment.yaml
Deploys the agent as a Deployment with:
- Resource limits
- Health checks
- Volume mounts
- Security context

### cronjob.yaml
Schedules periodic analysis runs:
- Default: Every Monday at 9 AM
- Configurable schedule
- Automatic issue creation

## Configuration Options

### Environment Variables

Set in `configmap.yaml`:

| Variable | Description | Default |
|----------|-------------|---------|
| `username` | GitHub username to analyze | Required |
| `log-level` | Logging level | INFO |
| `max-parallel-repos` | Max parallel processing | 5 |
| `automation-level` | Issue creation mode | manual |

### Resource Limits

Adjust in `deployment.yaml` and `cronjob.yaml`:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Storage

Adjust PVC size in `pvc.yaml`:

```yaml
resources:
  requests:
    storage: 5Gi
```

## Usage Patterns

### One-Time Analysis

Run a one-time job:

```bash
kubectl create job --from=cronjob/github-maintainer-weekly manual-run-$(date +%s)
```

### Interactive Analysis

Run interactively with manual approval:

```bash
kubectl run -it --rm github-maintainer-interactive \
  --image=gcr.io/YOUR_PROJECT_ID/github-maintainer-agent:latest \
  --env="GITHUB_TOKEN=$(kubectl get secret github-credentials -o jsonpath='{.data.token}' | base64 -d)" \
  --env="GEMINI_API_KEY=$(kubectl get secret gemini-credentials -o jsonpath='{.data.api-key}' | base64 -d)" \
  -- python main.py analyze myusername --automation manual
```

### Scheduled Analysis

The CronJob runs automatically based on the schedule. To modify:

```bash
# Edit schedule
kubectl edit cronjob github-maintainer-weekly

# Suspend CronJob
kubectl patch cronjob github-maintainer-weekly -p '{"spec":{"suspend":true}}'

# Resume CronJob
kubectl patch cronjob github-maintainer-weekly -p '{"spec":{"suspend":false}}'
```

## Monitoring

### View Logs

```bash
# Deployment logs
kubectl logs -l app=github-maintainer-agent --tail=100 --follow

# CronJob logs (latest job)
kubectl logs job/$(kubectl get jobs -l job-type=scheduled --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')

# All jobs
kubectl logs -l job-type=scheduled --tail=50
```

### Check Status

```bash
# Deployment status
kubectl get deployment github-maintainer-agent
kubectl describe deployment github-maintainer-agent

# Pod status
kubectl get pods -l app=github-maintainer-agent
kubectl describe pod -l app=github-maintainer-agent

# CronJob status
kubectl get cronjob github-maintainer-weekly
kubectl describe cronjob github-maintainer-weekly

# Job history
kubectl get jobs -l job-type=scheduled
```

### Resource Usage

```bash
# Current resource usage
kubectl top pod -l app=github-maintainer-agent

# Resource requests/limits
kubectl describe pod -l app=github-maintainer-agent | grep -A 5 "Limits\|Requests"
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod -l app=github-maintainer-agent

# Check logs
kubectl logs -l app=github-maintainer-agent --previous

# Common issues:
# - Image pull errors: Verify image name and registry access
# - Secret not found: Ensure secrets are created
# - PVC pending: Check storage class and provisioner
```

### Authentication Errors

```bash
# Verify secrets
kubectl get secret github-credentials -o jsonpath='{.data.token}' | base64 -d
kubectl get secret gemini-credentials -o jsonpath='{.data.api-key}' | base64 -d

# Update secrets
kubectl delete secret github-credentials
kubectl create secret generic github-credentials --from-literal=token='new_token'
```

### CronJob Not Running

```bash
# Check if suspended
kubectl get cronjob github-maintainer-weekly -o jsonpath='{.spec.suspend}'

# Check schedule
kubectl get cronjob github-maintainer-weekly -o jsonpath='{.spec.schedule}'

# View job history
kubectl get jobs -l job-type=scheduled --sort-by=.metadata.creationTimestamp
```

### Out of Memory

```bash
# Check memory usage
kubectl top pod -l app=github-maintainer-agent

# Increase memory limit in deployment.yaml
resources:
  limits:
    memory: "4Gi"

# Apply changes
kubectl apply -f k8s/deployment.yaml
```

## Security Best Practices

1. **Use External Secret Management**: Don't commit secrets to Git
2. **Network Policies**: Restrict pod network access
3. **Pod Security Standards**: Enable pod security admission
4. **RBAC**: Use minimal permissions
5. **Image Scanning**: Scan images for vulnerabilities
6. **Resource Limits**: Always set resource limits
7. **Non-Root User**: Run as non-root (already configured)

### Example Network Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: github-maintainer-agent
spec:
  podSelector:
    matchLabels:
      app: github-maintainer-agent
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS for GitHub and Gemini APIs
    - protocol: TCP
      port: 53   # DNS
```

## GKE-Specific Configuration

### Workload Identity

For GKE with Workload Identity:

```bash
# Create GCP service account
gcloud iam service-accounts create github-maintainer-agent

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-maintainer-agent@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Bind to Kubernetes service account
gcloud iam service-accounts add-iam-policy-binding \
  github-maintainer-agent@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[default/github-maintainer-agent]"

# Annotate Kubernetes service account
kubectl annotate serviceaccount github-maintainer-agent \
  iam.gke.io/gcp-service-account=github-maintainer-agent@PROJECT_ID.iam.gserviceaccount.com
```

### Using Google Secret Manager

Instead of Kubernetes secrets, use Google Secret Manager:

```yaml
# Add to deployment.yaml
env:
- name: GITHUB_TOKEN
  valueFrom:
    secretKeyRef:
      name: github-token
      key: latest
```

Requires [External Secrets Operator](https://external-secrets.io/latest/provider/google-secrets-manager/).

## Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/

# Or delete individually
kubectl delete cronjob github-maintainer-weekly
kubectl delete deployment github-maintainer-agent
kubectl delete pvc agent-memory-pvc
kubectl delete configmap agent-config
kubectl delete secret github-credentials gemini-credentials
kubectl delete serviceaccount github-maintainer-agent
kubectl delete role github-maintainer-agent
kubectl delete rolebinding github-maintainer-agent
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
