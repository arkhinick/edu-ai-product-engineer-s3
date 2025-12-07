"""
Laminar observability for Research Agent V2.

This module integrates Laminar for full agent observability.
Laminar uses a Rust proxy to intercept ALL Claude Agent SDK
communications, providing complete visibility into:

- Full prompts (including system prompts)
- Complete conversation history
- Tool calls with inputs AND outputs
- Real token counts (not partial SDK metrics)
- Accurate cost tracking

Key Concept: The Claude Agent SDK abstracts away API calls.
Laminar's proxy reveals what's really happening.

Debug Mode:
    Set DEBUG_LLM=true in .env to see prompts/responses in console.
"""

import os
import time
import json
from typing import Optional, Any

# Global state
_laminar_initialized = False
_debug_mode = False


def init_observability() -> bool:
    """
    Initialize Laminar observability and debug mode.

    Requires environment variable:
    - LAMINAR_API_KEY: Your Laminar project API key

    Optional:
    - DEBUG_LLM: Set to "true" for console output

    Returns:
        bool: True if Laminar is configured and initialized, False otherwise.
    """
    global _laminar_initialized, _debug_mode

    # Check for debug mode
    _debug_mode = os.getenv("DEBUG_LLM", "").lower() in ("true", "1", "yes")
    if _debug_mode:
        print("\n  [Debug] DEBUG_LLM enabled - full prompts/responses will be shown")

    api_key = os.getenv("LAMINAR_API_KEY")

    if not api_key:
        print("\n  [Observability] Laminar not configured - running without tracing")
        print("  To enable: Set LAMINAR_API_KEY in .env")
        print("  Get your key at: https://www.laminar.run\n")
        return False

    try:
        from lmnr import Laminar

        Laminar.initialize(project_api_key=api_key)
        _laminar_initialized = True

        print("\n  [Observability] Laminar enabled!")
        print("  View traces at: https://www.laminar.run\n")
        return True

    except ImportError:
        print("\n  [Observability] Laminar not installed - running without tracing")
        print("  To enable: pip install 'lmnr[claude-agent-sdk]'\n")
        return False

    except Exception as e:
        print(f"\n  [Observability] Failed to initialize Laminar: {e}")
        print("  Running without tracing\n")
        return False


def flush_observations():
    """Flush is automatic with Laminar, but kept for API compatibility."""
    if _laminar_initialized:
        print("  [Observability] Traces sent to Laminar")


def observe(name: str = None, **kwargs):
    """
    Decorator to trace function execution in Laminar.

    When Laminar is available, this wraps functions for automatic tracing.
    When not available, this is a passthrough decorator.
    """
    try:
        from lmnr import observe as laminar_observe
        return laminar_observe(name=name, **kwargs)
    except ImportError:
        def passthrough_decorator(func):
            return func
        return passthrough_decorator


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return _debug_mode


def debug_print(title: str, content: str, max_lines: int = None):
    """
    Print debug information in a formatted box.

    Args:
        title: Title for the debug box
        content: Content to display
        max_lines: Optional limit on number of lines to show
    """
    if not _debug_mode:
        return

    border = "═" * 70
    print(f"\n╔{border}╗")
    print(f"║ 🔍 DEBUG: {title:<57} ║")
    print(f"╠{border}╣")

    lines = content.split('\n')
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... ({len(lines) - max_lines} more lines)"]

    for line in lines:
        # Truncate long lines
        if len(line) > 68:
            line = line[:65] + "..."
        print(f"║ {line:<68} ║")

    print(f"╚{border}╝")


class LLMTracker:
    """
    Track LLM generations for observability.

    This class provides manual tracking for DEBUG_LLM mode.
    When Laminar is enabled, it captures everything automatically
    via the Rust proxy, so this is mainly for console output.

    Usage:
        tracker = create_tracker("research-session")

        # For each LLM turn:
        tracker.start_generation("V1 Research", prompt)
        ... collect response ...
        tracker.end_generation(response_text, token_info)

        # When done:
        tracker.end_trace()
    """

    def __init__(self, trace_name: str = "agent-session"):
        """Initialize a new tracker."""
        self.trace_name = trace_name
        self.generations = []
        self.start_time = time.time()
        self.current_gen_name = None
        self.current_gen_start = None

    def start_generation(
        self,
        name: str,
        prompt: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Start tracking an LLM generation.

        Args:
            name: Name for this generation (e.g., "V1 Research")
            prompt: The prompt being sent to the LLM
            model: The model being used
        """
        self.current_gen_name = name
        self.current_gen_start = time.time()

        # Debug output: Show the prompt being sent
        debug_print(f"PROMPT → {name}", prompt)

    def log_tool_call(self, tool_name: str, tool_input: dict, tool_output: str = None):
        """
        Log a tool call.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters to the tool
            tool_output: Output from the tool (if available)
        """
        tool_debug = f"Tool: {tool_name}\nInput: {json.dumps(tool_input, indent=2)}"
        if tool_output:
            tool_debug += f"\nOutput: {tool_output[:500]}..."
        debug_print(f"TOOL CALL → {tool_name}", tool_debug)

    def end_generation(
        self,
        output: str,
        input_tokens: int = None,
        output_tokens: int = None,
        cost_usd: float = None
    ):
        """
        End the current generation with the response.

        Args:
            output: The LLM's response text
            input_tokens: Number of input tokens (if available)
            output_tokens: Number of output tokens (if available)
            cost_usd: Cost in USD (if available)
        """
        duration_ms = (time.time() - self.current_gen_start) * 1000 if self.current_gen_start else 0

        # Debug output: Show the LLM response
        gen_name = self.current_gen_name or 'Unknown'
        metrics = []
        if input_tokens:
            metrics.append(f"Input: {input_tokens} tokens")
        if output_tokens:
            metrics.append(f"Output: {output_tokens} tokens")
        if cost_usd:
            metrics.append(f"Cost: ${cost_usd:.6f}")
        metrics.append(f"Duration: {duration_ms:.0f}ms")

        response_debug = f"[{' | '.join(metrics)}]\n\n{output}"
        debug_print(f"RESPONSE ← {gen_name}", response_debug, max_lines=30)

        # Store generation info
        self.generations.append({
            "name": gen_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
            "duration_ms": duration_ms
        })

    def end_trace(self):
        """End the trace and return summary statistics."""
        total_duration = time.time() - self.start_time
        total_input_tokens = sum(g.get("input_tokens") or 0 for g in self.generations)
        total_output_tokens = sum(g.get("output_tokens") or 0 for g in self.generations)
        total_cost = sum(g.get("cost_usd") or 0 for g in self.generations)

        return {
            "generations": len(self.generations),
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "cost_usd": total_cost,
            "duration_s": total_duration
        }


def create_tracker(name: str = "agent-session") -> LLMTracker:
    """
    Create a new LLM tracker for observability.

    Args:
        name: Name for the trace

    Returns:
        LLMTracker instance
    """
    return LLMTracker(name)


def is_observability_enabled() -> bool:
    """Check if observability is currently enabled."""
    return _laminar_initialized


def get_trace_url() -> str | None:
    """Get the URL to view traces."""
    if not _laminar_initialized:
        return None
    return "https://www.laminar.run"
