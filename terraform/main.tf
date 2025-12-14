# ==============================================================================
# PySparkMLRAG - Terraform Infrastructure
# ==============================================================================

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ------------------------------------------------------------------------------
# Provider Configuration
# ------------------------------------------------------------------------------
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "PySparkMLRAG"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ------------------------------------------------------------------------------
# Variables
# ------------------------------------------------------------------------------
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_prefix" {
  description = "Prefix for all resources"
  type        = string
  default     = "pysparkmlrag"
}

# Random suffix for globally unique S3 bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

locals {
  bucket_suffix = random_id.bucket_suffix.hex
}

# ------------------------------------------------------------------------------
# S3 Buckets
# ------------------------------------------------------------------------------

# Raw data bucket (SEC filings land here)
resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.project_prefix}-raw-${local.bucket_suffix}"
}

resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Processed data bucket (cleaned, chunked, embeddings)
resource "aws_s3_bucket" "processed_data" {
  bucket = "${var.project_prefix}-processed-${local.bucket_suffix}"
}

resource "aws_s3_bucket_versioning" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Scripts bucket (PySpark jobs, Lambda code)
resource "aws_s3_bucket" "scripts" {
  bucket = "${var.project_prefix}-scripts-${local.bucket_suffix}"
}

# Airflow bucket (DAGs and logs)
resource "aws_s3_bucket" "airflow" {
  bucket = "${var.project_prefix}-airflow-${local.bucket_suffix}"
}

# ------------------------------------------------------------------------------
# S3 Bucket Folder Structure (using empty objects)
# ------------------------------------------------------------------------------
resource "aws_s3_object" "raw_folders" {
  for_each = toset([
    "sec-filings/",
  ])
  
  bucket  = aws_s3_bucket.raw_data.id
  key     = each.value
  content = ""
}

resource "aws_s3_object" "processed_folders" {
  for_each = toset([
    "cleaned/",
    "chunks/",
    "embeddings/",
  ])
  
  bucket  = aws_s3_bucket.processed_data.id
  key     = each.value
  content = ""
}

resource "aws_s3_object" "scripts_folders" {
  for_each = toset([
    "pyspark/",
    "lambda/",
  ])
  
  bucket  = aws_s3_bucket.scripts.id
  key     = each.value
  content = ""
}

resource "aws_s3_object" "airflow_folders" {
  for_each = toset([
    "dags/",
    "logs/",
  ])
  
  bucket  = aws_s3_bucket.airflow.id
  key     = each.value
  content = ""
}

# ------------------------------------------------------------------------------
# Outputs
# ------------------------------------------------------------------------------
output "raw_bucket_name" {
  description = "Raw data S3 bucket name"
  value       = aws_s3_bucket.raw_data.id
}

output "processed_bucket_name" {
  description = "Processed data S3 bucket name"
  value       = aws_s3_bucket.processed_data.id
}

output "scripts_bucket_name" {
  description = "Scripts S3 bucket name"
  value       = aws_s3_bucket.scripts.id
}

output "airflow_bucket_name" {
  description = "Airflow S3 bucket name"
  value       = aws_s3_bucket.airflow.id
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}