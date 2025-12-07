"""
Prompts for Research Agent V2

This module exports the prompt templates used for the reflection pattern:
- SYSTEM_PROMPT: Agent's role and capabilities
- V1_RESEARCH_PROMPT: Initial research generation
- VALIDATION_PROMPT: Request external feedback
- REFLECTION_PROMPT: Generate improved research based on feedback
- RESEARCH_CRITERIA: Quality checklist for reflection
"""

from .reflection import (
    SYSTEM_PROMPT,
    V1_RESEARCH_PROMPT,
    VALIDATION_PROMPT,
    REFLECTION_PROMPT,
    RESEARCH_CRITERIA,
)

__all__ = [
    "SYSTEM_PROMPT",
    "V1_RESEARCH_PROMPT",
    "VALIDATION_PROMPT",
    "REFLECTION_PROMPT",
    "RESEARCH_CRITERIA",
]
