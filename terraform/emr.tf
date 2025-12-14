# ==============================================================================
# EMR Cluster Configuration
# ==============================================================================

# IAM role for EMR service
resource "aws_iam_role" "emr_service_role" {
  name = "${var.project_prefix}-emr-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "elasticmapreduce.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "emr_service_policy" {
  role       = aws_iam_role.emr_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole"
}

# IAM role for EC2 instances in the cluster
resource "aws_iam_role" "emr_ec2_role" {
  name = "${var.project_prefix}-emr-ec2-role"

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
}

resource "aws_iam_role_policy_attachment" "emr_ec2_policy" {
  role       = aws_iam_role.emr_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role"
}

# extra S3 access for our buckets
resource "aws_iam_role_policy" "emr_s3_access" {
  name = "${var.project_prefix}-emr-s3-access"
  role = aws_iam_role.emr_ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*",
          aws_s3_bucket.processed_data.arn,
          "${aws_s3_bucket.processed_data.arn}/*",
          aws_s3_bucket.scripts.arn,
          "${aws_s3_bucket.scripts.arn}/*"
        ]
      }
    ]
  })
}

# instance profile for EC2
resource "aws_iam_instance_profile" "emr_ec2_instance_profile" {
  name = "${var.project_prefix}-emr-ec2-profile"
  role = aws_iam_role.emr_ec2_role.name
}

# security group for EMR
resource "aws_security_group" "emr_master" {
  name        = "${var.project_prefix}-emr-master-sg"
  description = "Security group for EMR master node"

  # ssh access (optional, for debugging)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}-emr-master-sg"
  }
}

resource "aws_security_group" "emr_core" {
  name        = "${var.project_prefix}-emr-core-sg"
  description = "Security group for EMR core nodes"

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}-emr-core-sg"
  }
}

# outputs for EMR
output "emr_service_role_arn" {
  description = "EMR service role ARN"
  value       = aws_iam_role.emr_service_role.arn
}

output "emr_ec2_instance_profile" {
  description = "EMR EC2 instance profile"
  value       = aws_iam_instance_profile.emr_ec2_instance_profile.name
}

output "emr_master_security_group" {
  description = "EMR master security group ID"
  value       = aws_security_group.emr_master.id
}

output "emr_core_security_group" {
  description = "EMR core security group ID"
  value       = aws_security_group.emr_core.id
}