"""
AGENT WITH SDK: Claude Agent SDK Implementation

This file demonstrates the Claude Agent SDK approach.
With observability enabled (Laminar), you can see:

1. Full conversation history (including what you don't see)
2. System prompts
3. Tool definitions and executions
4. Actual token counts (not just what ResultMessage reports)
5. Real costs

Compare this with agent_raw_api.py to see what the SDK abstracts away.

Usage:
    python agent_with_sdk.py
"""

import os
import asyncio
import requests
from typing import Any
from dotenv import load_dotenv

from lmnr import Laminar, observe
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    tool,
    AssistantMessage,
    UserMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

ENRICHLAYER_API_KEY = os.getenv("ENRICHLAYER_API_KEY")

SYSTEM_PROMPT = """You are an AI sales assistant specializing in LinkedIn research.

Your goal: Research a prospect and provide a brief summary.

Available tools:
- fetch_linkedin_profile: Fetches profile data from LinkedIn URLs

Instructions:
1. Use fetch_linkedin_profile to get the profile data
2. Provide a brief summary of the person (name, role, company)
3. Keep your response concise
"""


# ============================================================================
# TOOL DEFINITION
# ============================================================================

@tool(
    "fetch_linkedin_profile",
    "Fetch LinkedIn profile data from a URL. Returns profile information including name, title, company.",
    {"profile_url": str}
)
async def fetch_linkedin_profile(args: dict[str, Any]) -> dict[str, Any]:
    """Custom tool for fetching LinkedIn profiles."""
    profile_url = args["profile_url"]
    print(f"  [Tool] Fetching profile: {profile_url}")

    try:
        response = requests.get(
            "https://enrichlayer.com/api/v2/profile",
            params={"profile_url": profile_url},
            headers={"Authorization": f"Bearer {ENRICHLAYER_API_KEY}"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"  [Tool] Success! Found: {data.get('first_name', 'Unknown')}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Profile data:\n{response.text[:1000]}"
                }]
            }
        else:
            error = f"API error {response.status_code}: {response.text[:200]}"
            print(f"  [Tool] Error: {error}")
            return {"content": [{"type": "text", "text": error}], "is_error": True}

    except Exception as e:
        print(f"  [Tool] Exception: {str(e)}")
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "is_error": True}


# ============================================================================
# MESSAGE DISPLAY
# ============================================================================

def display_message(msg):
    """Display agent messages."""
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                preview = block.text[:200] + "..." if len(block.text) > 200 else block.text
                print(f"\n  Agent: {preview}")
            elif isinstance(block, ToolUseBlock):
                print(f"\n  Tool call: {block.name}")
                print(f"  Input: {block.input}")

    elif isinstance(msg, ResultMessage):
        if msg.total_cost_usd:
            print(f"\n  Cost (reported): ${msg.total_cost_usd:.6f}")


# ============================================================================
# AGENT WITH LAMINAR OBSERVABILITY
# ============================================================================

@observe()  # Laminar decorator - traces everything inside
async def research_with_sdk(linkedin_url: str) -> dict:
    """
    Research a prospect using Claude Agent SDK.

    The @observe() decorator tells Laminar to trace all SDK interactions.
    Check laminar.run to see:
    - Full prompts (including system prompt)
    - Complete conversation history
    - Tool calls with inputs AND outputs
    - Real token counts (often 10-50x what you expect!)
    """
    print(f"\n{'='*70}")
    print("CLAUDE AGENT SDK + LAMINAR OBSERVABILITY")
    print(f"{'='*70}")
    print(f"URL: {linkedin_url}")

    # Create MCP server with our tool
    linkedin_server = create_sdk_mcp_server(
        name="linkedin",
        version="1.0.0",
        tools=[fetch_linkedin_profile]
    )

    options = ClaudeAgentOptions(
        mcp_servers={"linkedin": linkedin_server},
        allowed_tools=["mcp__linkedin__fetch_linkedin_profile"],
        system_prompt=SYSTEM_PROMPT,
        max_turns=5,
    )

    prompt = f"""Research this LinkedIn profile and provide a brief summary:

LinkedIn URL: {linkedin_url}

Fetch the profile and tell me about this person."""

    print(f"\n[PROMPT]")
    print(f"  {prompt[:200]}...")

    metrics = {
        "turns": 0,
        "tool_calls": [],
        "reported_cost": 0,
        "final_response": ""
    }

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)

        async for msg in client.receive_response():
            display_message(msg)

            if isinstance(msg, AssistantMessage):
                metrics["turns"] += 1
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        metrics["final_response"] = block.text
                    elif isinstance(block, ToolUseBlock):
                        metrics["tool_calls"].append({
                            "tool": block.name,
                            "input": block.input
                        })

            elif isinstance(msg, ResultMessage):
                if msg.total_cost_usd:
                    metrics["reported_cost"] = msg.total_cost_usd

    print(f"\n{'='*70}")
    print("SDK METRICS (what the SDK reports)")
    print(f"{'='*70}")
    print(f"  Turns: {metrics['turns']}")
    print(f"  Tool calls: {len(metrics['tool_calls'])}")
    print(f"  Reported cost: ${metrics['reported_cost']:.6f}")
    print(f"\n  NOTE: Check Laminar for REAL token counts!")
    print(f"  The SDK reports partial metrics. Laminar sees everything.")

    return metrics


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run the SDK agent with Laminar observability."""

    # Initialize Laminar
    api_key = os.getenv("LAMINAR_API_KEY")
    if not api_key:
        print("ERROR: LAMINAR_API_KEY not set in .env")
        print("Get your key at: https://www.laminar.run")
        return

    print("\n" + "#"*70)
    print("# CLAUDE AGENT SDK + LAMINAR")
    print("# SDK abstracts complexity, Laminar shows what really happens")
    print("#"*70)

    print("\n  [Laminar] Initializing...")
    Laminar.initialize(project_api_key=api_key)
    print("  [Laminar] Ready! Traces at: https://www.laminar.run")

    linkedin_url = "https://www.linkedin.com/in/jenhsunhuang/"
    metrics = await research_with_sdk(linkedin_url)

    print(f"\n{'='*70}")
    print("FINAL RESPONSE")
    print(f"{'='*70}")
    print(metrics.get("final_response", "No response"))

    print(f"\n{'='*70}")
    print("NEXT STEP")
    print(f"{'='*70}")
    print("Go to https://www.laminar.run to see the REAL metrics:")
    print("  - Actual input tokens (includes system prompt, history, tools)")
    print("  - Actual output tokens")
    print("  - Real cost breakdown")
    print("  - Full conversation timeline")

    return metrics


if __name__ == "__main__":
    asyncio.run(main())
