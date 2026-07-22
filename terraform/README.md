# Declarative Infrastructure as Code (Terraform) — ECG Multi-Agent System

This directory contains complete, production-grade **Terraform** configurations to declaratively provision and manage all foundational Google Cloud Platform (GCP) resources required by the European Camping Group (ECG) Autonomous Multi-Agent System.

---

## 🏛️ Provisioned Architecture & Resources

| File | Resource Type | Description |
| :--- | :--- | :--- |
| **[`main.tf`](./main.tf)** | Provider & API Enablement | Configures `google` and `google-beta` providers (v5.38+) and programmatically enables required GCP APIs (`aiplatform`, `bigquery`, `firestore`, `secretmanager`, `run`, `iam`, `trace`, `logging`). |
| **[`variables.tf`](./variables.tf)** | Declarative Variables | Configures customizable deployment parameters: `project_id`, `region`, `environment`, `bigquery_dataset_id`, `firestore_location`, and Apigee endpoint URIs. |
| **[`outputs.tf`](./outputs.tf)** | Resource Outputs | Exposes key infrastructure outputs for CI/CD pipelines: `bigquery_dataset_uri`, `firestore_database_id`, `agent_runner_sa_email`, and Secret Manager IDs. |
| **[`bigquery.tf`](./bigquery.tf)** | BigQuery Dataset & Tables | Creates the `ecg_analytics` dataset and provisions tables `occupancy_daily` and `booking_segments` with explicit JSON schema definitions for yield analysis. |
| **[`firestore.tf`](./firestore.tf)** | Native Firestore DB & Indexes | Provisions the `(default)` Firestore Native database instance and creates composite indexes (`support_tickets` by status/campsite, `pms_inventory` by campsite/status) for multi-turn session and inventory retention. |
| **[`secret_manager.tf`](./secret_manager.tf)** | Secret Manager Credentials | Provisions secure secrets (`apigee-pms-token`, `apigee-marketing-token`, `gemini-api-key`) with automatic replication to avoid hardcoded API keys. |
| **[`iam.tf`](./iam.tf)** | Least-Privilege IAM & SA | Creates specialized Service Accounts (`agent-ecg-runner`, `agent-ecg-mcp`) and binds strict least-privilege roles (`aiplatform.user`, `bigquery.dataViewer`, `datastore.user`, `secretmanager.secretAccessor`). |

---

## 🚀 Quick Start / Usage

### 1. Initialize Terraform Workspace
Download required Google Cloud provider plugins:
```bash
terraform init
```

### 2. Validate & Preview Deployment Plan
Review the infrastructure changes before applying:
```bash
terraform plan -var="project_id=customer-demo-01" -var="environment=prod"
```

### 3. Apply Infrastructure Changes
Provision all resources in Google Cloud (requires project Owner or Editor permissions):
```bash
terraform apply -auto-approve -var="project_id=customer-demo-01"
```

### 4. Verify Provisioned Outputs
To inspect output URIs and service account emails after deployment:
```bash
terraform output
```
