"""
AGENT WITHOUT SDK: Direct Anthropic API Implementation

This file demonstrates building an agent using the RAW Anthropic API
instead of the Claude Agent SDK. This shows students exactly what
happens "under the hood":

1. How conversation history accumulates
2. How tool definitions are sent with each request
3. How the agentic loop works (LLM -> tool -> LLM -> tool -> ...)
4. Why token counts grow so quickly
5. The exact JSON being sent to/from the API

Key Insight: This is what the SDK abstracts away. Understanding this
helps you debug agents and optimize costs.

Observability:
    This file uses Laminar's automatic instrumentation to trace all
    Anthropic API calls. View traces at https://www.laminar.run

Usage:
    python agent_raw_api.py
"""

import os
import json
import requests
from typing import Any
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Initialize Laminar BEFORE importing anthropic
# This enables automatic instrumentation of all Anthropic API calls
from lmnr import Laminar, Instruments, observe

_laminar_api_key = os.getenv("LAMINAR_API_KEY")
if _laminar_api_key:
    Laminar.initialize(
        project_api_key=_laminar_api_key,
        instruments={Instruments.ANTHROPIC}
    )
    print("  [Laminar] Raw API tracing enabled")
else:
    print("  [Laminar] Not configured - set LAMINAR_API_KEY for tracing")

# Now import anthropic (AFTER Laminar.initialize for auto-instrumentation)
import anthropic

# ============================================================================
# CONFIGURATION
# ============================================================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ENRICHLAYER_API_KEY = os.getenv("ENRICHLAYER_API_KEY")
MODEL = "claude-sonnet-4-20250514"
MAX_TURNS = 5

# ============================================================================
# TOOL DEFINITION (what we send to the API)
# ============================================================================

TOOLS = [
    {
        "name": "fetch_linkedin_profile",
        "description": "Fetch LinkedIn profile data from a URL. Returns profile information including name, title, company, and work history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_url": {
                    "type": "string",
                    "description": "The LinkedIn profile URL to fetch"
                }
            },
            "required": ["profile_url"]
        }
    }
]

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
# TOOL EXECUTION (we handle this ourselves)
# ============================================================================

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a tool and return the result.

    In the SDK, this is handled automatically. Here we do it manually
    so students can see exactly what's happening.
    """
    print(f"\n  [TOOL EXECUTION]")
    print(f"  Tool: {tool_name}")
    print(f"  Input: {json.dumps(tool_input, indent=2)}")

    if tool_name == "fetch_linkedin_profile":
        profile_url = tool_input.get("profile_url", "")

        try:
            response = requests.get(
                "https://enrichlayer.com/api/v2/profile",
                params={"profile_url": profile_url},
                headers={"Authorization": f"Bearer {ENRICHLAYER_API_KEY}"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                result = f"Profile found: {data.get('first_name', 'Unknown')} {data.get('last_name', '')}"
                result += f"\nTitle: {data.get('occupation', 'Unknown')}"
                result += f"\nCompany: {data.get('company', 'Unknown')}"
                print(f"  Result: SUCCESS - {data.get('first_name', 'Unknown')}")
                return json.dumps(data)
            else:
                error = f"API error {response.status_code}: {response.text[:200]}"
                print(f"  Result: ERROR - {error}")
                return error

        except Exception as e:
            error = f"Exception: {str(e)}"
            print(f"  Result: ERROR - {error}")
            return error

    return f"Unknown tool: {tool_name}"


# ============================================================================
# THE AGENTIC LOOP (what the SDK does for you)
# ============================================================================

@observe(name="raw_api_research")
def run_agent(user_prompt: str, debug: bool = True) -> dict:
    """
    Run an agentic loop using the raw Anthropic API.

    This shows exactly what happens inside an agent:
    1. Send messages + tools to API
    2. If response has tool_use, execute tool
    3. Add tool result to messages
    4. Repeat until no more tool calls

    Returns metrics about the conversation.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Initialize conversation history
    messages = [
        {"role": "user", "content": user_prompt}
    ]

    # Metrics tracking
    metrics = {
        "turns": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "tool_calls": [],
        "api_calls": []
    }

    print(f"\n{'='*70}")
    print("RAW API AGENT - SEE WHAT HAPPENS UNDER THE HOOD")
    print(f"{'='*70}")

    if debug:
        print(f"\n[INITIAL PROMPT]")
        print(f"  {user_prompt[:200]}...")
        print(f"\n[SYSTEM PROMPT]")
        print(f"  {SYSTEM_PROMPT[:200]}...")
        print(f"\n[TOOLS SENT TO API]")
        print(f"  {len(TOOLS)} tool(s): {[t['name'] for t in TOOLS]}")

    # The agentic loop
    for turn in range(MAX_TURNS):
        metrics["turns"] += 1

        print(f"\n{'─'*70}")
        print(f"TURN {turn + 1}")
        print(f"{'─'*70}")

        if debug:
            # Show what we're sending
            total_message_chars = sum(
                len(json.dumps(m)) for m in messages
            )
            print(f"\n[API REQUEST]")
            print(f"  Messages in history: {len(messages)}")
            print(f"  Approx message size: {total_message_chars:,} chars")
            print(f"  Tools included: Yes ({len(TOOLS)} tools)")

        # Make API call
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        # Track tokens
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        metrics["total_input_tokens"] += input_tokens
        metrics["total_output_tokens"] += output_tokens

        metrics["api_calls"].append({
            "turn": turn + 1,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "stop_reason": response.stop_reason
        })

        if debug:
            print(f"\n[API RESPONSE]")
            print(f"  Input tokens: {input_tokens:,}")
            print(f"  Output tokens: {output_tokens:,}")
            print(f"  Stop reason: {response.stop_reason}")

        # Process response content
        assistant_content = []
        tool_use_blocks = []
        text_response = ""

        for block in response.content:
            if block.type == "text":
                text_response = block.text
                assistant_content.append({"type": "text", "text": block.text})
                if debug:
                    print(f"\n[LLM TEXT OUTPUT]")
                    preview = block.text[:300] + "..." if len(block.text) > 300 else block.text
                    print(f"  {preview}")

            elif block.type == "tool_use":
                tool_use_blocks.append(block)
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                metrics["tool_calls"].append({
                    "turn": turn + 1,
                    "tool": block.name,
                    "input": block.input
                })

        # Add assistant message to history
        messages.append({"role": "assistant", "content": assistant_content})

        # If no tool calls, we're done
        if response.stop_reason == "end_turn" or not tool_use_blocks:
            print(f"\n[AGENT COMPLETE]")
            print(f"  Reason: {response.stop_reason}")
            break

        # Execute tools and add results
        tool_results = []
        for tool_block in tool_use_blocks:
            result = execute_tool(tool_block.name, tool_block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": result
            })

        # Add tool results to conversation
        messages.append({"role": "user", "content": tool_results})

        if debug:
            print(f"\n[CONVERSATION HISTORY NOW]")
            print(f"  Total messages: {len(messages)}")
            for i, msg in enumerate(messages):
                role = msg["role"]
                content_types = []
                if isinstance(msg["content"], list):
                    content_types = [c.get("type", "text") for c in msg["content"]]
                else:
                    content_types = ["text"]
                print(f"    {i+1}. [{role}] {content_types}")

    # Final summary
    print(f"\n{'='*70}")
    print("AGENT METRICS SUMMARY")
    print(f"{'='*70}")
    print(f"  Total turns: {metrics['turns']}")
    print(f"  Total input tokens: {metrics['total_input_tokens']:,}")
    print(f"  Total output tokens: {metrics['total_output_tokens']:,}")
    print(f"  Total tokens: {metrics['total_input_tokens'] + metrics['total_output_tokens']:,}")
    print(f"  Tool calls: {len(metrics['tool_calls'])}")

    # Cost estimate (Claude Sonnet pricing)
    input_cost = metrics['total_input_tokens'] * 0.003 / 1000
    output_cost = metrics['total_output_tokens'] * 0.015 / 1000
    total_cost = input_cost + output_cost
    print(f"  Estimated cost: ${total_cost:.6f}")

    print(f"\n[TOKEN BREAKDOWN BY TURN]")
    for call in metrics["api_calls"]:
        print(f"  Turn {call['turn']}: {call['input_tokens']:,} in / {call['output_tokens']:,} out")

    metrics["final_response"] = text_response
    metrics["total_cost_usd"] = total_cost

    return metrics


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the raw API agent."""
    linkedin_url = "https://www.linkedin.com/in/jenhsunhuang/"

    prompt = f"""Research this LinkedIn profile and provide a brief summary:

LinkedIn URL: {linkedin_url}

Fetch the profile and tell me about this person."""

    print("\n" + "#"*70)
    print("# RAW ANTHROPIC API AGENT")
    print("# No SDK - See exactly what happens under the hood")
    print("#"*70)

    metrics = run_agent(prompt, debug=True)

    print(f"\n{'='*70}")
    print("FINAL RESPONSE")
    print(f"{'='*70}")
    print(metrics.get("final_response", "No response"))

    return metrics


if __name__ == "__main__":
    main()
