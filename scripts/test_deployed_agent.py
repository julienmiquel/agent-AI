"""Test Deployed Agent Engine Agent.

Sends a test prompt to the deployed Reasoning Engine / Agent Engine instance
and prints the streamed events and response.
"""

import sys
import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "ml-demo-384110"
LOCATION = "us-central1"
AGENT_RESOURCE_NAME = "projects/1008225662928/locations/us-central1/reasoningEngines/3783377179979546624"

def main():
    print(f"Connecting to deployed Agent Engine resource:\n  {AGENT_RESOURCE_NAME}")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    agent = reasoning_engines.ReasoningEngine(AGENT_RESOURCE_NAME)
    
    user_prompt = "Dutch booking lag in Mediterranean South vs last year"
    user_id = "julien_test_user"
    
    print(f"\nSending Query: '{user_prompt}' (User ID: {user_id})...\n")
    
    try:
        response_stream = agent.stream_query(
            message=user_prompt,
            user_id=user_id,
        )
        print("=== STREAMED AGENT RESPONSE ===")
        for event in response_stream:
            print(event)
        print("\n===============================")
        print("SUCCESS: Deployed agent execution completed!")
    except Exception as e:
        print(f"ERROR executing query against deployed agent: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
