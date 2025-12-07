"""
Reflection Prompts for Research Agent V2

These prompts implement the Reflection Pattern:
V1 (initial) -> External Feedback -> V2 (improved)

The key insight: External feedback breaks the prompt engineering plateau
by providing signals the LLM couldn't generate through reasoning alone.
"""

# System prompt defining the agent's role
SYSTEM_PROMPT = """You are an expert B2B sales researcher specializing in prospect research.

Your job is to research prospects and provide actionable intelligence for sales outreach.

You have access to these tools:
- fetch_linkedin_profile: Get professional background from LinkedIn URLs
- request_human_review: Request human feedback on your research quality

IMPORTANT GUIDELINES:

1. Always start by fetching the LinkedIn profile to gather factual data
2. Analyze the profile data quality - note any missing or incomplete information
3. Before finalizing, request human review to validate your research
4. Use the human feedback to improve your research in the reflection phase

Your research should be:
- Accurate: Based on verified data, not assumptions
- Actionable: Provides clear insights for sales outreach
- Specific: Includes concrete details, not generic observations
- Honest: Clearly marks any assumptions or unverified information

Context: You're supporting B2B sales for an AI sales automation product.
Target prospects: CEOs, Founders, Heads of Sales at $1M+ revenue companies."""


# Quality criteria checklist for reflection
RESEARCH_CRITERIA = """
QUALITY CRITERIA CHECKLIST:
[ ] Is the job title current and verified from the profile?
[ ] Is the company information accurate and up-to-date?
[ ] Is there relevant work history providing context?
[ ] Are there recent triggers identified? (job change, company growth, funding)
[ ] Is there a clear pain point identified for B2B outreach?
[ ] Is the information specific, not generic/templated?
[ ] Are any assumptions clearly marked as such?
"""


# Initial research prompt (Turn 1 - V1 generation)
V1_RESEARCH_PROMPT = """Research this prospect for B2B sales outreach.

LinkedIn URL: {linkedin_url}

Your task:
1. Fetch the LinkedIn profile using the fetch_linkedin_profile tool
2. Extract key information: name, title, company, professional background
3. Analyze their career trajectory and current focus
4. Identify potential pain points based on their role and company
5. Note any recent changes (job change, company growth) as outreach triggers

Provide a STRUCTURED RESEARCH REPORT with these sections:

## PROSPECT SUMMARY
Name, current title, company. 2-3 sentences about their role and background.

## KEY INSIGHTS
3-4 bullet points about what makes them relevant as a prospect:
- Their current responsibilities and focus areas
- Notable career trajectory or achievements
- Company context (size, industry, growth stage)

## PAIN POINTS
2-3 potential challenges based on their role that our product could address:
- What problems do people in this role typically face?
- How might our AI sales automation help?

## OUTREACH ANGLE
Best approach for initial contact:
- What hook would resonate with them?
- What specific value proposition to lead with?

## DATA QUALITY NOTES
Note any missing information or limitations in the research."""


# Validation prompt (Turn 2 - Request external feedback)
VALIDATION_PROMPT = """Now validate your research using external feedback.

You've completed initial research. Before finalizing, get human review to ensure quality.

Use the request_human_review tool to:
1. Present your research summary to a human reviewer
2. Collect their feedback on what could be improved
3. Learn what information might be missing
4. Get any corrections needed

Pass your complete research report as the research_summary parameter.

This external feedback will provide signals you cannot generate by reasoning alone:
- Real-world knowledge about the prospect or company
- Industry insights you might not have
- Quality assessment from human judgment
- Missing context that would strengthen the research"""


# Reflection prompt (Turn 3 - V2 generation based on feedback)
REFLECTION_PROMPT = """Review your research based on the external feedback received.

EXTERNAL FEEDBACK RECEIVED:
{feedback}

QUALITY CRITERIA TO CHECK:
{criteria}

REFLECTION PROCESS:
1. What issues were identified in the feedback?
   - Note any missing information the human mentioned
   - Note any corrections or inaccuracies flagged
   - Note any quality concerns raised

2. How should the research be improved?
   - What specific changes address the feedback?
   - What additional context can you add from your knowledge?
   - What assumptions should be clarified?

3. Apply the quality criteria checklist
   - Go through each criterion and assess
   - Identify areas where V1 fell short

Now produce an IMPROVED VERSION (V2) of the research that:
- Directly addresses all feedback points
- Fills gaps with additional context where possible
- Clearly marks any assumptions or unverified information with [ASSUMPTION]
- Provides more actionable and specific insights
- Notes what information couldn't be verified

Format the V2 research with the same structure as V1:
- PROSPECT SUMMARY
- KEY INSIGHTS
- PAIN POINTS
- OUTREACH ANGLE
- DATA QUALITY NOTES (updated based on feedback)

If the feedback indicated approval with no issues, acknowledge this and present
a refined version with any minor improvements you can make.

IMPROVED RESEARCH REPORT (V2):"""
