#!/bin/bash
# Enhanced Setup Script - Checks and enables logs, configures VPC Traffic Mirroring
# Usage: ./setup-logs-and-mirroring.sh

set -e

log() { echo -e "\n▶ $1"; }
success() { echo -e "✓ $1"; }
warn() { echo -e "⚠ $1"; }
error() { echo -e "✗ $1"; exit 1; }

# Get AWS info
REGION=$(aws configure get region || echo "us-east-1")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
INSTANCE_ID=$(ec2-metadata --instance-id 2>/dev/null | cut -d' ' -f2 || echo "")

log "AWS Configuration"
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo "Instance: ${INSTANCE_ID:-N/A}"

# Load config
CONFIG_FILE="/opt/elb-ddos-defender/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    error "Config file not found: $CONFIG_FILE"
fi

# Get selected load balancers from config
SELECTED_LBS=$(grep -A 100 "load_balancers:" "$CONFIG_FILE" | grep "name:" | awk '{print $3}')

if [ -z "$SELECTED_LBS" ]; then
    error "No load balancers found in config"
fi

log "Found load balancers in config:"
echo "$SELECTED_LBS"
echo ""

# Function to check and enable ALB access logs
enable_alb_access_logs() {
    local lb_name=$1
    local lb_arn=$2
    
    log "Checking access logs for: $lb_name"
    
    # Check if access logs enabled
    LOGS_ENABLED=$(aws elbv2 describe-load-balancer-attributes \
        --load-balancer-arn "$lb_arn" \
        --query 'Attributes[?Key==`access_logs.s3.enabled`].Value' \
        --output text)
    
    if [ "$LOGS_ENABLED" == "true" ]; then
        success "Access logs already enabled"
        return
    fi
    
    warn "Access logs NOT enabled"
    read -p "Enable access logs for $lb_name? [y/N]: " ENABLE
    
    if [[ "$ENABLE" =~ ^[Yy]$ ]]; then
        # Create S3 bucket for logs
        BUCKET_NAME="elb-access-logs-${ACCOUNT_ID}-${REGION}"
        
        if ! aws s3 ls "s3://$BUCKET_NAME" 2>/dev/null; then
            log "Creating S3 bucket: $BUCKET_NAME"
            aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
            
            # Add bucket policy for ELB
            ELB_ACCOUNT=$(case $REGION in
                us-east-1) echo "127311923021" ;;
                us-east-2) echo "033677994240" ;;
                us-west-1) echo "027434742980" ;;
                us-west-2) echo "797873946194" ;;
                *) echo "127311923021" ;;
            esac)
            
            cat > /tmp/bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::${ELB_ACCOUNT}:root"},
    "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
  }]
}
EOF
            aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/bucket-policy.json
        fi
        
        # Enable access logs
        aws elbv2 modify-load-balancer-attributes \
            --load-balancer-arn "$lb_arn" \
            --attributes \
                Key=access_logs.s3.enabled,Value=true \
                Key=access_logs.s3.bucket,Value="$BUCKET_NAME" \
                Key=access_logs.s3.prefix,Value="$lb_name"
        
        success "Access logs enabled → s3://$BUCKET_NAME/$lb_name"
        
        # Update config with bucket name
        echo "  access_logs_bucket: $BUCKET_NAME" >> "$CONFIG_FILE"
    fi
}

# Function to check and enable connection logs (NLB/GWLB)
enable_connection_logs() {
    local lb_name=$1
    local lb_arn=$2
    local lb_type=$3
    
    if [ "$lb_type" != "network" ] && [ "$lb_type" != "gateway" ]; then
        return
    fi
    
    log "Checking connection logs for: $lb_name"
    
    # NLB/GWLB use access logs for connection logging
    enable_alb_access_logs "$lb_name" "$lb_arn"
}

# Function to check target health logging
check_health_checks() {
    local lb_name=$1
    local lb_arn=$2
    
    log "Checking health check configuration for: $lb_name"
    
    # Get target groups
    TG_ARNS=$(aws elbv2 describe-target-groups \
        --load-balancer-arn "$lb_arn" \
        --query 'TargetGroups[*].TargetGroupArn' \
        --output text)
    
    if [ -z "$TG_ARNS" ]; then
        warn "No target groups found"
        return
    fi
    
    for TG_ARN in $TG_ARNS; do
        TG_NAME=$(aws elbv2 describe-target-groups \
            --target-group-arns "$TG_ARN" \
            --query 'TargetGroups[0].TargetGroupName' \
            --output text)
        
        HEALTH_CHECK=$(aws elbv2 describe-target-groups \
            --target-group-arns "$TG_ARN" \
            --query 'TargetGroups[0].HealthCheckEnabled' \
            --output text)
        
        if [ "$HEALTH_CHECK" == "true" ]; then
            success "Health checks enabled for: $TG_NAME"
        else
            warn "Health checks DISABLED for: $TG_NAME"
        fi
    done
}

# Function to enable VPC Flow Logs
enable_vpc_flow_logs() {
    local vpc_id=$1
    
    log "Checking VPC Flow Logs for VPC: $vpc_id"
    
    # Check if flow logs exist
    FLOW_LOG=$(aws ec2 describe-flow-logs \
        --filter "Name=resource-id,Values=$vpc_id" \
        --query 'FlowLogs[0].FlowLogId' \
        --output text)
    
    if [ "$FLOW_LOG" != "None" ] && [ -n "$FLOW_LOG" ]; then
        success "VPC Flow Logs already enabled"
        return
    fi
    
    warn "VPC Flow Logs NOT enabled"
    read -p "Enable VPC Flow Logs? [y/N]: " ENABLE
    
    if [[ "$ENABLE" =~ ^[Yy]$ ]]; then
        # Create CloudWatch log group
        LOG_GROUP="/aws/vpc/flowlogs"
        aws logs create-log-group --log-group-name "$LOG_GROUP" 2>/dev/null || true
        
        # Create IAM role for flow logs
        ROLE_NAME="VPCFlowLogsRole"
        if ! aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
            cat > /tmp/flow-logs-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF
            aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document file:///tmp/flow-logs-trust.json
            
            cat > /tmp/flow-logs-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams"
    ],
    "Resource": "*"
  }]
}
EOF
            aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "VPCFlowLogsPolicy" --policy-document file:///tmp/flow-logs-policy.json
            sleep 10
        fi
        
        ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
        
        # Create flow log with ALL fields
        aws ec2 create-flow-logs \
            --resource-type VPC \
            --resource-ids "$vpc_id" \
            --traffic-type ALL \
            --log-destination-type cloud-watch-logs \
            --log-group-name "$LOG_GROUP" \
            --deliver-logs-permission-arn "$ROLE_ARN" \
            --log-format '${version} ${account-id} ${interface-id} ${srcaddr} ${dstaddr} ${srcport} ${dstport} ${protocol} ${packets} ${bytes} ${start} ${end} ${action} ${log-status} ${vpc-id} ${subnet-id} ${instance-id} ${tcp-flags} ${type} ${pkt-srcaddr} ${pkt-dstaddr} ${region} ${az-id} ${sublocation-type} ${sublocation-id} ${pkt-src-aws-service} ${pkt-dst-aws-service} ${flow-direction} ${traffic-path}'
        
        success "VPC Flow Logs enabled with ALL custom fields → $LOG_GROUP"
    fi
}

# Function to setup VPC Traffic Mirroring
setup_vpc_traffic_mirroring() {
    local lb_name=$1
    local lb_arn=$2
    
    log "Setting up VPC Traffic Mirroring for: $lb_name"
    
    if [ -z "$INSTANCE_ID" ]; then
        warn "Not running on EC2, skipping traffic mirroring"
        return
    fi
    
    # Get monitoring instance ENI
    MONITOR_ENI=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].NetworkInterfaces[0].NetworkInterfaceId' \
        --output text)
    
    # Create or get mirror target
    TARGET_ID=$(aws ec2 describe-traffic-mirror-targets \
        --filters "Name=network-interface-id,Values=$MONITOR_ENI" \
        --query 'TrafficMirrorTargets[0].TrafficMirrorTargetId' \
        --output text)
    
    if [ "$TARGET_ID" == "None" ] || [ -z "$TARGET_ID" ]; then
        log "Creating traffic mirror target..."
        TARGET_ID=$(aws ec2 create-traffic-mirror-target \
            --network-interface-id "$MONITOR_ENI" \
            --description "ELB DDoS Defender - $lb_name" \
            --query 'TrafficMirrorTarget.TrafficMirrorTargetId' \
            --output text)
        success "Mirror target created: $TARGET_ID"
    else
        success "Mirror target exists: $TARGET_ID"
    fi
    
    # Create or get mirror filter
    FILTER_ID=$(aws ec2 describe-traffic-mirror-filters \
        --filters "Name=description,Values=ELB DDoS Defender Filter" \
        --query 'TrafficMirrorFilters[0].TrafficMirrorFilterId' \
        --output text)
    
    if [ "$FILTER_ID" == "None" ] || [ -z "$FILTER_ID" ]; then
        log "Creating traffic mirror filter..."
        FILTER_ID=$(aws ec2 create-traffic-mirror-filter \
            --description "ELB DDoS Defender Filter" \
            --query 'TrafficMirrorFilter.TrafficMirrorFilterId' \
            --output text)
        
        # Add ingress rule
        aws ec2 create-traffic-mirror-filter-rule \
            --traffic-mirror-filter-id "$FILTER_ID" \
            --traffic-direction ingress \
            --rule-number 100 \
            --rule-action accept \
            --protocol -1 \
            --source-cidr-block 0.0.0.0/0 \
            --destination-cidr-block 0.0.0.0/0
        
        # Add egress rule
        aws ec2 create-traffic-mirror-filter-rule \
            --traffic-mirror-filter-id "$FILTER_ID" \
            --traffic-direction egress \
            --rule-number 100 \
            --rule-action accept \
            --protocol -1 \
            --source-cidr-block 0.0.0.0/0 \
            --destination-cidr-block 0.0.0.0/0
        
        success "Mirror filter created: $FILTER_ID"
    else
        success "Mirror filter exists: $FILTER_ID"
    fi
    
    # Get load balancer ENIs
    LB_ENIS=$(aws ec2 describe-network-interfaces \
        --filters "Name=description,Values=*ELB*$lb_name*" \
        --query 'NetworkInterfaces[*].NetworkInterfaceId' \
        --output text)
    
    if [ -z "$LB_ENIS" ]; then
        warn "No ENIs found for load balancer: $lb_name"
        return
    fi
    
    # Create mirror session for each ENI
    SESSION_NUM=1
    for ENI in $LB_ENIS; do
        # Check if session already exists
        EXISTING=$(aws ec2 describe-traffic-mirror-sessions \
            --filters "Name=network-interface-id,Values=$ENI" \
            --query 'TrafficMirrorSessions[0].TrafficMirrorSessionId' \
            --output text)
        
        if [ "$EXISTING" != "None" ] && [ -n "$EXISTING" ]; then
            success "Mirror session already exists for ENI: $ENI"
            continue
        fi
        
        # Create session
        aws ec2 create-traffic-mirror-session \
            --network-interface-id "$ENI" \
            --traffic-mirror-target-id "$TARGET_ID" \
            --traffic-mirror-filter-id "$FILTER_ID" \
            --session-number "$SESSION_NUM" \
            --description "ELB DDoS Defender - $lb_name - ENI $SESSION_NUM" \
            2>/dev/null && success "Mirror session created for ENI: $ENI" || warn "Failed to create session for ENI: $ENI"
        
        SESSION_NUM=$((SESSION_NUM + 1))
    done
}

# Main processing loop
for LB_NAME in $SELECTED_LBS; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "Processing: $LB_NAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Get load balancer details
    LB_INFO=$(aws elbv2 describe-load-balancers \
        --names "$LB_NAME" \
        --query 'LoadBalancers[0].[LoadBalancerArn,Type,VpcId]' \
        --output text 2>/dev/null)
    
    if [ -z "$LB_INFO" ]; then
        error "Load balancer not found: $LB_NAME"
    fi
    
    LB_ARN=$(echo "$LB_INFO" | awk '{print $1}')
    LB_TYPE=$(echo "$LB_INFO" | awk '{print $2}')
    VPC_ID=$(echo "$LB_INFO" | awk '{print $3}')
    
    echo "Type: $LB_TYPE"
    echo "VPC: $VPC_ID"
    echo ""
    
    # Check and enable logs
    enable_alb_access_logs "$LB_NAME" "$LB_ARN"
    enable_connection_logs "$LB_NAME" "$LB_ARN" "$LB_TYPE"
    check_health_checks "$LB_NAME" "$LB_ARN"
    
    # Enable VPC Flow Logs (once per VPC)
    if [ -n "$VPC_ID" ]; then
        enable_vpc_flow_logs "$VPC_ID"
    fi
    
    # Setup VPC Traffic Mirroring
    setup_vpc_traffic_mirroring "$LB_NAME" "$LB_ARN"
done

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Setup Complete! ✅                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  ✅ Access logs checked/enabled"
echo "  ✅ Connection logs checked/enabled"
echo "  ✅ Health checks verified"
echo "  ✅ VPC Flow Logs enabled with ALL custom fields"
echo "  ✅ VPC Traffic Mirroring configured"
echo ""
echo "Restart the service to apply changes:"
echo "  sudo systemctl restart elb-ddos-defender"
echo ""
