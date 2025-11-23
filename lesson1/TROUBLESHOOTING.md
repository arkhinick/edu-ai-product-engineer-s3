# Troubleshooting Guide

Common issues and solutions for the LinkedIn Outreach Demo.

---

## Quick Diagnosis

Run this command to identify issues:
```bash
python verify_setup.py
```

This checks:
- ✓ Python version
- ✓ Node.js installation
- ✓ Claude CLI
- ✓ Dependencies
- ✓ API keys
- ✓ Network connectivity

---

## Common Issues

### 1. Python Version Errors

#### Symptom
```
ERROR: Could not find a version that satisfies the requirement claude-agent-sdk>=0.1.9
```

#### Cause
Claude Agent SDK requires Python 3.10+, you're using older version

#### Solution
```bash
# Check current version
python3 --version

# Install Python 3.11
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11 python3.11-venv

# Recreate venv with correct version
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 2. Node.js Not Found

#### Symptom
```
env: node: No such file or directory
Fatal error in message reader: Command failed with exit code 127
```

#### Cause
Claude CLI requires Node.js but it's not installed or not in PATH

#### Solution A: Install Node.js
```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm

# Verify
node --version  # Should show v16.x or higher
```

#### Solution B: Fix PATH
```bash
# Find where node is installed
which node

# If found but not in PATH, add to ~/.zshrc or ~/.bashrc
export PATH="/usr/local/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bashrc

# Verify
env | grep PATH
```

#### Solution C: Run with explicit PATH
```bash
# One-time fix for current session
env PATH="/usr/local/bin:$PATH" python agent_outreach.py
```

---

### 3. Claude CLI Issues

#### Symptom A: CLI not found
```
/usr/local/bin/claude: No such file or directory
```

**Solution:**
```bash
# Install Claude CLI
curl -fsSL https://claude.ai/install.sh | bash

# Verify installation
/usr/local/bin/claude --version
```

#### Symptom B: CLI timeout
```
Control request timeout: initialize
```

**Solutions:**
1. Check Node.js is accessible:
   ```bash
   which node
   # Should output: /usr/local/bin/node or similar
   ```

2. Test Claude CLI directly:
   ```bash
   /usr/local/bin/claude --version
   # Should output version number
   ```

3. Run agent with PATH fix:
   ```bash
   env PATH="/usr/local/bin:$PATH" python agent_outreach.py
   ```

---

### 4. API Key Problems

#### Symptom A: Key not found
```
TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'
```

**Cause:** `.env` file missing or not loaded

**Solution:**
```bash
# Check .env exists
ls -la .env

# If not, create it
cp .env.example .env
nano .env  # Add your API keys

# Verify keys are loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('ANTHROPIC_API_KEY:', os.getenv('ANTHROPIC_API_KEY')[:10] if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET')"
```

#### Symptom B: Invalid API key
```
Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error'}}
```

**Solutions:**
1. Verify key format:
   - Anthropic: Starts with `sk-ant-`
   - EnrichLayer: Check your dashboard

2. Check for extra spaces/newlines:
   ```bash
   # Keys should have no spaces
   ANTHROPIC_API_KEY=sk-ant-your-key-here  # ✓ Correct
   ANTHROPIC_API_KEY = sk-ant-your-key-here  # ✗ Wrong (spaces)
   ```

3. Regenerate keys:
   - Anthropic: https://console.anthropic.com/settings/keys
   - EnrichLayer: https://enrichlayer.com/dashboard/api-key/

#### Symptom C: Rate limit exceeded
```
Error code: 429 - {'type': 'error', 'error': {'type': 'rate_limit_error'}}
```

**Solutions:**
1. For Anthropic: Check credits at https://console.anthropic.com/
2. For EnrichLayer: Free tier has ~100 requests/day
3. Wait a few minutes and retry
4. Use cached demo data (see below)

---

### 5. Import/Module Errors

#### Symptom
```
ModuleNotFoundError: No module named 'claude_agent_sdk'
```

**Cause:** Virtual environment not activated or dependencies not installed

**Solution:**
```bash
# Step 1: Activate venv
source venv/bin/activate

# Verify activation (should show venv in path)
which python

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Verify installation
pip list | grep claude-agent-sdk

# Step 4: Test import
python -c "import claude_agent_sdk; print('✓ Import successful')"
```

---

### 6. EnrichLayer API Errors

#### Symptom A: Profile not found
```
Error 404 - Profile does not exist or has been deleted
```

**Causes:**
1. LinkedIn URL is malformed
2. Profile is private/deleted
3. Username has changed

**Solutions:**
1. Verify URL format:
   ```
   ✓ https://www.linkedin.com/in/jenhsunhuang/
   ✗ linkedin.com/in/jenhsunhuang (missing https://www.)
   ✗ www.linkedin.com/in/jenhsunhuang (missing https://)
   ```

2. Test in browser first - does the LinkedIn profile load?

3. For demo: Use known working URLs from `test_cases.py`

#### Symptom B: Service unavailable
```
Error 503 - Retrieval failed, please retry
```

**Cause:** EnrichLayer API is temporarily down or rate-limited

**Solutions:**
1. Wait 30 seconds and retry
2. Check EnrichLayer status: https://status.enrichlayer.com/
3. Use mock data for demo:
   ```python
   # In chained_outreach.py, temporarily mock the response
   def fetch_linkedin_profile(url: str) -> dict:
       return {
           "first_name": "Jensen",
           "experiences": [{"company": "NVIDIA", "description": "CEO"}]
       }
   ```

---

### 7. Agent Behavior Issues

#### Symptom A: Agent doesn't self-correct
```
# Agent tries once, then gives up
```

**Cause:** System prompt not loaded correctly or max_turns too low

**Solution:**
```python
# In agent_outreach.py, verify:
options = ClaudeAgentOptions(
    max_turns=10,  # Should be at least 5
    system_prompt="""..."""  # Should include self-correction strategy
)
```

#### Symptom B: Agent makes too many attempts
```
# Agent tries 10+ times, costs spike
```

**Cause:** max_turns set too high

**Solution:**
```python
options = ClaudeAgentOptions(
    max_turns=5,  # Reduce to 3-5 for demo
)
```

#### Symptom C: No rap format for tech companies
```
# NVIDIA profile generates professional message instead of rap
```

**Cause:** Industry detection logic not working

**Solution:**
1. Check the profile data returned by EnrichLayer
2. Verify headline/company name contains "tech", "AI", etc.
3. Debug with print statements:
   ```python
   print(f"Industry: {industry}")
   print(f"Is Tech: {is_tech}")
   ```

---

### 8. Performance Issues

#### Symptom: Agent takes >60 seconds
```
# Extremely slow response
```

**Causes:**
1. Network latency
2. EnrichLayer API slow
3. Too many retry attempts

**Solutions:**
1. Check internet connection
2. Reduce max_turns to 3-5
3. For demo: Use pre-recorded output

#### Symptom: High costs
```
# Each run costs $0.50+
```

**Causes:**
1. max_turns too high
2. Multiple test runs without cleanup

**Solutions:**
1. Set max_turns=3 for demo
2. Use Claude Sonnet 3.5 instead of Opus
3. Track costs in console.anthropic.com

---

## Demo Day Emergencies

### If Claude Agent SDK completely fails:

**Fallback Plan A: Show pre-recorded video**
```bash
# Play the recording from backup/
open backup/agent_demo_recording.mp4
```

**Fallback Plan B: Use n8n workflow**
```bash
# Import n8n.json and demonstrate visually
# No code needed, shows same concept
```

**Fallback Plan C: Show Chained only + explain concept**
- Run chained_outreach.py successfully
- Explain verbally what agent would do differently
- Show screenshots of agent reasoning from slides

### If EnrichLayer API is down:

**Use mock data:**
```python
# Create mock_data.py
MOCK_PROFILES = {
    "jenhsunhuang": {
        "first_name": "Jensen",
        "experiences": [{"company": "NVIDIA", "description": "CEO & Founder"}],
        "industry": "Computer Hardware"
    }
}

# Import in scripts
from mock_data import MOCK_PROFILES
```

---

## Prevention Checklist

Run this 1 hour before workshop:

- [ ] `python verify_setup.py` ✓ passes
- [ ] Test chained workflow with clean URL
- [ ] Test chained workflow with messy URL (should fail)
- [ ] Test agent workflow with messy URL (should self-correct)
- [ ] Check API credits (Anthropic + EnrichLayer)
- [ ] Verify Node.js in PATH
- [ ] Test Claude CLI directly
- [ ] Have backup video ready
- [ ] Print console output as PDF (fallback)
- [ ] Test on presentation laptop (not dev machine!)

---

## Getting Help

1. **Check logs:**
   ```bash
   # Run with verbose output
   PYTHONVERBOSE=1 python agent_outreach.py
   ```

2. **Check GitHub Issues:**
   - Claude Agent SDK: https://github.com/anthropics/claude-agent-sdk-python/issues
   - This repo: <your-repo-url>/issues

3. **Workshop Telegram group:**
   - Post error message
   - Include Python version, OS
   - Share last 20 lines of output

4. **Emergency contact:**
   - During workshop: Ask instructor
   - After workshop: Create issue in repo

---

## Debug Mode

Enable detailed logging:

```python
# Add to top of script
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for Claude Agent SDK specifically
import os
os.environ['CLAUDE_SDK_DEBUG'] = '1'
```

---

## Still Stuck?

Create a minimal reproduction:

```python
# test_minimal.py
import os
from dotenv import load_dotenv

load_dotenv()

print("Python version:", __import__('sys').version)
print("Anthropic key:", os.getenv("ANTHROPIC_API_KEY")[:10] if os.getenv("ANTHROPIC_API_KEY") else "NOT SET")
print("EnrichLayer key:", os.getenv("ENRICHLAYER_API_KEY")[:10] if os.getenv("ENRICHLAYER_API_KEY") else "NOT SET")

try:
    import claude_agent_sdk
    print("✓ Claude Agent SDK imported")
except Exception as e:
    print(f"✗ Import failed: {e}")

try:
    import anthropic
    print("✓ Anthropic imported")
except Exception as e:
    print(f"✗ Import failed: {e}")
```

Run and share output when asking for help.
