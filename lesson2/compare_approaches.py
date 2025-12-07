"""
COMPARISON: Raw API vs SDK with Laminar Observability

This script runs both approaches and compares:
1. Raw Anthropic API (full visibility, manual work)
2. Claude Agent SDK with Laminar (abstracted, auto-traced)

Key Learning:
- Raw API shows you EXACTLY what's happening
- SDK abstracts the complexity but hides details
- Laminar reveals what the SDK is hiding

Usage:
    python compare_approaches.py
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


def print_separator(title: str):
    print(f"\n{'#'*70}")
    print(f"# {title}")
    print(f"{'#'*70}\n")


async def run_comparison():
    """Run both approaches and compare results."""

    linkedin_url = "https://www.linkedin.com/in/jenhsunhuang/"

    print_separator("APPROACH COMPARISON: Raw API vs SDK + Laminar")
    print("This comparison shows what the SDK abstracts away.")
    print("We'll run the same task with both approaches.\n")

    results = {}

    # ========================================
    # APPROACH 1: Raw Anthropic API
    # ========================================
    print_separator("APPROACH 1: RAW ANTHROPIC API")
    print("- Full control and visibility")
    print("- You manage conversation history")
    print("- You handle tool execution")
    print("- You see exact token counts")
    print("-" * 50)

    from agent_raw_api import run_agent

    prompt = f"""Research this LinkedIn profile and provide a brief summary:

LinkedIn URL: {linkedin_url}

Fetch the profile and tell me about this person."""

    raw_metrics = run_agent(prompt, debug=True)
    results["raw_api"] = raw_metrics

    # ========================================
    # APPROACH 2: SDK with Laminar
    # ========================================
    print_separator("APPROACH 2: CLAUDE AGENT SDK + LAMINAR")
    print("- SDK handles complexity")
    print("- Laminar reveals what's hidden")
    print("- Same functionality, less code")
    print("-" * 50)

    # Initialize Laminar
    from lmnr import Laminar
    api_key = os.getenv("LAMINAR_API_KEY")
    if api_key:
        Laminar.initialize(project_api_key=api_key)
        print("  [Laminar] Initialized for full observability")

    from agent_with_sdk import research_with_sdk
    sdk_metrics = await research_with_sdk(linkedin_url)
    results["sdk_laminar"] = sdk_metrics

    # ========================================
    # COMPARISON SUMMARY
    # ========================================
    print_separator("COMPARISON SUMMARY")

    print("┌" + "─"*68 + "┐")
    print("│ {:^66} │".format("METRIC COMPARISON"))
    print("├" + "─"*34 + "┬" + "─"*33 + "┤")
    print("│ {:^32} │ {:^31} │".format("Raw API", "SDK + Laminar"))
    print("├" + "─"*34 + "┼" + "─"*33 + "┤")

    # Turns
    raw_turns = raw_metrics.get("turns", "?")
    sdk_turns = sdk_metrics.get("turns", "?")
    print("│ Turns: {:>25} │ Turns: {:>23} │".format(raw_turns, sdk_turns))

    # Tool calls
    raw_tools = len(raw_metrics.get("tool_calls", []))
    sdk_tools = len(sdk_metrics.get("tool_calls", []))
    print("│ Tool calls: {:>20} │ Tool calls: {:>18} │".format(raw_tools, sdk_tools))

    # Tokens (Raw API has real counts, SDK has partial)
    raw_input = raw_metrics.get("total_input_tokens", 0)
    raw_output = raw_metrics.get("total_output_tokens", 0)
    print("│ Input tokens: {:>18,} │ Input tokens: {:>16} │".format(raw_input, "See Laminar"))
    print("│ Output tokens: {:>17,} │ Output tokens: {:>15} │".format(raw_output, "See Laminar"))

    # Cost
    raw_cost = raw_metrics.get("total_cost_usd", 0)
    sdk_cost = sdk_metrics.get("reported_cost", 0)
    print("│ Cost: ${:>25.6f} │ Cost (reported): ${:>11.6f} │".format(raw_cost, sdk_cost))

    print("└" + "─"*34 + "┴" + "─"*33 + "┘")

    # Key insights
    print("\n" + "="*70)
    print("KEY INSIGHTS")
    print("="*70)

    print("""
1. TOKEN COUNT DIFFERENCE
   - Raw API shows exact tokens sent/received
   - SDK reports partial metrics
   - Laminar reveals the TRUE token count (often 10-50x higher!)

2. WHAT THE SDK HIDES
   - System prompt (~1,000 tokens)
   - Tool definitions (~2,000+ tokens per tool)
   - Conversation history (accumulates each turn)
   - Internal message formatting

3. WHEN TO USE EACH
   - Raw API: Learning, debugging, cost optimization
   - SDK + Laminar: Production with full visibility
   - SDK alone: Quick prototypes (but you're flying blind)

4. CHECK LAMINAR NOW
   Go to https://www.laminar.run to see:
   - The REAL token counts
   - Full conversation history
   - What the SDK is actually sending to Claude
""")

    return results


def main():
    """Run the comparison."""
    asyncio.run(run_comparison())


if __name__ == "__main__":
    main()
