"""
LinkedIn Profile Tool for Research Agent V2

Evolved from W1's fetch_linkedin_profile with:
- Improved docstrings (USE WHEN, RETURNS, ERRORS)
- Profile quality analysis (external feedback from data)
- Better error messages

This demonstrates how good docstrings help Claude use tools effectively.
"""

import os
import requests
from typing import Any
from dotenv import load_dotenv

# Load .env BEFORE accessing environment variables
load_dotenv()

from claude_agent_sdk import tool

# API key for EnrichLayer
ENRICHLAYER_API_KEY = os.getenv("ENRICHLAYER_API_KEY")


def analyze_profile_quality(profile_data: dict) -> dict:
    """
    Analyze EnrichLayer response for data quality signals.

    This provides EXTERNAL FEEDBACK about the profile data quality
    that the LLM couldn't generate by reasoning alone.

    Returns:
        dict with completeness_score, missing_fields, data_quality, suggestions
    """
    quality = {
        "completeness_score": 0,
        "missing_fields": [],
        "data_quality": "unknown",
        "suggestions": []
    }

    # Check key fields
    if not profile_data.get("first_name"):
        quality["missing_fields"].append("first_name")
        quality["suggestions"].append("Name not found - verify URL is correct")

    if not profile_data.get("experiences"):
        quality["missing_fields"].append("work_experience")
        quality["suggestions"].append("No work history - may need web search for context")
    elif len(profile_data.get("experiences", [])) < 2:
        quality["suggestions"].append("Limited work history - consider supplementing with other sources")

    if not profile_data.get("headline"):
        quality["missing_fields"].append("headline")
        quality["suggestions"].append("No headline - role may be unclear")

    if not profile_data.get("education"):
        quality["missing_fields"].append("education")

    if not profile_data.get("location"):
        quality["missing_fields"].append("location")

    # Calculate completeness score
    total_fields = 5  # first_name, experiences, headline, education, location
    present = total_fields - len(quality["missing_fields"])
    quality["completeness_score"] = round(present / total_fields * 100)

    # Determine overall quality
    if quality["completeness_score"] >= 80:
        quality["data_quality"] = "high"
    elif quality["completeness_score"] >= 50:
        quality["data_quality"] = "medium"
    else:
        quality["data_quality"] = "low"
        quality["suggestions"].append("Profile data is incomplete - consider alternative research methods")

    return quality


@tool(
    "fetch_linkedin_profile",
    """Fetch professional background data from a LinkedIn profile URL.

    USE WHEN: You need to research a person's professional background,
    including their name, current title, company, work history, or education.
    This is typically the first step in prospect research.

    RETURNS ON SUCCESS:
    - first_name, last_name: Person's name
    - headline: Current professional headline
    - company: Current company name (from most recent experience)
    - title: Current job title
    - location: Geographic location
    - experiences: List of past positions with company, title, description
    - education: List of educational background
    - industry: Industry classification
    - profile_quality: Assessment of data completeness (completeness_score, data_quality, suggestions)

    RETURNS ON ERROR:
    - error message if: URL invalid, profile not found, API timeout, rate limited
    - Suggestions for how to proceed (e.g., try URL variations, use web search)

    INPUT FORMAT: Full LinkedIn URL
    Examples:
    - https://www.linkedin.com/in/username
    - https://linkedin.com/in/username
    - linkedin.com/in/username (will be normalized)

    NOTE: Some profiles may have incomplete data if privacy settings restrict access.
    Check the profile_quality field to assess data completeness.""",
    {"profile_url": str}
)
async def fetch_linkedin_profile(args: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch LinkedIn profile data via EnrichLayer API with quality analysis.

    This is an MCP tool that Claude can call autonomously when it needs
    professional background information about a person.
    """
    profile_url = args["profile_url"]

    print(f"  [Tool] Fetching profile: {profile_url}")

    try:
        response = requests.get(
            "https://enrichlayer.com/api/v2/profile",
            params={"profile_url": profile_url},
            headers={"Authorization": f"Bearer {ENRICHLAYER_API_KEY}"},
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()

            # Analyze profile quality (external feedback)
            quality = analyze_profile_quality(data)

            # Extract current company from experiences
            current_company = None
            current_title = None
            if data.get("experiences") and len(data["experiences"]) > 0:
                current_exp = data["experiences"][0]
                current_company = current_exp.get("company", "Unknown")
                current_title = current_exp.get("title", "Unknown")

            first_name = data.get("first_name", "Unknown")
            print(f"  [Tool] Success! Found: {first_name} at {current_company}")
            print(f"  [Tool] Data quality: {quality['data_quality']} ({quality['completeness_score']}%)")

            # Build comprehensive result
            result = {
                "first_name": first_name,
                "last_name": data.get("last_name", ""),
                "headline": data.get("headline", ""),
                "company": current_company,
                "title": current_title,
                "location": data.get("location", ""),
                "industry": data.get("industry", ""),
                "experiences": data.get("experiences", []),
                "education": data.get("education", []),
                "profile_quality": quality,
                "raw_profile_snippet": str(data)[:500]  # For debugging
            }

            return {
                "content": [{
                    "type": "text",
                    "text": f"Successfully fetched LinkedIn profile:\n{result}"
                }]
            }

        elif response.status_code == 404:
            error_msg = "Profile not found. The username may be incorrect or the profile may be private."
            print(f"  [Tool] Profile not found")

            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: {error_msg}\n\nSuggestions:\n- Try removing hyphens from username\n- Try common variations (firstname-lastname, firstnamelastname)\n- Use web search to find the correct profile URL"
                }],
                "is_error": True
            }

        elif response.status_code == 429:
            error_msg = "Rate limited. Too many requests to the API."
            print(f"  [Tool] Rate limited")

            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: {error_msg}\n\nSuggestion: Wait a moment and try again, or proceed with available information."
                }],
                "is_error": True
            }

        else:
            error_msg = f"API returned {response.status_code}: {response.text[:200]}"
            print(f"  [Tool] API error: {error_msg}")

            return {
                "content": [{
                    "type": "text",
                    "text": f"Error fetching profile: {error_msg}"
                }],
                "is_error": True
            }

    except requests.Timeout:
        error_msg = "Request timed out. The API may be slow or unavailable."
        print(f"  [Tool] Timeout")

        return {
            "content": [{
                "type": "text",
                "text": f"Error: {error_msg}\n\nSuggestion: Try again or proceed with web search."
            }],
            "is_error": True
        }

    except Exception as e:
        error_msg = f"Exception occurred: {str(e)}"
        print(f"  [Tool] Exception: {error_msg}")

        return {
            "content": [{
                "type": "text",
                "text": f"Error: {error_msg}"
            }],
            "is_error": True
        }
