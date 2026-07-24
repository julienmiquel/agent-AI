#!/usr/bin/env python3
"""Cleans up stale / duplicate registered agents in Gemini Enterprise.

Deletes old/stale agent resources under default_assistant so Gemini Enterprise UI
always routes new turns to the active Company Supervisor Agent.

Usage:
    python3 scripts/cleanup_stale_discovery_agents.py [--project PROJECT] [--engine-id ENGINE_ID] [--keep-agent-id KEEP_ID]
"""

import sys
import os
import argparse
import subprocess
import json
import urllib.request
import urllib.error
import ssl

DEFAULT_PROJECT = os.environ.get("GCP_PROJECT_ID", "ml-demo-384110")
DEFAULT_ENGINE_ID = os.environ.get("GEMINI_ENTERPRISE_ENGINE_ID", "gemini-enterprise-ecg_1784557637596")
ACTIVE_RE_ID = "3550315899263123456"

def parse_args():
    parser = argparse.ArgumentParser(description="Cleanup Stale Discovery Engine Agents")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP Project ID")
    parser.add_argument("--engine-id", default=DEFAULT_ENGINE_ID, help="Gemini Enterprise Engine ID")
    parser.add_argument("--keep-agent-id", default="12052769936243497130", help="Primary Agent ID to keep")
    return parser.parse_args()

def get_access_token() -> str:
    res = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True)
    return res.stdout.strip()

def cleanup_stale_agents(project_id: str, engine_id: str, keep_agent_id: str):
    token = get_access_token()
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    list_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{engine_id}/assistants/default_assistant/agents"
    req = urllib.request.Request(list_url, headers={
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": project_id
    })

    try:
        with urllib.request.urlopen(req, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ Error fetching agents list: {e}", file=sys.stderr)
        sys.exit(1)

    agents = data.get("agents", [])
    print(f"Found {len(agents)} total registered agents in default_assistant.")

    for agent in agents:
        agent_name = agent.get("name", "")
        agent_id = agent_name.split("/")[-1]
        display_name = agent.get("displayName", "")
        
        # Protect builtin deep_research and the selected active agent ID
        if agent_id in ("deep_research", keep_agent_id):
            print(f"  [KEEP] {agent_id} ({display_name})")
            continue

        print(f"  [DELETE STALE] {agent_id} ({display_name})...")
        del_url = f"https://discoveryengine.googleapis.com/v1alpha/{agent_name}"
        del_req = urllib.request.Request(del_url, headers={
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": project_id
        }, method="DELETE")

        try:
            with urllib.request.urlopen(del_req, context=ssl_ctx) as del_resp:
                print(f"   ✅ Deleted: {agent_id}")
        except urllib.error.HTTPError as e:
            print(f"   ⚠️ Could not delete {agent_id}: status {e.code}")

def main():
    args = parse_args()
    cleanup_stale_agents(args.project, args.engine_id, args.keep_agent_id)

if __name__ == "__main__":
    main()
