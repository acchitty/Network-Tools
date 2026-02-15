# IAM Permissions for Traffic Analyzer

## Required EC2 Instance Role Policy

Your EC2 instance role MUST have this policy attached for CloudWatch features to work:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchMetricsAccess",
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
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/ec2/traffic-analyzer:*"
    }
  ]
}
```

## How to Apply:

### Option 1: AWS Console
1. Go to IAM > Roles
2. Find your EC2 instance role
3. Click "Add permissions" > "Create inline policy"
4. Paste the JSON above
5. Name it: `TrafficAnalyzerCloudWatch`
6. Click "Create policy"

### Option 2: AWS CLI
```bash
# Replace ROLE_NAME with your EC2 instance role name
aws iam put-role-policy \
  --role-name ROLE_NAME \
  --policy-name TrafficAnalyzerCloudWatch \
  --policy-document file://iam-policy.json
```

## Verify Permissions

On your EC2 instance:
```bash
# Test CloudWatch access
aws cloudwatch put-metric-data \
  --namespace LBTrafficAnalyzer \
  --metric-name TestMetric \
  --value 1

# Should return nothing (success)
# If you see "AccessDenied", permissions are missing
```

## Optional: SNS Alerting

For email/SMS alerts, also add:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SNSPublishAccess",
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:*:*:traffic-analyzer-*"
    }
  ]
}
```

## Security Best Practices

✅ **Recommended:** Use the condition in the policy to restrict to specific namespace
✅ **Recommended:** Use least privilege - only grant what's needed
✅ **Recommended:** Use separate policies for CloudWatch and SNS
❌ **Avoid:** Using `"Resource": "*"` without conditions
❌ **Avoid:** Granting `cloudwatch:*` (too broad)
