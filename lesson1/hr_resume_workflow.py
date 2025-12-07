"""
HR RESUME SCORING WORKFLOW: LangGraph Implementation

This is a rigid AI Workflow (not an autonomous agent) that processes
resumes through a deterministic pipeline using LangGraph.

Workflow:
1. Parser Node (LLM): Extracts structured data from raw resume text
2. Hard Filter Node (Python): Disqualifies based on experience & skills
3. Scorer Node (LLM): Rates qualified candidates 1-10

Key difference from agents:
- Fixed, deterministic flow
- Conditional branching based on rules (not LLM decisions)
- Predictable execution path
"""

import os
import json
from typing import TypedDict, Optional, List
from dotenv import load_dotenv
from anthropic import Anthropic

from langgraph.graph import StateGraph, END

load_dotenv()

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ============================================================================
# STATE DEFINITION
# ============================================================================

class ResumeState(TypedDict):
    """
    State for the HR Resume Scoring workflow.
    
    Attributes:
        input_text: Raw resume text to process
        structured_data: Parsed JSON with name, years_experience, tech_stack
        is_qualified: Whether candidate passed hard filters
        final_score: Score 1-10 (or "N/A" if disqualified)
        rejection_reason: Reason for disqualification (if any)
    """
    input_text: str
    structured_data: Optional[dict]
    is_qualified: Optional[bool]
    final_score: Optional[str]
    rejection_reason: Optional[str]


# ============================================================================
# NODE 1: PARSER (LLM)
# ============================================================================

def parser_node(state: ResumeState) -> dict:
    """
    Node 1: Parse raw resume text into structured JSON.
    
    Uses LLM to extract:
    - name (str)
    - years_experience (int)
    - tech_stack (list of strings)
    """
    print(f"  [Node 1] Parsing resume...")
    
    prompt = """<task>
Extract the following information from this resume and return ONLY valid JSON:
- name: The candidate's full name (string)
- years_experience: Total years of professional experience (integer)
- tech_stack: List of technologies/programming languages mentioned (array of strings)
</task>

<output_format>
Return ONLY a JSON object in this exact format, no other text:
{"name": "string", "years_experience": integer, "tech_stack": ["string", "string"]}
</output_format>

<resume>
""" + state["input_text"] + """
</resume>"""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        temperature=0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    response_text = response.content[0].text.strip()
    
    # Parse JSON from response
    try:
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        structured_data = json.loads(response_text.strip())
        print(f"    → Name: {structured_data.get('name')}")
        print(f"    → Experience: {structured_data.get('years_experience')} years")
        print(f"    → Tech Stack: {structured_data.get('tech_stack')}")
        
    except json.JSONDecodeError as e:
        print(f"    → ⚠️ JSON parsing error: {e}")
        structured_data = {
            "name": "Unknown",
            "years_experience": 0,
            "tech_stack": []
        }
    
    return {"structured_data": structured_data}


# ============================================================================
# NODE 2: HARD FILTER (Deterministic Python - NO LLM)
# ============================================================================

def hard_filter_node(state: ResumeState) -> dict:
    """
    Node 2: Apply deterministic hard filters.
    
    Disqualification criteria:
    - years_experience < 2
    - "Python" not in tech_stack
    
    NO LLM involved - pure Python logic.
    """
    print(f"  [Node 2] Applying hard filters...")
    
    data = state["structured_data"]
    years_exp = data.get("years_experience", 0)
    tech_stack = [tech.lower() for tech in data.get("tech_stack", [])]
    
    # Check experience requirement
    if years_exp < 2:
        reason = f"Insufficient experience: {years_exp} years (minimum: 2)"
        print(f"    → ❌ Disqualified: {reason}")
        return {
            "is_qualified": False,
            "rejection_reason": reason,
            "final_score": "N/A"
        }
    
    # Check Python requirement
    if "python" not in tech_stack:
        reason = f"Missing required skill: Python not found in tech stack"
        print(f"    → ❌ Disqualified: {reason}")
        return {
            "is_qualified": False,
            "rejection_reason": reason,
            "final_score": "N/A"
        }
    
    print(f"    → ✅ Passed all filters")
    return {
        "is_qualified": True,
        "rejection_reason": None
    }


# ============================================================================
# NODE 3: SCORER (LLM)
# ============================================================================

def scorer_node(state: ResumeState) -> dict:
    """
    Node 3: Score qualified candidates using LLM.
    
    Only runs if candidate passed hard filters.
    Returns score 1-10 based on overall resume quality.
    """
    print(f"  [Node 3] Scoring candidate...")
    
    data = state["structured_data"]
    
    prompt = f"""<task>
Rate this candidate on a scale of 1-10 based on their resume.
Consider: experience depth, tech stack breadth, and overall profile strength.
</task>

<candidate_info>
Name: {data.get('name')}
Years of Experience: {data.get('years_experience')}
Tech Stack: {', '.join(data.get('tech_stack', []))}
</candidate_info>

<original_resume>
{state['input_text']}
</original_resume>

<output_format>
Return ONLY a single integer from 1 to 10. No explanation, just the number.
</output_format>"""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=10,
        temperature=0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    score_text = response.content[0].text.strip()
    
    # Extract numeric score
    try:
        score = int(score_text)
        score = max(1, min(10, score))  # Clamp to 1-10
    except ValueError:
        # Try to extract first number from response
        import re
        numbers = re.findall(r'\d+', score_text)
        score = int(numbers[0]) if numbers else 5
        score = max(1, min(10, score))
    
    print(f"    → Score: {score}/10")
    
    return {"final_score": str(score)}


# ============================================================================
# CONDITIONAL EDGE: Route based on filter result
# ============================================================================

def should_score(state: ResumeState) -> str:
    """
    Conditional edge function.
    
    Routes to 'scorer' if qualified, otherwise to 'end'.
    """
    if state.get("is_qualified"):
        return "scorer"
    else:
        return "end"


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

def build_hr_workflow():
    """
    Build the LangGraph workflow for HR resume scoring.
    
    Flow:
    parser -> hard_filter -> (conditional) -> scorer OR end
    """
    # Initialize the graph with our state type
    workflow = StateGraph(ResumeState)
    
    # Add nodes
    workflow.add_node("parser", parser_node)
    workflow.add_node("hard_filter", hard_filter_node)
    workflow.add_node("scorer", scorer_node)
    
    # Define edges
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "hard_filter")
    
    # Conditional edge: route based on qualification
    workflow.add_conditional_edges(
        "hard_filter",
        should_score,
        {
            "scorer": "scorer",
            "end": END
        }
    )
    
    # Scorer goes to end
    workflow.add_edge("scorer", END)
    
    # Compile the graph
    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_workflow(resume_text: str) -> dict:
    """
    Run the HR resume scoring workflow.
    
    Args:
        resume_text: Raw resume text to process
        
    Returns:
        Final state with score and decision
    """
    print(f"\n{'='*60}")
    print(f"HR RESUME SCORING WORKFLOW")
    print(f"{'='*60}")
    
    # Build and run the graph
    graph = build_hr_workflow()
    
    initial_state = {
        "input_text": resume_text,
        "structured_data": None,
        "is_qualified": None,
        "final_score": None,
        "rejection_reason": None
    }
    
    # Execute the workflow
    final_state = graph.invoke(initial_state)
    
    # Print results
    print(f"\n{'-'*60}")
    print(f"FINAL RESULT:")
    print(f"{'-'*60}")
    print(f"  Candidate: {final_state.get('structured_data', {}).get('name', 'Unknown')}")
    print(f"  Qualified: {final_state.get('is_qualified')}")
    
    if final_state.get("is_qualified"):
        print(f"  Score: {final_state.get('final_score')}/10")
    else:
        print(f"  Rejection Reason: {final_state.get('rejection_reason')}")
    
    print(f"{'-'*60}\n")
    
    return final_state


if __name__ == "__main__":
    # =========================================================================
    # TEST CASE 1: Qualified Python Developer (should pass and get scored)
    # =========================================================================
    qualified_resume = """
    JOHN SMITH
    Senior Software Engineer
    
    SUMMARY
    Experienced software engineer with 5 years of professional experience
    building scalable web applications and data pipelines.
    
    SKILLS
    - Programming: Python, JavaScript, TypeScript, SQL
    - Frameworks: Django, FastAPI, React, Node.js
    - Cloud: AWS (Lambda, S3, EC2), Docker, Kubernetes
    - Data: PostgreSQL, Redis, Elasticsearch
    
    EXPERIENCE
    Senior Software Engineer | TechCorp Inc. | 2021 - Present
    - Led development of microservices architecture serving 1M+ users
    - Implemented ML pipeline for recommendation engine using Python
    - Reduced API latency by 40% through optimization
    
    Software Engineer | StartupXYZ | 2019 - 2021
    - Built RESTful APIs using Python/Django
    - Developed real-time data processing with Apache Kafka
    
    EDUCATION
    B.S. Computer Science | State University | 2019
    """
    
    print("\n" + "#"*60)
    print("# TEST 1: Qualified Python Developer")
    print("#"*60)
    result1 = run_workflow(qualified_resume)
    
    # =========================================================================
    # TEST CASE 2: Junior Developer (should be disqualified - < 2 years exp)
    # =========================================================================
    junior_resume = """
    JANE DOE
    Junior Developer
    
    SUMMARY
    Recent graduate eager to start career in software development.
    1 year of internship experience.
    
    SKILLS
    - Python, JavaScript, HTML/CSS
    - Django, React
    - Git, Linux
    
    EXPERIENCE
    Software Development Intern | TechStartup | 2023 - 2024
    - Assisted in building web applications
    - Wrote unit tests in Python
    
    EDUCATION
    B.S. Computer Science | University | 2024
    """
    
    print("\n" + "#"*60)
    print("# TEST 2: Junior Developer (< 2 years)")
    print("#"*60)
    result2 = run_workflow(junior_resume)
    
    # =========================================================================
    # TEST CASE 3: Non-Python Developer (should be disqualified - no Python)
    # =========================================================================
    java_resume = """
    BOB WILSON
    Java Developer
    
    SUMMARY
    5 years of experience in enterprise Java development.
    
    SKILLS
    - Java, Kotlin, Scala
    - Spring Boot, Hibernate
    - Oracle, MySQL
    - AWS, Jenkins
    
    EXPERIENCE
    Senior Java Developer | Enterprise Corp | 2019 - Present
    - Developed microservices using Spring Boot
    - Led team of 4 developers
    
    EDUCATION
    M.S. Software Engineering | Tech Institute | 2019
    """
    
    print("\n" + "#"*60)
    print("# TEST 3: Java Developer (No Python)")
    print("#"*60)
    result3 = run_workflow(java_resume)
