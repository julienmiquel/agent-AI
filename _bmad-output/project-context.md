---
project_name: 'agent-ecg'
user_name: 'Julien'
date: '2026-07-20'
sections_completed: ['technology_stack', 'critical_implementation_rules', 'available_skills_mapping']
existing_patterns_found: 4
---

# Project Context for AI Agents

_This file contains critical rules, architecture guidelines, and available context skills that AI agents must follow when implementing code and workflows in `agent-ecg`._

---

## Technology Stack & Versions

- **Framework**: Google Agent Development Kit (ADK) (`google.genai.agent_development_kit`)
- **Language**: Python 3.10+
- **LLM Engine**: Gemini Enterprise Models (`gemini-2.5-pro`, `gemini-3.5-flash`, `gemini-2.5-flash`) via `google-genai` SDK
- **Data & Analytics**: Google Cloud BigQuery (`BigQueryTool`, dataset `ecg_analytics`)
- **API Management & Connectivity**: REST OpenAPI via Apigee (`OpenAPITool`) for Resalys PMS (`api.ecg.camp/pms`) and CRM Marketing (`api.ecg.camp/marketing`) — *mocked during local dev & unit/eval testing*
- **Storage**: Google Cloud Storage (`gs://ecg-marketing-assets/`)
- **Observability & Audit**: Vertex AI Agent Observability & Cloud Logging
- **SDLC & Agent Framework**: BMAD (Brief -> Map -> Act -> Double-Check) & Agent Platform

---

## Critical Implementation Rules

### 1. Framework & Agent Architecture Rules (ADK & Gemini)
- **Multi-Agent Pattern**: Enforce the Supervisor Multi-Agent pattern: `ECG_Supervisor_Agent` orchestrates child agents (`Yield_Analytics_Agent`, `PMS_Operations_Agent`, `Marketing_Campaign_Agent`).
- **Model Selection**: Use `gemini-2.5-pro` for reasoning-heavy root supervisor and yield/marketing agents; use `gemini-3.5-flash` / `gemini-2.5-flash` for high-throughput, low-latency operational tasks (e.g. PMS inventory status).
- **State Management**: Preserve conversation state and cross-agent context using ADK `StateSession` context. Never re-instantiate transient state outside sessions.
- **Human-in-the-Loop (HITL) Gate**: Any tool execution causing mutating side-effects (`PUT`, `POST`, `DELETE`, e.g., Resalys inventory updates or CRM campaign drafting) **MUST** pause execution and request explicit user confirmation (`YES/NO`).
- **Relevant Skills**: `google-adk-agent-development`, `gemini-api-dev`, `vertex-ai-api-dev`, `gemini-agents-api`, `gemini-interactions-api`.

### 2. Data & Analytics Rules (BigQuery & Tool Security)
- **Zero Duplication**: Queries must execute on-the-fly against the `ecg_analytics` BigQuery dataset without staging copies or temporary table leaks.
- **Data Loss Prevention**: Destructive SQL (`DROP`, `TRUNCATE`, or unhedged `DELETE`) is strictly forbidden without explicit consent (`accidental-data-loss-prevention`).
- **Identity Passthrough**: Forward Google Cloud Identity / Workspace tokens so BigQuery and Apigee permissions mirror the authenticated user.
- **Relevant Skills**: `developing-with-bigquery`, `discovering-gcp-data-assets`, `bigquery-data-transfer-service`, `accidental-data-loss-prevention`.

### 3. Testing & Evaluation Rules
- **MCP & ADK Testing**: Validate tool schemas and local runner execution using the MCP testing framework before pushing updates (`agent-mcp-testing-framework`).
- **Apigee & External API Mocking**: All external Apigee REST API calls (`api.ecg.camp/pms` Resalys PMS and `api.ecg.camp/marketing` CRM) **MUST** be intercepted and mocked using OpenAPI mock specs or HTTP stubs (`httpx_mock` / `responses`) during testing, evaluation flywheel runs, and local dry-runs to prevent accidental side-effects on production systems.
- **Eval Flywheel**: Run continuous regression benchmarks on agent trajectories, tool call accuracy, and response grounding using `agent-eval-flywheel-sdlc`.
- **TDD / ATDD**: Scaffold acceptance tests using red-phase TDD prior to story execution (`bmad-testarch-atdd`, `bmad-testarch-automate`).
- **Relevant Skills**: `agent-mcp-testing-framework`, `agent-eval-flywheel-sdlc`, `bmad-code-review`, `bmad-testarch-framework`, `bmad-testarch-atdd`.

### 4. Observability, Security & Safety Rules
- **Tracing & Telemetry**: Emit OpenTelemetry spans and trace agent reasoning trajectories in Cloud Logging / Vertex AI Agent Observability (`agent-observability-tracing`).
- **Security Guardrails**: Enforce prompt injection safeguards, least-privilege IAM, and secret protection across all agents and MCP servers (`agent-security-guardrails`).
- **Relevant Skills**: `agent-observability-tracing`, `agent-security-guardrails`, `read-gcp-logs`.

### 5. Deployment & Ecosystem Registration Rules
- **Agent Platform & Enterprise**: Deploy models via Agent Platform (`agent-platform-deploy`) and register ADK agents with Gemini Enterprise / Discovery Engine (`gemini-enterprise-agent-registration`).
- **MCP & UI Extensions**: Containerize and deploy MCP servers on Cloud Run (`deploy-mcp-app`), creating interactive app UIs where relevant (`build-mcp-app-ui`).
- **Relevant Skills**: `agent-platform-deploy`, `gemini-enterprise-agent-registration`, `gemini-enterprise-app-management`, `deploy-mcp-app`, `build-mcp-app-ui`.

---

## Available Agent Skills Map

_The following skills are installed and available in this environment. Agents should consult and activate relevant skills for specific tasks._

### 🤖 ADK & Gemini Agent Development
- **`google-adk-agent-development`**: Google Agent Development Kit framework, `SupervisorAgent`, `Agent`, `Runner`, `StateSession`, `Tool` patterns.
- **`gemini-api-dev` / `vertex-ai-api-dev`**: Gemini multimodal models, function calling, structured outputs, GenAI SDK.
- **`gemini-agents-api` / `gemini-interactions-api`**: Programmatic agent management, stateful conversations, streaming & interactions.
- **`gemini-enterprise-agent-registration`**: Registering ADK agents into Gemini Enterprise / Agent Builder.
- **`gemini-enterprise-app-management`**: Managing Discovery Engine / Agent Builder search/chat engines.

### 🛡️ Observability, Testing & Security
- **`agent-mcp-testing-framework`**: Testing framework for ADK Agents and FastMCP endpoints.
- **`agent-observability-tracing`**: OpenTelemetry spans, Cloud Logging, metrics, and trace debugging.
- **`agent-eval-flywheel-sdlc`**: Evaluation dataset generation, trajectory scoring, and benchmark regression testing.
- **`agent-security-guardrails`**: IAM least privilege, prompt injection defense, secret management.
- **`read-gcp-logs`**: Reading Cloud Run & Vertex AI Agent Engine logs via gcloud.

### 📊 Data & BigQuery
- **`developing-with-bigquery`**: BigQuery SQL optimization, BigFrames, ML/AI functions.
- **`discovering-gcp-data-assets`**: Finding, exploring, and inspecting BigQuery datasets and GCP data assets.
- **`bigquery-data-transfer-service`**: DTS pipelines and datasource metadata inspection.
- **`accidental-data-loss-prevention`**: Rules for stopping unapproved destructive operations.

### 🚀 Agent Platform & MCP Deployment
- **`agent-platform-deploy`**: Model Garden deployment, endpoint management, undeployment.
- **`agent-platform-prompt-management`**: Managed prompts versioning and orchestration.
- **`agent-platform-rag-engine-management`**: RAG corpora management and grounded content generation.
- **`agent-platform-tuning`**: Model fine-tuning workflows on Agent Platform.
- **`deploy-mcp-app`**: Deploying MCP servers to Cloud Run & linking to Gemini Enterprise.
- **`build-mcp-app-ui`**: Building interactive web UI dashboards for MCP tools.

### 🛠️ BMAD SDLC & Workflow Tools
- **`bmad-architecture` / `bmad-spec` / `bmad-prd`**: Technical architecture, spec kernels, and PRD management.
- **`bmad-quick-dev` / `bmad-dev-story`**: Rapid implementation of user stories and code changes.
- **`bmad-code-review` / `bmad-review-edge-case-hunter`**: Adversarial code review and boundary testing.
- **`bmad-testarch-*`**: Test architecture, ATDD, framework setup, CI/CD quality gates, NFR auditing.
- **`bmad-generate-project-context`**: Generating and maintaining project context files.

### 🐍 Environment & Tooling
- **`managing-python-dependencies`**: Virtualenv, dependency isolation, and package management best practices.
- **`uv`**: Fast Python package manager setup and PATH verification.
- **`modern-web-guidance`**: Modern HTML/CSS/JS web development standards.
