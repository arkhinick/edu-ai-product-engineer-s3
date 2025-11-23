"""
CHAINED WORKFLOW: LinkedIn Cold Outreach Generator

This is the "Script Follower" approach:
- Fixed sequence of steps
- No self-correction
- Breaks on unexpected inputs
- Fast and cheap, but brittle

Workflow:
1. Fetch LinkedIn profile (EnrichLayer API)
2. Extract required fields
3. Generate message (single LLM call)
4. Return result

Expected behavior:
- ✅ Works great on clean, well-formatted URLs
- ❌ Fails on typos, variations, missing data
"""

import os
import json
import requests
from anthropic import Anthropic
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

# Initialize clients
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
enrichlayer_api_key = os.getenv("ENRICHLAYER_API_KEY")


def fetch_linkedin_profile(url: str) -> Dict:
    """
    Step 1: Fetch profile data from EnrichLayer API

    Returns raw JSON response
    Raises exception if profile not found
    """
    print(f"  [Step 1] Fetching profile: {url}")

    response = requests.get(
        "https://enrichlayer.com/api/v2/profile",
        params={"profile_url": url},
        headers={"Authorization": f"Bearer {enrichlayer_api_key}"}
    )

    if response.status_code != 200:
        raise Exception(f"Profile fetch failed: {response.status_code} - {response.text}")

    return response.json()


def extract_profile_data(profile: Dict) -> Dict:
    """
    Step 2: Extract required fields

    Hardcoded extraction - NO ERROR HANDLING
    If fields are missing, this will crash
    """
    print(f"  [Step 2] Extracting data...")

    # Direct field access - will crash if missing
    first_name = profile["first_name"]
    company = profile["experiences"][0]["company"]
    description = profile["experiences"][0]["description"]

    # Determine if company is "Tech" for rap logic
    industry = profile.get("industry") or ""
    industry = industry.lower()
    headline = profile.get("headline", "").lower()
    company_lower = company.lower()

    is_tech = (
        "tech" in industry or "software" in industry or "computer" in industry or
        "tech" in headline or "software" in headline or "ai" in headline or
        "nvidia" in company_lower or "microsoft" in company_lower or "google" in company_lower
    )

    extracted = {
        "first_name": first_name,
        "company": company,
        "description": description,
        "is_tech": is_tech
    }

    print(f"    → Name: {first_name}, Company: {company}, Tech: {is_tech}")
    return extracted


def generate_outreach_message(data: Dict) -> str:
    """
    Step 3: Generate LinkedIn outreach message using LLM

    Single LLM call with template-based prompt
    """
    print(f"  [Step 3] Generating message...")

    # Build prompt based on is_tech flag
    if data["is_tech"]:
        style_instruction = "Write the message in rap/verse format to stand out."
    else:
        style_instruction = "Write a professional, friendly message."

    prompt = f"""<task_context>
Role: You are the founder/salesperson of a B2B SaaS company offering AI-powered sales automation solutions.
Product: An AI sales rep that automates 70% of a human's work.
Customer: CEO/Founder/Heads of Sales in companies generating at least $1M in annual revenue.
</task_context>

<instructions>
Write the first LinkedIn message after a connection is accepted, which:
1. Starts with a personal greeting using their first name.
2. Includes a specific observation about the recipient's company based on their role.
3. Offers a clear value proposition with numbers (savings or growth).
4. Ends with a soft question about their interest.

{style_instruction}
</instructions>

<example>
Hi John,

I noticed that you're hiring sales reps: we offer an AI seller that automates 70% of a human's work to cut costs and help scale without increasing headcount.

Would this be of interest to you?

Bayram
</example>

<constraints>
– Length: 40–60 words
– Tone: Friendly and direct, not pushy
– Required: A specific benefit number (percentage or money)
– Never: Don't offer a demo or call in the first message
– Signature: Bayram
</constraints>

<input_variables>
Contact name: {data['first_name']}
Company: {data['company']}
What you noticed about the company: {data['description']}
</input_variables>

Output: Write a LinkedIn message using the information above."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=300,
        temperature=0.7,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    message = response.content[0].text
    return message


def chained_workflow(linkedin_url: str) -> Dict:
    """
    Main chained workflow function

    Executes steps sequentially with NO error recovery
    Returns success/failure result
    """
    print(f"\n{'='*60}")
    print(f"CHAINED WORKFLOW")
    print(f"URL: {linkedin_url}")
    print(f"{'='*60}")

    try:
        # Step 1: Fetch profile
        profile = fetch_linkedin_profile(linkedin_url)

        # Step 2: Extract data (will crash if fields missing)
        data = extract_profile_data(profile)

        # Step 3: Generate message
        message = generate_outreach_message(data)

        print(f"  [Step 4] ✅ Success!")
        print(f"\n{'-'*60}")
        print(f"GENERATED MESSAGE:\n")
        print(message)
        print(f"{'-'*60}\n")

        return {
            "success": True,
            "message": message,
            "url": linkedin_url
        }

    except Exception as e:
        print(f"  [Step X] ❌ FAILED: {str(e)}")
        print(f"{'-'*60}\n")

        return {
            "success": False,
            "error": str(e),
            "url": linkedin_url
        }


if __name__ == "__main__":
    # Test with sample URL
    from test_cases import DEMO_PAIR

    for label, url in DEMO_PAIR:
        print(f"\n{'#'*60}")
        print(f"# TEST: {label}")
        print(f"{'#'*60}")
        result = chained_workflow(url)
