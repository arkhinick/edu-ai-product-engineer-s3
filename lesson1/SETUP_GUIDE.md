# Setup Guide: LinkedIn Outreach Demo

## Prerequisites

Before starting, ensure you have:
- **Python 3.10 or higher** (`python3 --version`)
- **Node.js** (required for Claude CLI)
- **Git** (to clone repository)

## Step 1: System Requirements Check

### macOS/Linux
```bash
# Check Python version (must be 3.10+)
python3 --version

# Check Node.js (required for Claude Agent SDK)
node --version

# Check if Claude CLI is installed
/usr/local/bin/claude --version
```

### Windows
```powershell
# Check Python version
python --version

# Check Node.js
node --version

# Claude CLI location
where claude
```

**✅ Expected Output:**
- Python: 3.10.x or higher
- Node.js: Any recent version (16.x+)
- Claude CLI: 2.x.x

**❌ If missing:** See [Troubleshooting](#troubleshooting) section below

---

## Step 2: Clone Repository

```bash
cd ~/projects  # or your preferred directory
git clone <your-repo-url>
cd edu-ai-product-engineer-s3/lesson1
```

---

## Step 3: Create Virtual Environment

**Why?** Isolates dependencies, makes sharing with team easier

```bash
# Create venv with Python 3.11
python3.11 -m venv venv

# Activate venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Verify activation (should show venv path)
which python
```

---

## Step 4: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(claude|anthropic|requests)"
```

**✅ Expected packages:**
- `claude-agent-sdk` 0.1.9
- `anthropic` 0.74.1+
- `requests` 2.32.5+
- `python-dotenv` 1.2.1+

---

## Step 5: Get API Keys

### Anthropic API Key
1. Go to https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Copy the key (starts with `sk-ant-...`)
4. **Save it securely** - you won't see it again!

### EnrichLayer API Key
1. Go to https://enrichlayer.com/dashboard/api-key/
2. Sign up for free account (if needed)
3. Copy your API key
4. **Note**: Free tier has rate limits (~100 requests/day)

---

## Step 6: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Add your keys:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
ENRICHLAYER_API_KEY=your-enrichlayer-key-here
```

**⚠️ Security Note:**
- Never commit `.env` to git
- Keep API keys secret
- Rotate keys if accidentally exposed

---

## Step 7: Verify Setup

Run the verification script:
```bash
python verify_setup.py
```

**✅ Success Output:**
```
✓ Python version: 3.11.9 (OK)
✓ Node.js found: v20.3.1
✓ Claude CLI found: 2.0.0
✓ Virtual environment: Active
✓ Dependencies installed: 12/12
✓ ANTHROPIC_API_KEY: Set (sk-ant-...*****)
✓ ENRICHLAYER_API_KEY: Set (enr_...*****)
✓ API connectivity test: Success

🎉 All checks passed! Ready to run demos.
```

---

## Step 8: Run Demos

### Test Chained Workflow
```bash
python chained_outreach.py
```

**Expected:**
- Clean URL succeeds
- Messy URL fails immediately

### Test Agentic Workflow
```bash
# Make sure Node.js is in PATH
env PATH="/usr/local/bin:$PATH" python agent_outreach.py
```

**Expected:**
- Clean URL succeeds
- Messy URL self-corrects and succeeds!
- You see agent reasoning in console

---

## Troubleshooting

### Python Version Issues

**Problem:** `python3.10: command not found`

**Solution:**
```bash
# macOS (using Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11

# Verify
python3.11 --version
```

### Node.js Not Found

**Problem:** `env: node: No such file or directory`

**Solution:**
```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm

# Verify
node --version
```

### Claude CLI Issues

**Problem:** Claude CLI not found or not working

**Solution:**
```bash
# Install Claude CLI
curl -fsSL https://claude.ai/install.sh | bash

# Verify PATH
echo $PATH | grep "/usr/local/bin"

# If not in PATH, add to ~/.zshrc or ~/.bashrc
export PATH="/usr/local/bin:$PATH"
```

### API Key Errors

**Problem:** `API key not found` or `401 Unauthorized`

**Solutions:**
1. Check `.env` file exists in `lesson1/` directory
2. Verify no extra spaces in API keys
3. Ensure keys are valid (test in browser console)
4. For Anthropic: Check credits at https://console.anthropic.com/
5. For EnrichLayer: Check rate limits

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'claude_agent_sdk'`

**Solution:**
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify
python -c "import claude_agent_sdk; print('OK')"
```

### Agent Timeout Errors

**Problem:** `Control request timeout: initialize`

**Solutions:**
1. Ensure Node.js is accessible:
   ```bash
   which node  # Should show path
   ```
2. Run with explicit PATH:
   ```bash
   env PATH="/usr/local/bin:$PATH" python agent_outreach.py
   ```
3. Check Claude CLI works:
   ```bash
   /usr/local/bin/claude --version
   ```

---

## Next Steps

Once setup is complete:
1. ✅ Review `README.md` for demo overview
2. ✅ Run both workflows side-by-side
3. ✅ Modify `test_cases.py` with your own LinkedIn URLs
4. ✅ Calculate ROI for your use case
5. ✅ Check `workshop.md` for teaching notes

---

## Getting Help

- **Workshop-specific**: Ask in Telegram group
- **Claude Agent SDK**: https://github.com/anthropics/claude-agent-sdk-python
- **EnrichLayer API**: https://enrichlayer.com/docs
- **General setup**: Create issue in repository

---

## Quick Reference

### Common Commands

```bash
# Activate venv
source venv/bin/activate

# Run chained workflow
python chained_outreach.py

# Run agentic workflow
env PATH="/usr/local/bin:$PATH" python agent_outreach.py

# Deactivate venv
deactivate

# Update dependencies
pip install -r requirements.txt --upgrade
```

### File Structure
```
lesson1/
├── .env                    # Your API keys (git ignored)
├── .env.example           # Template
├── requirements.txt       # Dependencies
├── chained_outreach.py    # Script Follower
├── agent_outreach.py      # Problem Solver
├── test_cases.py          # Test URLs
├── README.md              # Overview
├── SETUP_GUIDE.md         # This file
└── venv/                  # Virtual environment
```

Happy coding! 🚀
