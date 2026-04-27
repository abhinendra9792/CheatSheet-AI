# Deployment Guide

## Local Development Deployment

### Docker Setup

#### Build Docker Images
```bash
# Backend
docker build -f Dockerfile.backend -t cheatsheet-ai-backend:1.0 .

# Frontend
docker build -f Dockerfile.frontend -t cheatsheet-ai-frontend:1.0 .
```

#### Docker Compose
```bash
docker-compose up -d
# Access at http://localhost:3000
```

#### Dockerfile.backend
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

ENV PYTHONUNBUFFERED=1

CMD ["python", "api_server.py"]
```

#### Dockerfile.frontend
```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
RUN npm install -g serve

EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

## Cloud Deployment

### Google Cloud (Recommended)

#### Cloud Run
```bash
# Deploy backend
gcloud run deploy cheatsheet-ai-backend \
  --source backend/ \
  --platform managed \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY=xxx

# Deploy frontend
gcloud run deploy cheatsheet-ai-frontend \
  --source frontend/ \
  --platform managed \
  --region us-central1
```

#### Cloud Storage
```bash
# Create bucket for cheatsheets
gsutil mb gs://cheatsheet-ai-outputs

# Configure CORS
gsutil cors set cors-config.json gs://cheatsheet-ai-outputs
```

### Azure Deployment

#### App Service
```bash
az appservice plan create \
  --name cheatsheet-ai-plan \
  --resource-group myGroup \
  --sku B1

az webapp create \
  --resource-group myGroup \
  --plan cheatsheet-ai-plan \
  --name cheatsheet-ai \
  --runtime "python|3.11"
```

### AWS Deployment

#### Lambda (Backend)
```bash
# Package backend
cd backend
pip install -r requirements.txt -t package/
cp -r src/ package/
cd package/
zip -r ../lambda_function.zip .

# Deploy
aws lambda create-function \
  --function-name cheatsheet-ai \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler main.lambda_handler \
  --zip-file fileb://../lambda_function.zip
```

#### S3 + CloudFront
```bash
# Create bucket
aws s3 mb s3://cheatsheet-ai-frontend

# Upload frontend
aws s3 sync frontend/dist/ s3://cheatsheet-ai-frontend

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://cf-config.json
```

## Kubernetes Deployment

### Prerequisites
- kubectl configured
- Kubernetes cluster running

### Deployment Manifest
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cheatsheet-ai

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  namespace: cheatsheet-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: cheatsheet-ai-backend:1.0
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: gemini-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: cheatsheet-ai
spec:
  type: LoadBalancer
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  selector:
    app: backend

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: cheatsheet-ai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-deployment
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Deploy to Kubernetes
```bash
kubectl apply -f k8s-manifest.yaml

# Check status
kubectl get pods -n cheatsheet-ai
kubectl logs -n cheatsheet-ai deployment/backend-deployment
```

## CI/CD Pipeline

### GitHub Actions Workflow

#### .github/workflows/deploy.yml
```yaml
name: Deploy CheatSheet AI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
    
    - name: Run tests
      run: |
        pytest backend/tests/ -v
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Frontend tests
      run: |
        cd frontend
        npm install
        npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Cloud Run
      uses: google-github-actions/deploy-cloudrun@v0
      with:
        service: cheatsheet-ai
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        region: us-central1
        metadata: backend/
```

## Monitoring & Logging

### Cloud Logging Setup
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cheatsheet-ai"

# Create alert
gcloud alpha monitoring policies create \
  --notification-channels=$CHANNEL_ID \
  --display-name="CheatSheet AI Error Alert" \
  --condition-display-name="High Error Rate"
```

### Application Monitoring
```python
# Add monitoring in backend
from google.cloud import monitoring_v3

def log_request(prompt, duration, status):
    """Log request metrics"""
    print(f"[METRIC] prompt={prompt}, duration={duration}s, status={status}")
```

## Rollback Procedure

### Git Rollback
```bash
git revert HEAD
git push origin main
```

### Kubernetes Rollback
```bash
kubectl rollout history deployment/backend-deployment -n cheatsheet-ai
kubectl rollout undo deployment/backend-deployment -n cheatsheet-ai
```

### Cloud Run Rollback
```bash
gcloud run deploy cheatsheet-ai \
  --image gcr.io/project/cheatsheet-ai:previous-version \
  --region us-central1
```

## Production Checklist

- [ ] API keys securely configured
- [ ] Database backups enabled
- [ ] CDN configured
- [ ] SSL/TLS certificates installed
- [ ] Monitoring alerts set up
- [ ] Rate limiting configured
- [ ] CORS headers set properly
- [ ] Error handling tested
- [ ] Performance tested
- [ ] Security scanning completed
- [ ] Load testing completed
- [ ] Documentation updated

## Performance Tuning

### Backend Optimization
```python
# Connection pooling
session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=100))

# Caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_prompt_template(topic):
    return f"Create a cheatsheet about {topic}"
```

### Frontend Optimization
```javascript
// Code splitting
const Generator = lazy(() => import('./pages/Generator'));

// Image optimization
<img src="image.webp" loading="lazy" />
```

---

Last Updated: April 2025
