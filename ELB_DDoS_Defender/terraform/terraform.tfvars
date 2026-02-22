# Test Configuration for Local Terraform Deployment

# Required - Using my-vpc-01 with private subnet
aws_region    = "us-east-1"
vpc_id        = "vpc-0fa389dd34dc4fe86"           # my-vpc-01
subnet_id     = "subnet-0c09b8d1e4ed0755c"        # My-Private Subnet-01 (us-east-1b)
email_address = "acchitty@amazon.com"

# Optional - Customize as needed
instance_type      = "t3.medium"
enable_public_ip   = false            # Using Session Manager (no public IP)
key_name           = ""               # Leave empty for Session Manager only
allowed_ssh_cidr   = "0.0.0.0/0"

# Tags
tags = {
  Project     = "ELB-DDoS-Defender"
  Environment = "Test"
  ManagedBy   = "Terraform"
}
