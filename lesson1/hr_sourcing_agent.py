"""
HR SOURCING AGENT: Autonomous Candidate Finder

This is an Autonomous AI Agent (not a rigid workflow) that uses the ReAct
pattern (Reason -> Act -> Observe) to find a candidate's contact email
given their GitHub username.

Key difference from workflows:
- Agent decides WHICH tools to use and WHEN
- Self-correcting: can retry with different strategies
- Goal-oriented reasoning, not fixed steps

Tools:
1. read_github_profile - Fetches public GitHub profile data
2. search_web - Mock web search for contact information
3. verify_email_format - Validates email format with regex
"""

import os
import re
import requests
from typing import Annotated
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


# ============================================================================
# TOOL 1: Read GitHub Profile
# ============================================================================

@tool
def read_github_profile(username: str) -> str:
    """
    Fetch a GitHub user's public profile data.
    
    Args:
        username: The GitHub username to look up (e.g., 'torvalds')
        
    Returns:
        JSON string with profile data including bio, blog, company, email fields.
        Returns error message if user not found.
    """
    print(f"  [Tool] Fetching GitHub profile for: {username}")
    
    try:
        response = requests.get(
            f"https://api.github.com/users/{username}",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant fields
            profile_info = {
                "login": data.get("login"),
                "name": data.get("name"),
                "email": data.get("email"),  # Often null for privacy
                "bio": data.get("bio"),
                "blog": data.get("blog"),
                "company": data.get("company"),
                "location": data.get("location"),
                "twitter_username": data.get("twitter_username"),
                "public_repos": data.get("public_repos"),
                "followers": data.get("followers")
            }
            
            print(f"    → Found profile: {profile_info.get('name') or username}")
            print(f"    → Public email: {profile_info.get('email') or 'Not public'}")
            print(f"    → Blog: {profile_info.get('blog') or 'None'}")
            
            return str(profile_info)
            
        elif response.status_code == 404:
            return f"Error: GitHub user '{username}' not found."
        else:
            return f"Error: GitHub API returned status {response.status_code}"
            
    except requests.RequestException as e:
        return f"Error fetching GitHub profile: {str(e)}"


# ============================================================================
# TOOL 2: Web Search (Mock Implementation)
# ============================================================================

@tool
def search_web(query: str) -> str:
    """
    Search the web for contact information related to a person or website.
    
    Args:
        query: Search query string (e.g., "torvalds email contact" or "dev-guru.io contact")
        
    Returns:
        Search results with potential contact information found in snippets.
    """
    print(f"  [Tool] Web search for: {query}")
    
    query_lower = query.lower()
    
    # Mock responses based on query patterns
    if "gmail" in query_lower:
        result = "Found a comment on Reddit: 'contact me at dev_guru_99 at gmail dot com'"
        print(f"    → Found Gmail reference")
        return result
        
    elif "blog" in query_lower or ".io" in query_lower or ".com" in query_lower:
        # Check for specific blog domains
        if "kernel.org" in query_lower or "linux" in query_lower:
            result = "Linux kernel mailing list archives show: torvalds@linux-foundation.org is the primary contact."
            print(f"    → Found Linux Foundation contact")
            return result
        else:
            result = "Blog 'dev-guru.io' found. About page mentions: 'Reach out to me via hello@dev-guru.io'"
            print(f"    → Found blog contact")
            return result
            
    elif "twitter" in query_lower or "x.com" in query_lower:
        result = "Twitter/X profile found but DMs are closed. Bio mentions: 'For work inquiries: work@example.com'"
        print(f"    → Found Twitter reference")
        return result
        
    elif "torvalds" in query_lower:
        # Special case for Linus Torvalds - well-known public figure
        result = "Multiple sources confirm: Linus Torvalds can be reached via torvalds@linux-foundation.org for Linux kernel matters."
        print(f"    → Found Torvalds contact info")
        return result
        
    elif "email" in query_lower or "contact" in query_lower:
        result = "Found potential contact page. Common pattern: firstname.lastname@company.com"
        print(f"    → Found generic contact pattern")
        return result
        
    else:
        result = "No direct contacts found in search snippets."
        print(f"    → No results")
        return result


# ============================================================================
# TOOL 3: Email Format Validator
# ============================================================================

@tool
def verify_email_format(email: str) -> str:
    """
    Verify if an email address has a valid format using regex.
    
    Args:
        email: The email address to validate (e.g., 'user@example.com')
        
    Returns:
        'VALID' if the email format is correct, 'INVALID' with reason otherwise.
    """
    print(f"  [Tool] Verifying email format: {email}")
    
    # Standard email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Clean up common text patterns
    email_cleaned = email.strip().lower()
    
    # Handle "at" and "dot" written out
    if " at " in email_cleaned or " dot " in email_cleaned:
        email_cleaned = email_cleaned.replace(" at ", "@").replace(" dot ", ".")
        print(f"    → Cleaned email: {email_cleaned}")
    
    if re.match(email_pattern, email_cleaned):
        print(f"    → ✅ Valid format")
        return f"VALID: '{email_cleaned}' is a properly formatted email address."
    else:
        print(f"    → ❌ Invalid format")
        return f"INVALID: '{email}' does not match standard email format (expected: user@domain.tld)"


# ============================================================================
# AGENT SETUP
# ============================================================================

# System prompt defining the agent's mission
SOURCING_AGENT_PROMPT = """You are a Sourcing Agent specialized in finding candidate contact information.

Your mission: Given a GitHub username, find the candidate's email address.

Strategy (follow this order):
1. FIRST: Check the GitHub profile using read_github_profile. If the email is public, verify it and you're done.
2. If email is null/empty: Look for a 'blog' or 'company' field in the profile.
3. Use search_web to find contacts associated with their blog, company, or username.
4. When you find a potential email, ALWAYS use verify_email_format to confirm it's valid.
5. If you cannot find a valid email after 3 search attempts, report that you couldn't find it.

Important rules:
- Always verify emails before reporting them as final
- If you find an email written as "user at domain dot com", convert it to user@domain.com
- Report your reasoning at each step
- Be persistent but give up after 3 failed search attempts

Output format for final answer:
✅ FOUND: [email] - [source where you found it]
or
❌ NOT FOUND: [summary of what you tried]
"""


def create_sourcing_agent():
    """
    Create the sourcing agent with tools and memory.
    
    Returns:
        Compiled LangGraph agent with ReAct pattern
    """
    # Initialize the LLM
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0
    )
    
    # Define the tools available to the agent
    tools = [
        read_github_profile,
        search_web,
        verify_email_format
    ]
    
    # Create memory checkpointer for conversation persistence
    memory = MemorySaver()
    
    # Create the ReAct agent using LangGraph's prebuilt function
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        prompt=SOURCING_AGENT_PROMPT
    )
    
    return agent, memory


# ============================================================================
# AGENT EXECUTION
# ============================================================================

def run_sourcing_agent(github_username: str, thread_id: str = "default"):
    """
    Run the sourcing agent to find a candidate's email.
    
    Args:
        github_username: The GitHub username to investigate
        thread_id: Unique ID for conversation persistence
        
    Returns:
        Final agent response
    """
    print(f"\n{'='*60}")
    print(f"HR SOURCING AGENT")
    print(f"Target: GitHub user '{github_username}'")
    print(f"{'='*60}")
    
    # Create the agent
    agent, memory = create_sourcing_agent()
    
    # Configuration for this conversation thread
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initial message to the agent
    initial_message = HumanMessage(
        content=f"Find the email for GitHub user '{github_username}'"
    )
    
    print(f"\n📤 Task: Find email for '{github_username}'")
    print(f"{'-'*60}")
    
    # Stream the agent's execution
    final_response = None
    step_count = 0
    
    for event in agent.stream(
        {"messages": [initial_message]},
        config=config,
        stream_mode="values"
    ):
        # Get the latest message
        messages = event.get("messages", [])
        if messages:
            latest = messages[-1]
            
            # Display agent reasoning (AI messages)
            if hasattr(latest, 'content') and latest.content:
                if hasattr(latest, 'tool_calls') and latest.tool_calls:
                    # Agent is about to use tools
                    step_count += 1
                    print(f"\n🤔 Step {step_count}: Agent reasoning...")
                    if isinstance(latest.content, str) and latest.content.strip():
                        print(f"   {latest.content[:200]}...")
                elif not hasattr(latest, 'tool_calls'):
                    # Final response or intermediate reasoning
                    if isinstance(latest.content, str):
                        final_response = latest.content
    
    # Print final result
    print(f"\n{'-'*60}")
    print(f"FINAL RESULT:")
    print(f"{'-'*60}")
    if final_response:
        print(final_response)
    print(f"{'-'*60}\n")
    
    return final_response


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # =========================================================================
    # TEST CASE 1: Famous developer (Linus Torvalds)
    # =========================================================================
    print("\n" + "#"*60)
    print("# TEST 1: Find email for 'torvalds' (Linus Torvalds)")
    print("#"*60)
    result1 = run_sourcing_agent("torvalds", thread_id="test-torvalds")
    
    # =========================================================================
    # TEST CASE 2: Another GitHub user (octocat - GitHub's mascot account)
    # =========================================================================
    print("\n" + "#"*60)
    print("# TEST 2: Find email for 'octocat' (GitHub mascot)")
    print("#"*60)
    result2 = run_sourcing_agent("octocat", thread_id="test-octocat")
