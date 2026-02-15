# Enhanced Features Setup Guide

## ⚠️ CRITICAL: IAM Permissions Required

**BEFORE enabling CloudWatch features, your EC2 instance role MUST have these permissions:**

### Required IAM Policy for CloudWatch Metrics

Attach this policy to your **EC2 Instance IAM Role**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudWatchMetrics",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

### How to Add Permissions:

1. **Find your EC2 instance role:**
   - AWS Console > EC2 > Instances > Select your instance
   - Look at "IAM Role" in the details
   
2. **Add the policy:**
   - AWS Console > IAM > Roles > [Your EC2 Role]
   - Click "Add permissions" > "Create inline policy"
   - Paste the JSON above
   - Name it: `CloudWatchMetricsAccess`

3. **Verify permissions:**
   ```bash
   # On your EC2 instance
   aws cloudwatch put-metric-data --namespace Test --metric-name TestMetric --value 1
   # Should succeed with no errors
   ```

### Optional: SNS Alerting Permissions

If you want email/SMS alerts, also add:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSNSPublish",
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:*:*:traffic-analyzer-alerts"
    }
  ]
}
```

---

## Step 1: ✅ Verify IAM Permissions (REQUIRED)

**Your EC2 instance role already has the correct permissions if:**
- You can see metrics appearing in CloudWatch Console under "LBTrafficAnalyzer" namespace
- No permission errors in logs: `sudo journalctl -u traffic-analyzer | grep -i "permission\|denied"`

**If you see permission errors, add the IAM policy shown above.**

---

## Step 2: Install boto3 (AWS SDK)

```bash
sudo pip3 install boto3
```

**✅ Already installed on your EC2 instance**

---

## Step 3: Create SNS topic (optional, for alerts)

```bash
aws sns create-topic --name traffic-analyzer-alerts --region us-east-1
aws sns subscribe --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:traffic-analyzer-alerts \
  --protocol email --notification-endpoint your-email@example.com
```

## Step 4: Enable features

**✅ Already enabled on your EC2 instance**

The service is running with CloudWatch enabled:
```bash
sudo systemctl status traffic-analyzer
```

To add SNS alerts, edit:

```bash
sudo nano /etc/systemd/system/traffic-analyzer.service
```

Update ExecStart line:
```
ExecStart=/usr/bin/python3 /home/ec2-user/aws-lb-traffic-analyzer/aws-lb-traffic-analyzer.py -i enX0 -s 10 --enable-cloudwatch --sns-topic arn:aws:sns:us-east-1:ACCOUNT_ID:traffic-analyzer-alerts
```

## Step 5: Restart service

```bash
sudo systemctl daemon-reload
sudo systemctl restart traffic-analyzer
```

## Features Added:

1. **CloudWatch Metrics** - View in AWS Console under Custom Namespaces > LBTrafficAnalyzer
2. **SNS Alerts** - Get email when errors exceed threshold
3. **Response Time Tracking** - Logs slow requests (>1s)
4. **IP Filtering** - Ignore internal monitoring IPs

## View CloudWatch Metrics:

AWS Console > CloudWatch > Metrics > Custom Namespaces > LBTrafficAnalyzer

Metrics available:
- TimeoutCount
- TCPErrorCount  
- HealthCheckFailures
- HTTPErrorRate
- ConnectionCount
