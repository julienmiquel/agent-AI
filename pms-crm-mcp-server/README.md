# ECG PMS & CRM Interactive MCP UI App Server

An interactive, host-theme-aware **MCP App Server** built with `@modelcontextprotocol/ext-apps` and `@modelcontextprotocol/sdk` for Holiday company **Resalys PMS Inventory Management** and **Apigee CRM Flash Campaign Staging**.

---

## 🌟 Key Features

1. **Interactive MCP UI Widget (`ui://pms-crm/mcp-app.html`)**:
   - Renders inside sandboxed iframe embedded in MCP Hosts (Claude Desktop, Gemini Enterprise, basic-host, etc.).
   - Built with Vite single-file bundler (`dist/mcp-app.html`).
   - Dark/Light mode theme awareness (`--mcp-background-color`, `--mcp-text-color`).
   - Safe area insets padding adaptation (`app.onhostcontextchanged`).

2. **Resalys PMS Inventory Control Center**:
   - Campsite selection (`LA_SIRENE_06`, `HIPOCAMP_07`, etc.).
   - Real-time Chart.js doughnut chart breaking down unit statuses (`AVAILABLE_FOR_SALE`, `HELD_BACK`, `MAINTENANCE`, `BOOKED`).
   - Interactive unit status controls & batch release action ("Release All Held Back").
   - Integrated Human-In-The-Loop (HITL) approval banner with amber border (`#f59e0b`) & confirmation transition (`#10b981`).
   - Identity Passthrough scope (`CloudIdentity (julien)`).

3. **Apigee CRM Flash Campaign Staging**:
   - Target market selection (`NL`, `FR`, `DE`, `UK`).
   - Target campsite cluster selection (`MEDITERRANEAN_SOUTH`, `ATLANTIC_NORTH`, etc.).
   - Discount percentage slider (5% to 50%).
   - Live ad copywriting preview auto-translated in Dutch, French, German, or English.
   - Imagen GCS URI resolution (`gs://ecg-marketing-assets/genai/banners/...`).
   - Interactive HITL campaign staging gate to Apigee gateway (`POST /marketing/v1/campaigns/draft`).

4. **Two-Way Client & Model Interaction (`app.registerTool`)**:
   - `get-pms-crm-state`: Model reads full UI state.
   - `update-pms-unit-status`: Model updates unit status live inside the UI widget.
   - `set-crm-campaign-config`: Model adjusts discount, market, or promo copywriting live.

---

## 🚀 Quick Start

### Build the MCP App Bundle & Server
```bash
cd pms-crm-mcp-server
npm install --registry=https://registry.npmjs.org/
npm run build
```

### Run HTTP Server
```bash
npm run serve:http
# Server runs on http://localhost:3002/mcp
# Standalone Web Widget UI accessible at http://localhost:3002/widget
```

### Run Stdio Server (for Claude Desktop / Local CLI)
```bash
npm run serve:stdio
```

---

## 🛠️ MCP Tools Registered

| Tool Name | Type | Description |
|-----------|------|-------------|
| `get-pms-inventory` | Read-Only | Returns campsite mobil-home units, occupancy breakdown, and held-back yield units with the MCP UI widget. |
| `resalys-update-inventory` | Mutating | Updates unit inventory status in Resalys PMS with identity scope. |
| `crm-stage-flash-campaign` | Mutating | Stages flash campaign draft to Apigee CRM Webhook gateway. |

---

## 🧪 Testing

Run pytest from the repository root:
```bash
uv run pytest
```
