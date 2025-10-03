# OpsAiX Kubernetes Deployment Guide

## Overview

OpsAiX provides comprehensive Kubernetes support with Helm charts for easy deployment across multiple cloud providers including AWS EKS, Azure AKS, and Google GKE.

## Prerequisites

- Kubernetes cluster (v1.20+)
- Helm 3.x
- kubectl configured for your cluster
- Appropriate cloud provider CLI tools (optional)

## Quick Start

### 1. Single Cloud Deployment

#### AWS EKS
```bash
# Deploy to AWS EKS
./deploy.sh --cloud aws --region us-east-1
```

#### Azure AKS  
```bash
# Deploy to Azure AKS
./deploy.sh --cloud azure --region eastus
```

#### Google GKE
```bash
# Deploy to Google GKE
./deploy.sh --cloud gcp --region us-central1
```

### 2. Multi-Cloud Deployment

```bash
# Deploy across AWS and Azure
./deploy.sh --multi-cloud --primary aws --secondary azure

# Deploy across all three clouds
./deploy.sh --multi-cloud --primary aws --secondary azure --tertiary gcp
```

## Helm Chart Configuration

### Basic Installation

```bash
# Add Bitnami repo for dependencies
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install OpsAiX
helm install opsaix k8s/helm/opsaix/ --namespace opsaix --create-namespace
```

### Custom Values

Create a custom `values.yaml` file:

```yaml
# Custom values for production deployment
opsaix:
  replicaCount: 5
  image:
    tag: "v0.1.0"
  
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 2000m
      memory: 4Gi

postgresql:
  auth:
    postgresPassword: "your-secure-password"
    password: "your-app-password"

secrets:
  openaiApiKey: "your-openai-key"
  secretKey: "your-secret-key"

ingress:
  enabled: true
  hosts:
    - host: opsaix.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
```

Deploy with custom values:
```bash
helm install opsaix k8s/helm/opsaix/ -f custom-values.yaml --namespace opsaix
```

## Cloud-Specific Configurations

### AWS EKS

#### Prerequisites
- AWS Load Balancer Controller
- EBS CSI Driver
- IAM roles for service accounts

```yaml
# AWS-specific values
global:
  storageClass: "gp3"

ingress:
  className: "aws-load-balancer-controller"
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
```

### Azure AKS

#### Prerequisites
- Application Gateway Ingress Controller
- Azure Disk CSI Driver

```yaml
# Azure-specific values
global:
  storageClass: "managed-premium"

ingress:
  className: "azure/application-gateway"
  annotations:
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
```

### Google GKE

#### Prerequisites
- GCE Ingress Controller
- Compute Persistent Disk CSI Driver

```yaml
# GCP-specific values
global:
  storageClass: "standard-rwo"

ingress:
  className: "gce"
  annotations:
    kubernetes.io/ingress.global-static-ip-name: "opsaix-ip"
```

## Security Configuration

### RBAC

The Helm chart creates appropriate RBAC resources:

```yaml
security:
  rbac:
    create: true
  serviceAccount:
    create: true
    name: "opsaix"
```

### Network Policies

Enable network policies for enhanced security:

```yaml
security:
  networkPolicy:
    enabled: true
```

### Pod Security Standards

Configure pod security context:

```yaml
opsaix:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
```

## Monitoring and Observability

### Prometheus Integration

```yaml
monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
    adminPassword: "admin"
```

### Distributed Tracing

```yaml
monitoring:
  jaeger:
    enabled: true
```

## Scaling and High Availability

### Horizontal Pod Autoscaling

```yaml
opsaix:
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
```

### Multi-Region Deployment

For true high availability, deploy across multiple regions:

```bash
# Deploy to multiple regions in the same cloud
./deploy.sh --cloud aws --region us-east-1 --release opsaix-east
./deploy.sh --cloud aws --region us-west-2 --release opsaix-west
```

## Backup and Disaster Recovery

### Database Backup

```yaml
postgresql:
  primary:
    persistence:
      enabled: true
      size: 50Gi
    backup:
      enabled: true
      schedule: "0 2 * * *"
```

### Cross-Cloud Data Replication

For multi-cloud deployments, configure data replication between regions.

## Troubleshooting

### Common Issues

1. **Pod Startup Issues**
   ```bash
   kubectl describe pod -l app.kubernetes.io/name=opsaix -n opsaix
   kubectl logs -f deployment/opsaix -n opsaix
   ```

2. **Ingress Not Working**
   ```bash
   kubectl describe ingress opsaix -n opsaix
   kubectl get events -n opsaix
   ```

3. **Database Connection Issues**
   ```bash
   kubectl exec -it deployment/opsaix -n opsaix -- env | grep DATABASE
   kubectl logs -f statefulset/opsaix-postgresql -n opsaix
   ```

### Health Checks

```bash
# Check overall deployment health
kubectl get all -n opsaix

# Check application health endpoint
kubectl port-forward svc/opsaix 8080:8080 -n opsaix
curl http://localhost:8080/health
```

## Upgrading

### Helm Upgrade

```bash
# Upgrade to newer version
helm upgrade opsaix k8s/helm/opsaix/ --namespace opsaix --reuse-values
```

### Rolling Updates

The deployment supports rolling updates with zero downtime:

```yaml
opsaix:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
```

## Uninstall

```bash
# Uninstall OpsAiX
helm uninstall opsaix --namespace opsaix

# Remove namespace (optional)
kubectl delete namespace opsaix
```

## Production Checklist

- [ ] Configure proper resource limits and requests
- [ ] Set up monitoring and alerting  
- [ ] Configure backup strategies
- [ ] Enable network policies
- [ ] Set up ingress with TLS certificates
- [ ] Configure secrets management (External Secrets, Vault, etc.)
- [ ] Test disaster recovery procedures
- [ ] Set up log aggregation
- [ ] Configure autoscaling policies