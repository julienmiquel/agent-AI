#!/usr/bin/env python3
"""Unified Automated Deployment, Verification, and Registration Pipeline.

1. Updates the EXISTING Vertex AI Agent Engine instance in-place (or creates if none exists).
2. Runs post-deployment verification suite against the updated reasoning engine.
3. Registers/updates the reasoning engine in Gemini Enterprise instance.

Usage:
    python3 scripts/pipeline.py [--project PROJECT] [--region REGION] [--engine-id ENGINE_ID] [--reasoning-engine-id REASONING_ENGINE_ID]
"""

import sys
import os
import argparse
import subprocess
import re

DEFAULT_PROJECT = os.environ.get("GCP_PROJECT_ID", "ml-demo-384110")
DEFAULT_REGION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
DEFAULT_ENGINE_ID = os.environ.get("GEMINI_ENTERPRISE_ENGINE_ID", "gemini-enterprise-ecg_1784557637596")
ID_FILE_PATH = ".agent_engine_id"

def get_default_reasoning_engine_id() -> str:
    if os.environ.get("REASONING_ENGINE_ID"):
        return os.environ["REASONING_ENGINE_ID"].strip()
    if os.path.exists(ID_FILE_PATH):
        try:
            with open(ID_FILE_PATH, "r") as f:
                val = f.read().strip()
                if val:
                    return val
        except Exception:
            pass
    return "6630778044384542720"

def save_reasoning_engine_id(re_id: str):
    try:
        with open(ID_FILE_PATH, "w") as f:
            f.write(re_id.strip() + "\n")
    except Exception as e:
        print(f"Warning: Could not save .agent_engine_id: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description="Unified Deployment, Verification & Registration Pipeline")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP Project ID")
    parser.add_argument("--region", default=DEFAULT_REGION, help="GCP Region")
    parser.add_argument("--engine-id", default=DEFAULT_ENGINE_ID, help="Gemini Enterprise Engine ID")
    parser.add_argument("--reasoning-engine-id", default=get_default_reasoning_engine_id(), help="Reasoning Engine ID to update in-place")
    return parser.parse_args()

def run_step_1_deploy(project: str, region: str, re_id: str) -> str:
    print("\n==================================================================")
    print(f" [Step 1/3] Updating Agent Engine Instance in-place: {re_id}")
    print("==================================================================")
    
    adk_bin = ".venv/bin/adk" if os.path.exists(".venv/bin/adk") else "adk"
    session_uri = f"agentengine://projects/{project}/locations/{region}/reasoningEngines/{re_id}"
    
    cmd = [
        adk_bin, "deploy", "agent_engine",
        f"--project={project}",
        f"--region={region}",
        f"--agent_engine_id={re_id}",
        f"--session_service_uri={session_uri}",
        "--display_name=ECG Supervisor Agent",
        "agent_ecg"
    ]
    
    print(f"Running: {' '.join(cmd)}\n")
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    captured_output = []
    
    for line in iter(process.stdout.readline, ""):
        print(line, end="")
        captured_output.append(line)
        
    process.wait()
    full_output = "".join(captured_output)
    
    if process.returncode != 0:
        print(f"\n❌ Deployment update failed with exit code {process.returncode}", file=sys.stderr)
        sys.exit(1)
        
    match = re.search(r'Deployed to Agent Platform:\s*(projects/\S+)', full_output)
    if not match:
        match = re.search(r'Created a new instance:\s*(projects/\S+)', full_output)
        
    if match:
        re_resource_name = match.group(1).strip()
    else:
        re_resource_name = f"projects/{project}/locations/{region}/reasoningEngines/{re_id}"
        
    # Extract numerical ID if full resource name returned
    if "/" in re_resource_name:
        extracted_id = re_resource_name.split("/")[-1]
        save_reasoning_engine_id(extracted_id)
        
    print(f"\n✅ SUCCESS: Agent Engine Updated In-Place: {re_resource_name}\n")
    return re_resource_name

def run_step_2_verify(re_resource_name: str, project: str, region: str):
    print("==================================================================")
    print(" [Step 2/3] Executing Post-Deployment Verification Suite")
    print("==================================================================")
    
    python_bin = ".venv/bin/python3" if os.path.exists(".venv/bin/python3") else sys.executable
    cmd = [
        python_bin, "scripts/verify_deployment.py",
        f"--resource-name={re_resource_name}",
        f"--project={project}",
        f"--region={region}"
    ]
    
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"\n❌ Verification failed for {re_resource_name}", file=sys.stderr)
        sys.exit(1)

def run_step_3_register(re_resource_name: str, project: str, engine_id: str):
    print("==================================================================")
    print(" [Step 3/3] Registering Agent in Gemini Enterprise Instance")
    print("==================================================================")
    
    python_bin = ".venv/bin/python3" if os.path.exists(".venv/bin/python3") else sys.executable
    cmd = [
        python_bin, "scripts/register_agent_gemini_enterprise.py",
        f"--project={project}",
        f"--engine-id={engine_id}",
        f"--reasoning-engine={re_resource_name}"
    ]
    
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"\n❌ Registration failed for {re_resource_name}", file=sys.stderr)
        sys.exit(1)

def main():
    args = parse_args()
    re_id = args.reasoning_engine_id.split("/")[-1]
    
    print("==================================================================")
    print(" 🚀 ECG Agent In-Place Update, Verification & Registration")
    print("==================================================================")
    print(f" Project ID          : {args.project}")
    print(f" Region              : {args.region}")
    print(f" Engine ID           : {args.engine_id}")
    print(f" Target Agent Engine : {re_id}")
    print("------------------------------------------------------------------")
    
    re_resource_name = run_step_1_deploy(args.project, args.region, re_id)
    run_step_2_verify(re_resource_name, args.project, args.region)
    run_step_3_register(re_resource_name, args.project, args.engine_id)
    
    print("\n==================================================================")
    print(" 🎉 IN-PLACE UPDATE PIPELINE COMPLETED SUCCESSFULLY!")
    print(f" Updated Resource  : {re_resource_name}")
    print(f" Registered Engine : {args.engine_id}")
    print("==================================================================\n")

if __name__ == "__main__":
    main()
