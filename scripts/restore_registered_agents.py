#!/usr/bin/env python3
"""Restores and registers all required Company agents in Gemini Enterprise.

Re-creates:
1. Company PMS (Resalys Inventory Assistant)
2. Company Marketing CRM (CRM Flash Campaign Assistant)
3. company_analytics (BigQuery Analytics Assistant)
4. Company (Base Company Assistant)

Usage:
    python3 scripts/restore_registered_agents.py [--project PROJECT] [--engine-id ENGINE_ID]
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
REASONING_ENGINE_NAME = "projects/1008225662928/locations/us-central1/reasoningEngines/3550315899263123456"

def parse_args():
    parser = argparse.ArgumentParser(description="Restore Company Agents in Gemini Enterprise")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP Project ID")
    parser.add_argument("--engine-id", default=DEFAULT_ENGINE_ID, help="Gemini Enterprise Engine ID")
    return parser.parse_args()

def get_access_token() -> str:
    res = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True)
    return res.stdout.strip()

def restore_agent(project_id: str, engine_id: str, display_name: str, description: str, re_name: str = None) -> dict:
    token = get_access_token()
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{engine_id}/assistants/default_assistant/agents"
    
    payload = {
        "displayName": display_name,
        "description": description,
    }
    if re_name:
        payload["adkAgentDefinition"] = {
            "provisionedReasoningEngine": {
                "reasoningEngine": re_name
            }
        }

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": project_id,
            "Content-Type": "application/json"
        },
        data=json.dumps(payload).encode("utf-8"),
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"✅ Successfully restored agent '{display_name}' (ID: {data.get('name', '').split('/')[-1]})")
            return data
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"⚠️ Failed to restore '{display_name}': status {e.code} - {err_body}")
        return {}

def main():
    args = parse_args()
    print("==========================================================")
    print(" Restoring Agents in Gemini Enterprise Instance")
    print(f" Project ID  : {args.project}")
    print(f" Engine ID   : {args.engine_id}")
    print("==========================================================")

    agents_to_restore = [
        ("Company PMS", "Assistant Company d'inventaire PMS Resalys", REASONING_ENGINE_NAME),
        ("Company Marketing CRM", "Assistant Company de gestion des campagnes marketing CRM", REASONING_ENGINE_NAME),
        ("company_analytics", "Assistant Company d'analyse des données BigQuery & Yield Analytics", REASONING_ENGINE_NAME),
        ("Company", "Assistant Company Général", REASONING_ENGINE_NAME),
    ]

    for name, desc, re_path in agents_to_restore:
        restore_agent(args.project, args.engine_id, name, desc, re_path)

if __name__ == "__main__":
    main()
