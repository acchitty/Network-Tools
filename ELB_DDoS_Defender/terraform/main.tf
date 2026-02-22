# ELB DDoS Defender - Complete Terraform Deployment
# Deploys everything in one command

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC ID where load balancers are located"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for monitoring instance (private subnet recommended)"
  type        = string
}

variable "key_name" {
  description = "EC2 Key Pair name (optional, Session Manager recommended)"
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "email_address" {
  description = "Email address for DDoS alerts"
  type        = string
}

variable "enable_public_ip" {
  description = "Enable public IP (set false for private subnet with Session Manager)"
  type        = bool
  default     = false
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH (if public IP enabled)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project = "ELB-DDoS-Defender"
    ManagedBy = "Terraform"
  }
}

# Data sources
data "aws_vpc" "selected" {
  id = var.vpc_id
}

data "aws_subnet" "selected" {
  id = var.subnet_id
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# IAM Role for EC2 Instance
resource "aws_iam_role" "defender" {
  name = "ELBDDoSDefenderRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Policy for Defender
resource "aws_iam_role_policy" "defender" {
  name = "ELBDDoSDefenderPolicy"
  role = aws_iam_role.defender.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:Describe*",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeInstances",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:CreateTrafficMirrorTarget",
          "ec2:CreateTrafficMirrorFilter",
          "ec2:CreateTrafficMirrorFilterRule",
          "ec2:CreateTrafficMirrorSession",
          "ec2:DescribeTrafficMirror*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/elb-ddos-defender*"
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::*-ddos-pcaps/*"
      }
    ]
  })
}

# Attach SSM policy for Session Manager
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.defender.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance Profile
resource "aws_iam_instance_profile" "defender" {
  name = "ELBDDoSDefenderProfile"
  role = aws_iam_role.defender.name

  tags = var.tags
}

# Security Group
resource "aws_security_group" "defender" {
  name        = "elb-ddos-defender-sg"
  description = "Security group for ELB DDoS Defender"
  vpc_id      = var.vpc_id

  # SSH (optional)
  dynamic "ingress" {
    for_each = var.enable_public_ip && var.key_name != "" ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [var.allowed_ssh_cidr]
      description = "SSH access"
    }
  }

  # Traffic Mirroring
  ingress {
    from_port   = 4789
    to_port     = 4789
    protocol    = "udp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
    description = "VPC Traffic Mirroring"
  }

  # Outbound - HTTPS for AWS APIs
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS for AWS APIs"
  }

  # Outbound - All within VPC
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
    description = "All traffic within VPC"
  }

  tags = merge(var.tags, {
    Name = "elb-ddos-defender-sg"
  })
}

# User Data Script
locals {
  user_data = templatefile("${path.module}/user-data.sh", {
    region        = var.aws_region
    email_address = var.email_address
  })
}

# EC2 Instance
resource "aws_instance" "defender" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.defender.id]
  iam_instance_profile   = aws_iam_instance_profile.defender.name
  key_name               = var.key_name != "" ? var.key_name : null
  
  associate_public_ip_address = var.enable_public_ip

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = local.user_data

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # IMDSv2 only
    http_put_response_hop_limit = 1
  }

  tags = merge(var.tags, {
    Name = "ELB-DDoS-Defender"
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "defender" {
  name              = "/aws/elb-ddos-defender"
  retention_in_days = 90

  tags = var.tags
}

# Outputs
output "instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.defender.id
}

output "instance_private_ip" {
  description = "Private IP address"
  value       = aws_instance.defender.private_ip
}

output "instance_public_ip" {
  description = "Public IP address (if enabled)"
  value       = var.enable_public_ip ? aws_instance.defender.public_ip : "N/A - Use Session Manager"
}

output "security_group_id" {
  description = "Security Group ID"
  value       = aws_security_group.defender.id
}

output "iam_role_arn" {
  description = "IAM Role ARN"
  value       = aws_iam_role.defender.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group"
  value       = aws_cloudwatch_log_group.defender.name
}

output "session_manager_command" {
  description = "Command to connect via Session Manager"
  value       = "aws ssm start-session --target ${aws_instance.defender.id} --region ${var.aws_region}"
}

output "ssh_command" {
  description = "SSH command (if public IP enabled)"
  value       = var.enable_public_ip && var.key_name != "" ? "ssh -i ${var.key_name}.pem ec2-user@${aws_instance.defender.public_ip}" : "N/A - Use Session Manager"
}

output "dashboard_command" {
  description = "Command to view dashboard after connecting"
  value       = "sudo /opt/elb-ddos-defender/dashboard.sh"
}

output "next_steps" {
  description = "Next steps after deployment"
  value       = <<-EOT
    
    ✅ Deployment Complete!
    
    1. Connect to instance:
       ${var.enable_public_ip && var.key_name != "" ? "ssh -i ${var.key_name}.pem ec2-user@${aws_instance.defender.public_ip}" : "aws ssm start-session --target ${aws_instance.defender.id} --region ${var.aws_region}"}
    
    2. Wait for installation to complete (~5 minutes):
       tail -f /var/log/cloud-init-output.log
    
    3. View dashboard:
       sudo /opt/elb-ddos-defender/dashboard.sh
    
    4. Check status:
       sudo systemctl status elb-ddos-defender
    
    5. View logs:
       sudo tail -f /var/log/elb-ddos-defender/defender.log
    
    📚 Documentation: https://github.com/acchitty/Network-Tools/tree/main/ELB_DDoS_Defender
  EOT
}
