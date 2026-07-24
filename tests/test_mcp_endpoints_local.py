"""Automated local integration tests for all 6 MCP App Server endpoints via JSON-RPC stdio."""

import os
import json
import subprocess
import pytest

MCP_SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pms-crm-mcp-server"))
DIST_MAIN = os.path.join(MCP_SERVER_DIR, "dist", "main.js")


class MCPStdioClient:
    """Helper client to spawn Node.js MCP stdio process and exchange JSON-RPC frames."""

    def __init__(self):
        self.proc = subprocess.Popen(
            ["node", DIST_MAIN, "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=MCP_SERVER_DIR,
        )
        self.msg_id = 0
        self._initialize()

    def _initialize(self):
        resp = self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pytest-mcp-client", "version": "1.0.0"}
        })
        assert "result" in resp, f"Failed MCP initialize: {resp}"

        # Send initialized notification
        notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        self.proc.stdin.write(json.dumps(notify) + "\n")
        self.proc.stdin.flush()

    def send_request(self, method: str, params: dict = None) -> dict:
        self.msg_id += 1
        payload = {"jsonrpc": "2.0", "id": self.msg_id, "method": method}
        if params is not None:
            payload["params"] = params
        line = json.dumps(payload) + "\n"
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

        while True:
            resp_line = self.proc.stdout.readline()
            if not resp_line:
                raise RuntimeError("MCP process terminated unexpectedly")
            data = json.loads(resp_line)
            # Filter out server notifications/events and match response by id
            if data.get("id") == self.msg_id:
                return data

    def close(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=3)
        except Exception:
            self.proc.kill()


@pytest.fixture(scope="module")
def mcp_client():
    client = MCPStdioClient()
    yield client
    client.close()


def test_mcp_tools_list_and_past_issue_annotations(mcp_client):
    """Verify all 6 tools are registered, schemas are correct, and past issue annotations/rules are present."""
    resp = mcp_client.send_request("tools/list")
    assert "result" in resp, f"tools/list failed: {resp}"
    tools = {t["name"]: t for t in resp["result"]["tools"]}

    expected_tools = {
        "get-pms-inventory",
        "resalys-update-inventory",
        "crm-stage-flash-campaign",
        "company-create-support-ticket",
        "company-get-support-tickets",
        "company-update-ticket-status",
    }
    assert expected_tools.issubset(tools.keys()), f"Missing expected tools: {expected_tools - tools.keys()}"

    # Verify Past Issue 1: crm-stage-flash-campaign description contains CRITICAL RULE requiring non-empty text
    crm_tool = tools["crm-stage-flash-campaign"]
    assert "CRITICAL RULE" in crm_tool["description"], "crm-stage-flash-campaign missing CRITICAL RULE against empty text responses"
    assert "Never invoke this tool with an empty text response" in crm_tool["description"]

    # Verify Past Issue 2: Annotations distinguish read-only vs mutating tools
    assert tools["get-pms-inventory"]["annotations"]["readOnlyHint"] is True
    assert tools["company-get-support-tickets"]["annotations"]["readOnlyHint"] is True
    assert tools["resalys-update-inventory"]["annotations"]["readOnlyHint"] is False
    assert tools["crm-stage-flash-campaign"]["annotations"]["readOnlyHint"] is False
    assert tools["company-create-support-ticket"]["annotations"]["readOnlyHint"] is False
    assert tools["company-update-ticket-status"]["annotations"]["readOnlyHint"] is False


def test_mcp_endpoint_get_pms_inventory(mcp_client):
    """Test get-pms-inventory read-only endpoint execution."""
    resp = mcp_client.send_request("tools/call", {
        "name": "get-pms-inventory",
        "arguments": {"campsiteId": "LA_SIRENE_06"}
    })
    assert "result" in resp, f"get-pms-inventory call failed: {resp}"
    result = resp["result"]
    assert "structuredContent" in result
    assert result["structuredContent"]["identityScope"] == "CloudIdentity (julien)"
    campsites = result["structuredContent"]["campsites"]
    assert isinstance(campsites, list) and len(campsites) >= 1
    assert campsites[0]["campsiteId"] == "LA_SIRENE_06"


def test_mcp_endpoint_resalys_update_inventory(mcp_client):
    """Test resalys-update-inventory mutating endpoint execution."""
    resp = mcp_client.send_request("tools/call", {
        "name": "resalys-update-inventory",
        "arguments": {
            "campsiteId": "LA_SIRENE_06",
            "unitIds": ["MH-102"],
            "newStatus": "AVAILABLE_FOR_SALE"
        }
    })
    assert "result" in resp, f"resalys-update-inventory call failed: {resp}"
    result = resp["result"]
    assert "structuredContent" in result
    payload = result["structuredContent"]
    assert payload["status"] == "SUCCESS"
    assert "MH-102" in payload["updatedUnits"]
    assert payload["newStatus"] == "AVAILABLE_FOR_SALE"
    # Ensure accompanying non-empty text content exists
    assert len(result["content"]) >= 1 and len(result["content"][0]["text"]) > 10


def test_mcp_endpoint_crm_stage_flash_campaign(mcp_client):
    """Test crm-stage-flash-campaign mutating endpoint execution and verify accompanying text rule."""
    resp = mcp_client.send_request("tools/call", {
        "name": "crm-stage-flash-campaign",
        "arguments": {
            "campaignName": "NL Summer Flash Sale",
            "targetMarket": "NL",
            "cluster": "MEDITERRANEAN_SOUTH",
            "discountPercentage": 15
        }
    })
    assert "result" in resp, f"crm-stage-flash-campaign call failed: {resp}"
    result = resp["result"]
    assert "structuredContent" in result
    payload = result["structuredContent"]
    assert payload["status"] == "SUCCESS"
    assert payload["campaignName"] == "NL Summer Flash Sale"
    assert payload["discountPercentage"] == 15

    # Verify text response is present and non-empty (Past Issue 3 assert)
    assert len(result["content"]) >= 1
    text_item = result["content"][0]
    assert text_item["type"] == "text"
    assert "Successfully staged flash campaign 'NL Summer Flash Sale'" in text_item["text"]


def test_mcp_endpoint_company_create_support_ticket(mcp_client):
    """Test company-create-support-ticket mutating endpoint execution."""
    resp = mcp_client.send_request("tools/call", {
        "name": "company-create-support-ticket",
        "arguments": {
            "customerName": "Jean Dupont",
            "campsiteId": "LA_SIRENE_06",
            "unitId": "MH-108",
            "category": "MAINTENANCE",
            "priority": "HIGH",
            "description": "Water heater leak reported"
        }
    })
    assert "result" in resp, f"company-create-support-ticket call failed: {resp}"
    result = resp["result"]
    assert "structuredContent" in result
    payload = result["structuredContent"]
    assert payload["status"] == "SUCCESS"
    assert payload["ticket"]["campsite_id"] == "LA_SIRENE_06"
    assert payload["ticket"]["priority"] == "HIGH"
    assert len(result["content"]) >= 1 and len(result["content"][0]["text"]) > 10


def test_mcp_endpoint_company_get_support_tickets(mcp_client):
    """Test company-get-support-tickets read-only endpoint execution."""
    resp = mcp_client.send_request("tools/call", {
        "name": "company-get-support-tickets",
        "arguments": {"status": "OPEN", "campsiteId": "LA_SIRENE_06"}
    })
    assert "result" in resp, f"company-get-support-tickets call failed: {resp}"
    result = resp["result"]
    assert "structuredContent" in result
    assert result["structuredContent"]["status"] == "SUCCESS"
    assert isinstance(result["structuredContent"]["tickets"], list)


def test_mcp_endpoint_company_update_ticket_status(mcp_client):
    """Test company-update-ticket-status mutating endpoint execution."""
    resp = mcp_client.send_request("tools/call", {
        "name": "company-update-ticket-status",
        "arguments": {"ticketId": "TCK-801", "newStatus": "RESOLVED"}
    })
    assert "result" in resp, f"company-update-ticket-status call failed: {resp}"
    result = resp["result"]
    assert "structuredContent" in result
    assert result["structuredContent"]["status"] == "SUCCESS"
    assert result["structuredContent"]["ticketId"] == "TCK-801"
    assert result["structuredContent"]["newStatus"] == "RESOLVED"
