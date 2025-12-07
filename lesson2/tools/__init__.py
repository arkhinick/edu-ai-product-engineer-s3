"""
Tools for Research Agent V2

This module exports the MCP tools used by the research agent:
- fetch_linkedin_profile: Fetch professional background from LinkedIn
- request_human_review: Collect human feedback on research output
"""

from .linkedin import fetch_linkedin_profile, analyze_profile_quality
from .human_feedback import request_human_review

__all__ = [
    "fetch_linkedin_profile",
    "analyze_profile_quality",
    "request_human_review",
]
