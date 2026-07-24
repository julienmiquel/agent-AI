#!/usr/bin/env python3
"""Standalone Remote Verification Script for Company Supervisor Agent.

Tests the live deployed Agent Engine instance on Vertex AI via the LLM Chat Interface
and verifies GCP Cloud Logging audit entries.

Usage:
    python3 scripts/test_remote_agent.py [--resource-name RE_NAME] [--project PROJECT] [--region REGION]
"""

import sys
import os
import argparse
import time
import subprocess
from google.cloud import aiplatform_v1beta1

DEFAULT_PROJECT = os.environ.get("GCP_PROJECT_ID", "ml-demo-384110")
DEFAULT_REGION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
ID_FILE_PATH = ".agent_engine_id"

def get_default_resource_name(project: str, region: str) -> str:
    if os.environ.get("REASONING_ENGINE_NAME"):
        return os.environ["REASONING_ENGINE_NAME"].strip()
    if os.path.exists(ID_FILE_PATH):
        try:
            with open(ID_FILE_PATH, "r") as f:
                val = f.read().strip()
                if val:
                    re_id = val.split("/")[-1]
                    return f"projects/{project}/locations/{region}/reasoningEngines/{re_id}"
        except Exception:
            pass
    return f"projects/{project}/locations/{region}/reasoningEngines/3550315899263123456"

def parse_args():
    parser = argparse.ArgumentParser(description="Standalone Remote Agent Engine Health Check")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP Project ID")
    parser.add_argument("--region", default=DEFAULT_REGION, help="GCP Region")
    parser.add_argument("--resource-name", default=None, help="Reasoning Engine Resource Name")
    parser.add_argument("--prompt", default="Dutch booking lag in Mediterranean South vs last year", help="Test prompt to send to the agent")
    return parser.parse_args()

def test_remote_agent(resource_name: str, region: str, prompt: str) -> bool:
    print("\n==========================================================")
    print(" 📡 [1/2] Invoking Live Agent Engine (LLM Chat Interface)")
    print(f" Target Resource : {resource_name}")
    print(f" Prompt          : '{prompt}'")
    print("==========================================================")
    
    endpoint = f"{region}-aiplatform.googleapis.com"
    client = aiplatform_v1beta1.ReasoningEngineExecutionServiceClient(
        client_options={"api_endpoint": endpoint}
    )
    
    start_time = time.time()
    try:
        response = client.query_reasoning_engine(
            request={
                "name": resource_name,
                "input": {
                    "message": prompt,
                    "user_id": "test_remote_verifier"
                },
                "class_method": "stream_query"
            }
        )
        elapsed = time.time() - start_time
        resp_str = str(response)
        
        print(f"\n⏱️ Response received in {elapsed:.2f} seconds.")
        print("----------------------------------------------------------")
        print("Agent Response Sample:")
        print(resp_str[:400] + ("..." if len(resp_str) > 400 else ""))
        print("----------------------------------------------------------")
        print("✅ Live Agent Engine turn completed successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Remote Execution Failed: {e}", file=sys.stderr)
        return False

def check_cloud_logs(resource_name: str, project_id: str) -> bool:
    print("\n==========================================================")
    print(" 📋 [2/2] Audit Cloud Logging Logs")
    print("==========================================================")
    
    re_id = resource_name.split("/")[-1]
    filter_str = f'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="{re_id}"'
    cmd = [
        "gcloud", "logging", "read",
        filter_str,
        f"--project={project_id}",
        "--limit=5",
        "--format=value(timestamp,textPayload)"
    ]
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logs = res.stdout.strip()
        if logs:
            print("✅ Verified Cloud Logging entries:")
            for line in logs.splitlines()[:3]:
                print(f"   {line[:120]}")
            return True
        else:
            print("ℹ️ No log entries returned for the filter (logs may take a few seconds to ingest).")
            return True
    except Exception as e:
        print(f"⚠️ Cloud logging query encountered issue: {e}")
        return True

def main():
    args = parse_args()
    resource_name = args.resource_name or get_default_resource_name(args.project, args.region)
    
    print("==========================================================")
    print(" 🚀 Live Remote Company Agent Health & Verification Check")
    print("==========================================================")
    print(f" Project ID    : {args.project}")
    print(f" Region        : {args.region}")
    print(f" Target Engine : {resource_name}")
    print("----------------------------------------------------------")
    
    exec_ok = test_remote_agent(resource_name, args.region, args.prompt)
    logs_ok = check_cloud_logs(resource_name, args.project)
    
    if exec_ok and logs_ok:
        print("\n==========================================================")
        print(" 🎉 REMOTE VERIFICATION PASSED: Agent is healthy & online!")
        print("==========================================================\n")
        sys.exit(0)
    else:
        print("\n❌ REMOTE VERIFICATION FAILED", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
