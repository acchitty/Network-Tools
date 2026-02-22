#!/bin/bash
# Interactive CloudFormation Setup for ELB DDoS Defender

set -e

echo "=========================================="
echo "  ELB DDoS Defender - CloudFormation Setup"
echo "=========================================="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Run 'aws configure' first."
    exit 1
fi

# Get region
echo "📍 Select AWS Region:"
echo "1) us-east-1 (N. Virginia)"
echo "2) us-west-2 (Oregon)"
echo "3) eu-west-1 (Ireland)"
echo "4) Custom region"
read -p "Enter choice [1-4]: " region_choice

case $region_choice in
    1) REGION="us-east-1" ;;
    2) REGION="us-west-2" ;;
    3) REGION="eu-west-1" ;;
    4) read -p "Enter region: " REGION ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

echo "✅ Using region: $REGION"
echo ""

# List VPCs
echo "🌐 Available VPCs in $REGION:"
aws ec2 describe-vpcs --region $REGION \
    --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0],IsDefault]' \
    --output table

read -p "Enter VPC ID: " VPC_ID

# Validate VPC
if ! aws ec2 describe-vpcs --vpc-ids $VPC_ID --region $REGION &>/dev/null; then
    echo "❌ Invalid VPC ID"
    exit 1
fi

echo "✅ Using VPC: $VPC_ID"
echo ""

# List subnets in VPC
echo "📡 Available Subnets in $VPC_ID:"
aws ec2 describe-subnets --region $REGION \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,MapPublicIpOnLaunch,Tags[?Key==`Name`].Value|[0]]' \
    --output table

read -p "Enter Subnet ID: " SUBNET_ID

# Validate subnet
if ! aws ec2 describe-subnets --subnet-ids $SUBNET_ID --region $REGION &>/dev/null; then
    echo "❌ Invalid Subnet ID"
    exit 1
fi

echo "✅ Using Subnet: $SUBNET_ID"
echo ""

# List key pairs
echo "🔑 Available Key Pairs in $REGION:"
aws ec2 describe-key-pairs --region $REGION \
    --query 'KeyPairs[*].[KeyName,KeyPairId]' \
    --output table

read -p "Enter Key Pair name (or leave empty for Session Manager only): " KEY_NAME

if [ -z "$KEY_NAME" ]; then
    KEY_NAME="NONE"
    echo "ℹ️  Using Session Manager (no SSH key)"
else
    echo "✅ Using SSH key: $KEY_NAME"
fi

echo ""

# Email address
read -p "📧 Enter email address for alerts: " EMAIL_ADDRESS

# Validate email
if [[ ! "$EMAIL_ADDRESS" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "❌ Invalid email address"
    exit 1
fi

echo ""

# Instance type
echo "💻 Select Instance Type:"
echo "1) t3.medium (Recommended - Up to 5 ELBs)"
echo "2) t3.large (5-10 ELBs)"
echo "3) t3.xlarge (10+ ELBs)"
read -p "Enter choice [1-3]: " instance_choice

case $instance_choice in
    1) INSTANCE_TYPE="t3.medium" ;;
    2) INSTANCE_TYPE="t3.large" ;;
    3) INSTANCE_TYPE="t3.xlarge" ;;
    *) INSTANCE_TYPE="t3.medium" ;;
esac

echo "✅ Using instance type: $INSTANCE_TYPE"
echo ""

# Stack name
read -p "📦 Enter CloudFormation stack name [elb-ddos-defender]: " STACK_NAME
STACK_NAME=${STACK_NAME:-elb-ddos-defender}

echo ""

# Summary
echo "=========================================="
echo "  Configuration Summary"
echo "=========================================="
echo "Stack Name:       $STACK_NAME"
echo "Region:           $REGION"
echo "VPC:              $VPC_ID"
echo "Subnet:           $SUBNET_ID"
echo "Instance Type:    $INSTANCE_TYPE"
echo "Email:            $EMAIL_ADDRESS"
echo "SSH Key:          $KEY_NAME"
echo "=========================================="
echo ""

read -p "Proceed with deployment? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

# Deploy CloudFormation stack
echo ""
echo "🚀 Deploying CloudFormation stack..."

aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://template.yaml \
  --parameters \
    ParameterKey=VpcId,ParameterValue=$VPC_ID \
    ParameterKey=SubnetId,ParameterValue=$SUBNET_ID \
    ParameterKey=KeyName,ParameterValue=$KEY_NAME \
    ParameterKey=EmailAddress,ParameterValue=$EMAIL_ADDRESS \
    ParameterKey=InstanceType,ParameterValue=$INSTANCE_TYPE \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo ""
echo "⏳ Waiting for stack creation to complete..."
echo "   This may take 5-10 minutes..."

aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME \
  --region $REGION

echo ""
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""

# Get outputs
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

PUBLIC_IP=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`PublicIP`].OutputValue' \
  --output text 2>/dev/null || echo "N/A")

echo "📋 Stack Details:"
echo "   Stack Name: $STACK_NAME"
echo "   Instance ID: $INSTANCE_ID"
echo ""

if [ "$KEY_NAME" != "NONE" ] && [ "$PUBLIC_IP" != "N/A" ]; then
    echo "🔗 SSH Access:"
    echo "   ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"
else
    echo "🔗 Session Manager Access:"
    echo "   aws ssm start-session --target $INSTANCE_ID --region $REGION"
fi

echo ""
echo "📊 View Dashboard:"
echo "   sudo /opt/elb-ddos-defender/dashboard.sh"
echo ""
echo "📝 View Logs:"
echo "   sudo tail -f /var/log/elb-ddos-defender/defender.log"
echo ""
echo "⏳ Installation will complete in ~5 minutes"
echo "=========================================="
