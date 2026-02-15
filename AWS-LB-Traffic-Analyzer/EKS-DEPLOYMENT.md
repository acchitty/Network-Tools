# AWS Load Balancer Traffic Analyzer - EKS Deployment Guide

Deploy the traffic analyzer to Amazon EKS clusters as a DaemonSet.

---

## Architecture

**DaemonSet Deployment:**
- Runs one analyzer pod per EKS node
- Uses host network mode to capture all pod traffic
- Requires privileged containers
- Sends metrics/logs to CloudWatch

---

## Prerequisites

1. **EKS Cluster** running
2. **kubectl** configured
3. **AWS CLI** configured
4. **ECR repository** for Docker image
5. **IAM role** for service account (IRSA)

---

## Step 1: Create IAM Role for Service Account (IRSA)

### Create IAM Policy

```bash
cat > traffic-analyzer-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "LBTrafficAnalyzer"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/eks/traffic-analyzer:*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name TrafficAnalyzerPolicy \
  --policy-document file://traffic-analyzer-policy.json
```

### Create IAM Role with IRSA

```bash
# Replace with your values
CLUSTER_NAME="your-cluster"
ACCOUNT_ID="123456789012"
REGION="us-east-1"

# Create service account with IAM role
eksctl create iamserviceaccount \
  --name traffic-analyzer \
  --namespace traffic-analyzer \
  --cluster $CLUSTER_NAME \
  --region $REGION \
  --attach-policy-arn arn:aws:iam::$ACCOUNT_ID:policy/TrafficAnalyzerPolicy \
  --approve \
  --override-existing-serviceaccounts
```

---

## Step 2: Build and Push Docker Image

### Build Image

```bash
cd ~/aws-lb-traffic-analyzer

# Build Docker image
docker build -t traffic-analyzer:latest .
```

### Push to ECR

```bash
# Replace with your account ID and region
ACCOUNT_ID="123456789012"
REGION="us-east-1"

# Create ECR repository
aws ecr create-repository \
  --repository-name traffic-analyzer \
  --region $REGION

# Login to ECR
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Tag image
docker tag traffic-analyzer:latest \
  $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/traffic-analyzer:latest

# Push image
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/traffic-analyzer:latest
```

---

## Step 3: Update Kubernetes Manifest

Edit `eks-daemonset.yaml`:

```bash
# Replace ACCOUNT_ID with your AWS account ID
sed -i "s/ACCOUNT_ID/123456789012/g" eks-daemonset.yaml

# Verify changes
grep "ACCOUNT_ID" eks-daemonset.yaml
```

---

## Step 4: Deploy to EKS

```bash
# Create namespace and deploy
kubectl apply -f eks-daemonset.yaml

# Verify deployment
kubectl get daemonset -n traffic-analyzer
kubectl get pods -n traffic-analyzer -o wide
```

---

## Step 5: Verify It's Working

### Check Pod Status

```bash
# List all analyzer pods
kubectl get pods -n traffic-analyzer

# Should show one pod per node, all Running
```

### View Logs

```bash
# Get pod name
POD_NAME=$(kubectl get pods -n traffic-analyzer -o jsonpath='{.items[0].metadata.name}')

# View logs
kubectl logs -n traffic-analyzer $POD_NAME -f

# View logs from all pods
kubectl logs -n traffic-analyzer -l app=traffic-analyzer --tail=50
```

### Check CloudWatch

**Metrics:**
```
CloudWatch > Metrics > LBTrafficAnalyzer
```

**Logs:**
```
CloudWatch > Logs > /aws/eks/traffic-analyzer
```

---

## Configuration

### Adjust Sample Rate (Lower CPU Usage)

Edit the DaemonSet:

```bash
kubectl edit daemonset traffic-analyzer -n traffic-analyzer
```

Change CMD:
```yaml
cmd: ["-i", "eth0", "-s", "20", "--enable-cloudwatch"]  # 1 in 20 packets
```

### Adjust Resource Limits

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"  # Increase if needed
    cpu: "500m"      # Increase if needed
```

---

## Monitoring

### View Metrics

```bash
# Get metrics from CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace LBTrafficAnalyzer \
  --metric-name TimeoutCount \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-1
```

### View Logs

```bash
# Tail CloudWatch Logs
aws logs tail "/aws/eks/traffic-analyzer" --follow --region us-east-1

# Query with Logs Insights
# Go to CloudWatch > Logs > Insights
# Select log group: /aws/eks/traffic-analyzer
# Run query:
fields @timestamp, @message
| filter @message like /TIMEOUT/
| stats count() by bin(5m)
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod -n traffic-analyzer <POD_NAME>

# Common issues:
# 1. Image pull error - Check ECR permissions
# 2. Privileged mode denied - Check PSP/PSA
# 3. IRSA not working - Check service account annotation
```

### No Metrics in CloudWatch

```bash
# Check pod logs for errors
kubectl logs -n traffic-analyzer <POD_NAME> | grep -i "cloudwatch\|error"

# Verify IRSA is working
kubectl describe sa traffic-analyzer -n traffic-analyzer
# Should show: eks.amazonaws.com/role-arn annotation

# Test AWS credentials in pod
kubectl exec -n traffic-analyzer <POD_NAME> -- \
  aws sts get-caller-identity
```

### High CPU Usage

```bash
# Increase sample rate (analyze fewer packets)
kubectl set env daemonset/traffic-analyzer -n traffic-analyzer \
  SAMPLE_RATE=20

# Or edit DaemonSet directly
kubectl edit daemonset traffic-analyzer -n traffic-analyzer
```

### Permission Denied Errors

```bash
# Verify pod is privileged
kubectl get pod -n traffic-analyzer <POD_NAME> -o yaml | grep privileged

# Should show: privileged: true

# Check security context
kubectl get pod -n traffic-analyzer <POD_NAME> -o yaml | grep -A 5 securityContext
```

---

## Security Considerations

⚠️ **This DaemonSet requires privileged containers**

**Risks:**
- Privileged pods can access host resources
- Can capture all network traffic on the node
- Requires NET_ADMIN and NET_RAW capabilities

**Mitigations:**
1. Use dedicated namespace
2. Limit RBAC permissions
3. Use Pod Security Standards (restricted where possible)
4. Monitor pod activity
5. Use network policies to restrict pod communication

**Alternative:** Use AWS VPC Flow Logs instead if security is a concern.

---

## Uninstall

```bash
# Delete DaemonSet
kubectl delete -f eks-daemonset.yaml

# Delete namespace
kubectl delete namespace traffic-analyzer

# Delete IAM resources
eksctl delete iamserviceaccount \
  --name traffic-analyzer \
  --namespace traffic-analyzer \
  --cluster your-cluster

aws iam delete-policy \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/TrafficAnalyzerPolicy

# Delete ECR repository
aws ecr delete-repository \
  --repository-name traffic-analyzer \
  --force \
  --region us-east-1
```

---

## Comparison: EKS vs EC2 Deployment

| Feature | EC2 | EKS DaemonSet |
|---------|-----|---------------|
| **Installation** | Simple | Complex |
| **Privileges** | Root | Privileged container |
| **Scope** | Single instance | All pods on node |
| **Resource Usage** | Low | Medium |
| **Security** | Better | Requires privileged |
| **Maintenance** | Manual | Kubernetes managed |

---

## Recommended Alternatives for EKS

Instead of this analyzer, consider:

1. **AWS VPC Flow Logs** - Native AWS solution
2. **Istio/Linkerd** - Service mesh with built-in observability
3. **Datadog/New Relic** - Commercial Kubernetes monitoring
4. **Prometheus + Grafana** - Open source monitoring stack
5. **AWS X-Ray** - Application tracing

These provide better Kubernetes integration without privileged containers.

---

## Support

**View pod logs:**
```bash
kubectl logs -n traffic-analyzer -l app=traffic-analyzer --tail=100
```

**Exec into pod:**
```bash
kubectl exec -it -n traffic-analyzer <POD_NAME> -- /bin/bash
```

**Check CloudWatch:**
```bash
aws cloudwatch list-metrics --namespace LBTrafficAnalyzer
aws logs tail "/aws/eks/traffic-analyzer" --follow
```
