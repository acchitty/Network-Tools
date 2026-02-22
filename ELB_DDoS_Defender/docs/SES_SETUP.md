# Amazon SES Email Setup Guide

## Quick Setup

The installer automatically sends a verification email to your address. You just need to click the link.

## Step-by-Step SES Configuration

### 1. Automatic Verification (During Installation)

When you run the installer, it automatically:
```bash
aws ses verify-email-identity --email-address your-email@example.com --region us-east-1
```

You'll receive an email from AWS with subject: **"Amazon SES Email Address Verification Request"**

### 2. Click Verification Link

Open the email and click the verification link. You'll see:
```
✅ Email address verified successfully
```

### 3. Verify Status

```bash
# Check verification status
aws ses get-identity-verification-attributes --identities your-email@example.com

# Output should show:
# VerificationStatus: Success
```

### 4. Test Email Sending

```bash
# Send test email
aws ses send-email \
  --from your-email@example.com \
  --destination ToAddresses=your-email@example.com \
  --message Subject={Data="Test"},Body={Text={Data="Test email"}} \
  --region us-east-1
```

## SES Sandbox vs Production

### Sandbox Mode (Default)

- Can only send TO verified email addresses
- Limited to 200 emails per day
- 1 email per second

**To verify additional recipients:**
```bash
aws ses verify-email-identity --email-address recipient@example.com
```

### Production Mode (Recommended)

Request production access to send to any email address:

1. Go to: https://console.aws.amazon.com/ses/
2. Click "Account Dashboard"
3. Click "Request production access"
4. Fill out the form:
   - **Mail Type**: Transactional
   - **Website URL**: Your company website
   - **Use Case**: DDoS attack alerting system
   - **Compliance**: Describe how you handle bounces
5. Submit (usually approved in 24 hours)

## Troubleshooting

### Email Not Received

```bash
# Check if verification was sent
aws ses get-identity-verification-attributes --identities your-email@example.com

# Resend verification
aws ses verify-email-identity --email-address your-email@example.com

# Check spam folder
```

### "Email address not verified" Error

```bash
# Verify the sender email
aws ses verify-email-identity --email-address sender@example.com

# Verify recipient emails (if in sandbox)
aws ses verify-email-identity --email-address recipient@example.com
```

### Wrong Region

SES is region-specific. Make sure you're using the same region:

```bash
# Check current region
aws configure get region

# Or specify region explicitly
aws ses verify-email-identity --email-address your@example.com --region us-east-1
```

## Multiple Recipients

To send alerts to multiple people:

### Option 1: Verify Each Email (Sandbox)

```bash
aws ses verify-email-identity --email-address admin@example.com
aws ses verify-email-identity --email-address security@example.com
aws ses verify-email-identity --email-address oncall@example.com
```

### Option 2: Use Production Mode

Request production access (see above), then you can send to any email without verification.

## SES Pricing

- **Free Tier**: 62,000 emails per month (if sending from EC2)
- **After Free Tier**: $0.10 per 1,000 emails
- **Attachments**: Included in email count

**Example Cost:**
- 100 attack alerts per month with 3 attachments each = 100 emails
- Cost: **FREE** (well within free tier)

## Configuration in config.yaml

```yaml
alerts:
  email:
    enabled: true
    backend: ses
    sender: security@example.com  # Must be verified
    recipients:
      - admin@example.com         # Must be verified (sandbox)
      - team@example.com          # Must be verified (sandbox)
    region: us-east-1
```

## Advanced: Domain Verification

Instead of verifying individual emails, verify your entire domain:

```bash
# Verify domain
aws ses verify-domain-identity --domain example.com

# AWS will provide DNS records to add
# Add TXT record to your DNS
# Then any email @example.com can send
```

## Quick Reference

```bash
# Verify email
aws ses verify-email-identity --email-address your@example.com

# Check status
aws ses get-identity-verification-attributes --identities your@example.com

# List verified emails
aws ses list-identities

# Delete verification
aws ses delete-identity --identity your@example.com

# Send test email
aws ses send-email \
  --from your@example.com \
  --destination ToAddresses=recipient@example.com \
  --message Subject={Data="Test"},Body={Text={Data="Test"}}
```
