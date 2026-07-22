#!/usr/bin/env python3
"""Registers deployed Agent Engine instance into Gemini Enterprise instance.

Calls Discovery Engine REST API v1alpha endpoint:
POST /v1alpha/projects/{project}/locations/global/collections/default_collection/engines/{engine_id}/assistants/default_assistant/agents
to register provisionedReasoningEngine in Gemini Enterprise, and updates default_assistant displayName.

Usage:
    python3 scripts/register_agent_gemini_enterprise.py [--engine-id ENGINE_ID] [--reasoning-engine RE_NAME] [--project PROJECT]
"""

import sys
import os
import argparse
import subprocess
import json
import datetime
import urllib.request
import urllib.error

DEFAULT_PROJECT = os.environ.get("GCP_PROJECT_ID", "ml-demo-384110")
DEFAULT_ENGINE_ID = os.environ.get("GEMINI_ENTERPRISE_ENGINE_ID", "gemini-enterprise-ecg_1784557637596")
DEFAULT_RE_NAME = "projects/1008225662928/locations/us-central1/reasoningEngines/3550315899263123456"

def parse_args():
    parser = argparse.ArgumentParser(description="Register Agent into Gemini Enterprise Instance")
    parser.add_argument("--engine-id", default=DEFAULT_ENGINE_ID, help="Gemini Enterprise Engine ID")
    parser.add_argument("--reasoning-engine", default=DEFAULT_RE_NAME, help="Deployed Reasoning Engine resource name")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP Project ID")
    return parser.parse_args()

def get_access_token() -> str:
    res = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True)
    return res.stdout.strip()

def register_agent(project_id: str, engine_id: str, reasoning_engine_name: str):
    print("==========================================================")
    print(" Registering Agent in Gemini Enterprise Instance")
    print(f" Engine ID         : {engine_id}")
    print(f" Reasoning Engine  : {reasoning_engine_name}")
    print("==========================================================")
    
    token = get_access_token()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Register provisionedReasoningEngine agent under default_assistant
    agent_reg_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{engine_id}/assistants/default_assistant/agents"
    print(f"Registration Endpoint: {agent_reg_url}")
    
    agent_payload = {
        "displayName": "ECG Supervisor Agent",
        "description": f"Deployed via robust ADK architecture at {timestamp}",
        "adkAgentDefinition": {
             "provisionedReasoningEngine": {
                "reasoningEngine": reasoning_engine_name
             }
        }
    }
    
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    agent_req = urllib.request.Request(
        agent_reg_url,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": project_id,
            "Content-Type": "application/json"
        },
        data=json.dumps(agent_payload).encode("utf-8"),
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(agent_req, context=ssl_context) as resp:
            reg_resp = json.loads(resp.read().decode("utf-8"))
            print("✅ SUCCESS: Reasoning Engine agent registered in Gemini Enterprise!")
            print(f"   Registered Agent Name: {reg_resp.get('name')}")
            print(f"   Response Payload:\n{json.dumps(reg_resp, indent=2)}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"⚠️ Registration POST status {e.code}: {err_msg}")
        if e.code == 409 or "ALREADY_EXISTS" in err_msg:
            print("ℹ️ Agent definition already registered in default_assistant. Proceeding...")
        else:
            print(f"❌ Failed to register agent in Gemini Enterprise: {err_msg}", file=sys.stderr)

    # 2. Update default_assistant displayName
    assistant_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{engine_id}/assistants/default_assistant?update_mask=displayName"
    assistant_payload = {
        "name": f"projects/{project_id}/locations/global/collections/default_collection/engines/{engine_id}/assistants/default_assistant",
        "displayName": "ECG Supervisor Agent"
    }
    
    assistant_req = urllib.request.Request(
        assistant_url,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": project_id,
            "Content-Type": "application/json"
        },
        data=json.dumps(assistant_payload).encode("utf-8"),
        method="PATCH"
    )
    
    try:
        with urllib.request.urlopen(assistant_req, context=ssl_context) as resp:
            assistant_resp = json.loads(resp.read().decode("utf-8"))
            print("✅ SUCCESS: Discovery Engine default_assistant updated to 'ECG Supervisor Agent'!")
            print(f"   Assistant Name: {assistant_resp.get('name')}")
            print(f"   Display Name  : {assistant_resp.get('displayName')}")
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to patch default_assistant: {e.read().decode('utf-8')}", file=sys.stderr)

def main():
    args = parse_args()
    register_agent(args.project, args.engine_id, args.reasoning_engine)

if __name__ == "__main__":
    main()
