"""
Test prospects for Research Agent V2 demo.

Workshop 2 focuses on the Reflection Pattern:
- V1 research (initial)
- External feedback (human review)
- V2 research (improved)

For this demo, we primarily need GOOD data to showcase
the reflection pattern - the improvement from V1 to V2.
"""

# Primary demo prospect - high-quality profile for demonstrating reflection
DEMO_PROSPECT = (
    "Bayram Annakov - Instructor",
    "https://linkedin.com/in/bayramannakov"
)

# Alternative demo prospects with good data quality
DEMO_PROSPECTS_ALT = [
    (
        "Satya Nadella - Microsoft CEO",
        "https://www.linkedin.com/in/satyanadella/"
    ),
    (
        "Demis Hassabis - Google DeepMind",
        "https://www.linkedin.com/in/demishassabis/"
    ),
]

# Prospects that might produce interesting reflection scenarios
# These have varying data quality, which can lead to richer V1->V2 improvements
REFLECTION_SCENARIOS = [
    {
        "name": "Complete Profile",
        "url": "https://www.linkedin.com/in/jenhsunhuang/",
        "description": "Full data available - focus on insight quality improvement",
        "expected_feedback": "V1 may lack specific pain points; V2 should be more actionable"
    },
    {
        "name": "Executive with Short Tenure",
        "url": "https://www.linkedin.com/in/satyanadella/",
        "description": "Well-known exec - V1 may rely on generic knowledge",
        "expected_feedback": "Human can provide current context the API missed"
    },
]

# For quick workshop testing - use this for the live demo
QUICK_TEST_URL = "https://www.linkedin.com/in/jenhsunhuang/"

# Workshop teaching notes:
#
# The Reflection Pattern Demo:
# 1. Run with DEMO_PROSPECT
# 2. During human review, provide specific feedback:
#    - Rate 3/5 (needs improvement)
#    - Feedback: "Add more specific pain points for an AI chip company CEO"
#    - Missing: "No mention of recent AI boom or NVIDIA's market position"
#    - Corrections: "none"
# 3. Watch V2 incorporate this external feedback
#
# This demonstrates the key insight:
# External feedback (human judgment) provides signals that
# the LLM couldn't generate through reasoning alone.
