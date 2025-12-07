"""
Human-in-the-Loop Feedback Tool for Research Agent V2

This is the KEY INNOVATION of Workshop 2:
- Demonstrates that external feedback doesn't require additional APIs
- Human judgment is the most valuable form of external feedback
- Shows how tools can be human interactions, not just API calls

The reflection pattern (V1 -> feedback -> V2) relies on this tool
to collect real-world signals that break the prompt engineering plateau.

Demo Mode:
    Set AUTO_FEEDBACK=true in .env for non-interactive demos.
    This provides sample feedback automatically.
"""

import os
import sys
from typing import Any
from dotenv import load_dotenv

load_dotenv()

from claude_agent_sdk import tool

# Check for auto-feedback mode (non-interactive demos)
AUTO_FEEDBACK = os.getenv("AUTO_FEEDBACK", "").lower() in ("true", "1", "yes")


@tool(
    "request_human_review",
    """Request human review of the research output.

    USE WHEN:
    - Initial research is complete and needs validation
    - You want human judgment on research quality
    - Before finalizing a research report
    - When you're uncertain about the accuracy of your findings

    RETURNS:
    - rating: 1-5 quality score from human reviewer
    - feedback: Specific feedback on what to improve
    - missing_info: What information is missing that should be found
    - corrections: What information needs to be corrected
    - approved: Whether human approves the research (rating >= 4)

    This is EXTERNAL FEEDBACK - signals you cannot generate by reasoning alone.
    Human judgment catches errors that automated checks miss, including:
    - Factual inaccuracies you might not detect
    - Missing context that would improve the research
    - Quality issues that aren't obvious from the data
    - Real-world knowledge about the prospect or company

    INPUT:
    - research_summary: The research output to be reviewed
    - prospect_name: Name of the prospect being researched""",
    {"research_summary": str, "prospect_name": str}
)
async def request_human_review(args: dict[str, Any]) -> dict[str, Any]:
    """
    Collect human feedback via CLI during agent execution.

    This demonstrates human-in-the-loop as external feedback.
    The human reviewer provides signals that the LLM couldn't
    generate through reasoning alone.
    """
    research = args["research_summary"]
    prospect = args["prospect_name"]

    # Display the research for review
    print(f"\n{'='*60}")
    print(f"  HUMAN REVIEW REQUESTED")
    print(f"{'='*60}")
    print(f"\nProspect: {prospect}")
    print(f"\n--- Research Summary ---")
    print(research)
    print(f"\n{'='*60}")

    # AUTO_FEEDBACK mode for non-interactive demos
    if AUTO_FEEDBACK:
        print("\n  [AUTO_FEEDBACK mode] Generating sample feedback...")
        print("  (Set AUTO_FEEDBACK=false in .env for interactive mode)\n")

        # Provide realistic demo feedback that demonstrates the reflection pattern
        auto_result = {
            "rating": 3,
            "feedback": "Add more specific pain points for their industry",
            "missing_info": "Missing recent news about the company's market position",
            "corrections": None,
            "approved": False
        }

        print(f"  Auto-generated feedback:")
        print(f"    Rating: {auto_result['rating']}/5 (Needs improvement)")
        print(f"    Improvements: {auto_result['feedback']}")
        print(f"    Missing: {auto_result['missing_info']}")

        response_text = f"""Human Review Feedback for {prospect}:
- Rating: {auto_result['rating']}/5
- Approved: No - needs improvement
- Improvement suggestions: {auto_result['feedback']}
- Missing information: {auto_result['missing_info']}"""

        return {
            "content": [{
                "type": "text",
                "text": response_text
            }]
        }

    # Interactive mode - collect structured feedback from human
    print("\nPlease review the research above and provide feedback:")
    print("(This is EXTERNAL FEEDBACK that helps improve the research)\n")

    rating = input("  Rating (1-5, or 'skip' for auto-approve): ").strip()

    if rating.lower() == 'skip':
        # Skip mode for faster demos - still counts as external feedback
        print("\n  Skipped - auto-approving with no specific feedback")
        return {
            "content": [{
                "type": "text",
                "text": "Human review: Auto-approved (skipped). No specific feedback provided. The research can proceed as-is."
            }]
        }

    # Parse rating
    try:
        rating_int = int(rating) if rating.isdigit() else 3
        rating_int = max(1, min(5, rating_int))  # Clamp to 1-5
    except ValueError:
        rating_int = 3

    # Collect detailed feedback
    print(f"\n  Your rating: {rating_int}/5")

    feedback = input("  What could be improved? (or 'none'): ").strip()
    missing = input("  What's missing? (or 'none'): ").strip()
    corrections = input("  Any corrections needed? (or 'none'): ").strip()

    # Build structured result
    result = {
        "rating": rating_int,
        "feedback": feedback if feedback.lower() not in ['none', 'n', ''] else None,
        "missing_info": missing if missing.lower() not in ['none', 'n', ''] else None,
        "corrections": corrections if corrections.lower() not in ['none', 'n', ''] else None,
        "approved": rating_int >= 4
    }

    # Provide summary
    print(f"\n  Feedback collected:")
    print(f"    Rating: {rating_int}/5 {'(Approved)' if result['approved'] else '(Needs improvement)'}")
    if result['feedback']:
        print(f"    Improvements: {result['feedback']}")
    if result['missing_info']:
        print(f"    Missing: {result['missing_info']}")
    if result['corrections']:
        print(f"    Corrections: {result['corrections']}")

    # Build response text for Claude
    response_parts = [f"Human Review Feedback for {prospect}:"]
    response_parts.append(f"- Rating: {rating_int}/5")
    response_parts.append(f"- Approved: {'Yes' if result['approved'] else 'No - needs improvement'}")

    if result['feedback']:
        response_parts.append(f"- Improvement suggestions: {result['feedback']}")
    if result['missing_info']:
        response_parts.append(f"- Missing information: {result['missing_info']}")
    if result['corrections']:
        response_parts.append(f"- Corrections needed: {result['corrections']}")

    if not any([result['feedback'], result['missing_info'], result['corrections']]):
        response_parts.append("- No specific issues identified")

    # Return in MCP tool result format
    return {
        "content": [{
            "type": "text",
            "text": "\n".join(response_parts)
        }]
    }
