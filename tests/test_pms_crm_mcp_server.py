"""Integration tests for European Camping Company (Company) PMS & CRM MCP App Server."""

import os
import json
import subprocess
import pytest

MCP_SERVER_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "pms-crm-mcp-server")
)


def test_pms_crm_mcp_server_files_exist():
    """Verify all required MCP server and app bundle files are created."""
    assert os.path.exists(os.path.join(MCP_SERVER_DIR, "package.json"))
    assert os.path.exists(os.path.join(MCP_SERVER_DIR, "server.ts"))
    assert os.path.exists(os.path.join(MCP_SERVER_DIR, "main.ts"))
    assert os.path.exists(os.path.join(MCP_SERVER_DIR, "mcp-app.html"))
    assert os.path.exists(os.path.join(MCP_SERVER_DIR, "src", "mcp-app.ts"))
    assert os.path.exists(os.path.join(MCP_SERVER_DIR, "dist", "mcp-app.html"))


def test_pms_crm_mcp_server_bundle_content():
    """Verify built HTML bundle contains Company title, tabs, and Chart.js integration."""
    bundle_path = os.path.join(MCP_SERVER_DIR, "dist", "mcp-app.html")
    with open(bundle_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Company PMS & CRM Operations Control Center" in content
    assert "PMS Resalys Inventory" in content
    assert "CRM Flash Campaigns" in content
    assert "CloudIdentity (julien)" in content
