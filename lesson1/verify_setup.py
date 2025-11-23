#!/usr/bin/env python3
"""
Setup Verification Script
Checks all prerequisites for LinkedIn Outreach Demo
"""

import sys
import os
import subprocess
from pathlib import Path


def print_header(text):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def check_python_version():
    """Verify Python version is 3.10+"""
    print("\n1. Checking Python version...")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major == 3 and version.minor >= 10:
        print(f"   ✓ Python version: {version_str} (OK)")
        return True
    else:
        print(f"   ✗ Python version: {version_str} (Need 3.10+)")
        print(f"   → Install Python 3.11: brew install python@3.11")
        return False


def check_nodejs():
    """Verify Node.js is installed"""
    print("\n2. Checking Node.js...")
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   ✓ Node.js found: {version}")
            return True
        else:
            print(f"   ✗ Node.js not working")
            return False
    except FileNotFoundError:
        print(f"   ✗ Node.js not found")
        print(f"   → Install: brew install node")
        return False
    except Exception as e:
        print(f"   ✗ Error checking Node.js: {e}")
        return False


def check_claude_cli():
    """Verify Claude CLI is installed"""
    print("\n3. Checking Claude CLI...")
    cli_paths = [
        "/usr/local/bin/claude",
        "claude",
    ]

    for cli_path in cli_paths:
        try:
            result = subprocess.run(
                [cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                env={**os.environ, "PATH": "/usr/local/bin:" + os.environ.get("PATH", "")}
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"   ✓ Claude CLI found: {version}")
                print(f"   Location: {cli_path}")
                return True
        except FileNotFoundError:
            continue
        except Exception as e:
            continue

    print(f"   ✗ Claude CLI not found")
    print(f"   → Install: curl -fsSL https://claude.ai/install.sh | bash")
    return False


def check_venv():
    """Check if running in virtual environment"""
    print("\n4. Checking virtual environment...")
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print(f"   ✓ Virtual environment: Active")
        print(f"   Location: {sys.prefix}")
        return True
    else:
        print(f"   ⚠ Virtual environment: Not active")
        print(f"   → Activate: source venv/bin/activate")
        return False


def check_dependencies():
    """Verify all required packages are installed"""
    print("\n5. Checking dependencies...")
    required = {
        "claude-agent-sdk": "0.1.9",
        "anthropic": "0.40.0",
        "requests": "2.31.0",
        "python-dotenv": "1.0.0",
    }

    all_installed = True
    for package, min_version in required.items():
        try:
            if package == "claude-agent-sdk":
                import claude_agent_sdk
                # Version check would go here if available
                print(f"   ✓ {package}: Installed")
            elif package == "anthropic":
                import anthropic
                print(f"   ✓ {package}: Installed")
            elif package == "requests":
                import requests
                print(f"   ✓ {package}: Installed")
            elif package == "python-dotenv":
                import dotenv
                print(f"   ✓ {package}: Installed")
        except ImportError:
            print(f"   ✗ {package}: Not installed")
            all_installed = False

    if not all_installed:
        print(f"\n   → Install: pip install -r requirements.txt")

    return all_installed


def check_env_file():
    """Check if .env file exists and has required keys"""
    print("\n6. Checking environment configuration...")
    env_path = Path(".env")

    if not env_path.exists():
        print(f"   ✗ .env file not found")
        print(f"   → Create: cp .env.example .env")
        return False

    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv()

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        enrichlayer_key = os.getenv("ENRICHLAYER_API_KEY")

        if anthropic_key and anthropic_key.startswith("sk-ant-"):
            masked = anthropic_key[:10] + "*" * 10
            print(f"   ✓ ANTHROPIC_API_KEY: Set ({masked})")
        else:
            print(f"   ✗ ANTHROPIC_API_KEY: Not set or invalid")
            return False

        if enrichlayer_key:
            masked = enrichlayer_key[:10] + "*" * 10 if len(enrichlayer_key) > 10 else enrichlayer_key[:3] + "*" * 5
            print(f"   ✓ ENRICHLAYER_API_KEY: Set ({masked})")
        else:
            print(f"   ✗ ENRICHLAYER_API_KEY: Not set")
            return False

        return True

    except Exception as e:
        print(f"   ✗ Error loading .env: {e}")
        return False


def check_api_connectivity():
    """Test API connectivity"""
    print("\n7. Testing API connectivity...")

    # Test Anthropic API
    try:
        from dotenv import load_dotenv
        from anthropic import Anthropic

        load_dotenv()
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )

        if response.content:
            print(f"   ✓ Anthropic API: Connected")
            return True
        else:
            print(f"   ✗ Anthropic API: Unexpected response")
            return False

    except Exception as e:
        print(f"   ✗ Anthropic API: Failed ({str(e)[:50]}...)")
        return False


def check_file_structure():
    """Verify all required files exist"""
    print("\n8. Checking file structure...")
    required_files = [
        "chained_outreach.py",
        "agent_outreach.py",
        "test_cases.py",
        "requirements.txt",
        ".env.example",
    ]

    all_exist = True
    for file in required_files:
        if Path(file).exists():
            print(f"   ✓ {file}: Found")
        else:
            print(f"   ✗ {file}: Missing")
            all_exist = False

    return all_exist


def print_summary(results):
    """Print summary of all checks"""
    print_header("SUMMARY")

    passed = sum(results.values())
    total = len(results)

    for check, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"{symbol} {check}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All checks passed! Ready to run demos.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix issues above.")
        print("\nSee SETUP_GUIDE.md and TROUBLESHOOTING.md for help.")
        return 1


def main():
    """Run all verification checks"""
    print_header("LinkedIn Outreach Demo - Setup Verification")

    results = {
        "Python 3.10+": check_python_version(),
        "Node.js": check_nodejs(),
        "Claude CLI": check_claude_cli(),
        "Virtual Environment": check_venv(),
        "Dependencies": check_dependencies(),
        "Environment Config": check_env_file(),
        "File Structure": check_file_structure(),
    }

    # Only test API if previous checks passed
    if results["Dependencies"] and results["Environment Config"]:
        results["API Connectivity"] = check_api_connectivity()
    else:
        print("\n7. Skipping API test (fix dependencies first)")

    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
