# Lesson 1: Chained vs Agentic Workflows

This workshop demonstrates the key architectural decision for AI products: **when to use deterministic pipelines vs adaptive agents**.

## 🎯 What You'll Learn

Compare two approaches to LinkedIn cold outreach generation:
- **Chained Workflow** (`chained_outreach.py`) - Fast, cheap, brittle "Script Follower"
- **Agentic Workflow** (`agent_outreach.py`) - Slower, smarter "Problem Solver"

## 📋 Prerequisites

- Python 3.10+
- API Keys:
  - [Anthropic API Key](https://console.anthropic.com/settings/keys)
  - [EnrichLayer API Key](https://enrichlayer.com/dashboard/api-key/)

## 🚀 Quick Setup

### 1. Activate Virtual Environment

```bash
# From the lesson1/ directory
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the `lesson1/` directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ENRICHLAYER_API_KEY=your_enrichlayer_api_key_here
```

## 🎮 Running the Demo

### Chained Workflow (Script Follower)

```bash
python chained_outreach.py
```

**Expected behavior:**
- ✅ Clean URL → Works great
- ❌ Messy URL → Fails (missing protocol, typos, etc.)

### Agentic Workflow (Problem Solver)

```bash
python agent_outreach.py
```

**Expected behavior:**
- ✅ Clean URL → Works great
- ✅ Messy URL → Self-corrects and succeeds!

## 📊 Side-by-Side Comparison

| Metric | Chained | Agentic |
|--------|---------|---------|
| **Cost** | $0.01-0.05 | $0.10-0.50 |
| **Speed** | 1-3 sec | 5-20 sec |
| **Success (clean data)** | 95%+ | 95%+ |
| **Success (messy data)** | 40-70% | 85-95%+ |
| **Self-correction** | ❌ None | ✅ Built-in |

## 🧪 Test Cases

The demo uses test cases from `test_cases.py`:

**DEMO_PAIR:**
1. **Clean URL**: `https://www.linkedin.com/in/jenhsunhuang/`
   - Well-formatted, complete
   - Both workflows should succeed

2. **Messy URL**: `linkedin.com/in/jenhsun-huang`
   - Missing `https://www.`
   - Typo in username (hyphen instead of no hyphen)
   - Chained workflow → Fails
   - Agentic workflow → Self-corrects!

## 🔍 What to Watch For

### Chained Workflow
- Fixed sequence of steps
- Direct API call with no error recovery
- Fast failure on bad input
- Predictable, debuggable

### Agentic Workflow
- Agent reasoning displayed in console
- Tool usage (`fetch_linkedin_profile`)
- Self-correction attempts
- Final message generation

## 🛠️ Key Files

- `chained_outreach.py` - Traditional pipeline approach
- `agent_outreach.py` - Claude Agent SDK implementation
- `test_cases.py` - Clean and messy test URLs
- `n8n.json` - n8n workflow (optional, for no-code demo)

## 💡 The Key Insight

> **"If you keep adding IF branches to handle edge cases → use an agent"**

Real-world data is messy:
- Typos and variations
- Missing fields
- Unexpected formats
- Multiple edge cases

**Chained workflows break → Lost opportunities**
**Agentic workflows adapt → Conversions**

## 📚 Next Steps

1. Try modifying the test URLs in `test_cases.py`
2. Add more edge cases
3. Observe how each approach handles them
4. Calculate ROI for your own use case

## 🤝 Workshop Structure

This is **Workshop 1** of the AI Product Engineer course:
- ✅ Lesson 1: Chained vs Agentic Workflows (this)
- 🔜 Lesson 2: LLM-Powered Product Management
- 🔜 Lesson 3: Multi-Agent Systems
- 🔜 Lesson 4: Eval-Driven Development

---

**Questions?** Check the workshop.md for detailed notes and discussion points.
