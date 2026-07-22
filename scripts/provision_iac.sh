#!/usr/bin/env bash
# Automated Declarative Infrastructure Provisioning Script using Terraform
set -e

PROJECT_ID=${GCP_PROJECT_ID:-"customer-demo-01"}
REGION=${GOOGLE_CLOUD_LOCATION:-"us-central1"}
ENV=${DEPLOY_ENV:-"prod"}

echo "=================================================================="
echo " [IaC Provisioning] Initializing and Applying Terraform Configurations"
echo " Project: ${PROJECT_ID} | Region: ${REGION} | Env: ${ENV}"
echo "=================================================================="

cd "$(dirname "$0")/../terraform"

echo "1. Initializing Terraform workspace and downloading Google Cloud providers..."
terraform init -input=false

echo "2. Validating Terraform syntax and schema configurations..."
terraform validate

echo "3. Applying declarative infrastructure changes (BigQuery, Firestore, Secret Manager, IAM)..."
terraform apply -auto-approve \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="environment=${ENV}"

echo ""
echo "=== Terraform Provisioning Completed Successfully! ==="
terraform output
