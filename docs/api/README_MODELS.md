# Model Configuration Guide

This guide explains how to configure and switch between different AI models in the qPCR Assistant application.

## Quick Reference

### Change Model

Edit `autogen_app/.env`:

```bash
MODEL_NAME=anthropic/claude-3.5-sonnet
```

Restart the application. That's it!

## Available Models

Your configuration supports these models:

### Via OpenRouter (Recommended)

**Anthropic Claude:**
```bash
MODEL_NAME=anthropic/claude-3.5-sonnet  # ⭐ Best overall
MODEL_NAME=anthropic/claude-3-opus      # Most capable
MODEL_NAME=anthropic/claude-3-haiku     # Fast & cheap
```

**OpenAI:**
```bash
MODEL_NAME=openai/gpt-4o      # Latest GPT-4
MODEL_NAME=openai/gpt-4o-mini # Fast & cheap
```

**Google:**
```bash
MODEL_NAME=google/gemini-2.0-flash-001  # Fast
```

**Others:**
```bash
MODEL_NAME=deepseek/deepseek-chat              # Very cheap
MODEL_NAME=meta-llama/llama-3.1-70b-instruct   # Open source
MODEL_NAME=mistralai/mistral-large             # European AI
```

### Direct Provider Access (Optional)

**OpenAI Direct:**
```bash
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o
```

**Google Direct:**
```bash
GOOGLE_API_KEY=...
MODEL_NAME=gemini-2.5-flash-lite
```

## Setup

### Option 1: Interactive Setup (Easiest)

From the project root:

```bash
./setup_openrouter.sh
```

### Option 2: Manual Setup

1. Copy the template:
   ```bash
   cp autogen_app/.env.template autogen_app/.env
   ```

2. Edit `autogen_app/.env` and add your API key:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   MODEL_NAME=anthropic/claude-3.5-sonnet
   ```

3. Get your OpenRouter API key:
   - Visit https://openrouter.ai/keys
   - Sign up and add credits ($5-10 to start)
   - Copy your API key

## Model Comparison

| Model | Quality | Speed | Cost | Function Calling |
|-------|---------|-------|------|-----------------|
| `anthropic/claude-3.5-sonnet` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Excellent |
| `anthropic/claude-3-opus` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ✅ Excellent |
| `anthropic/claude-3-haiku` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Good |
| `openai/gpt-4o` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Excellent |
| `openai/gpt-4o-mini` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Good |
| `deepseek/deepseek-chat` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⚠️ Varies |
| `google/gemini-2.0-flash-001` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ Good |

## Use Case Recommendations

**Production Workloads:**
- Primary: `anthropic/claude-3.5-sonnet`
- Alternative: `openai/gpt-4o`

**Development & Testing:**
- Primary: `openai/gpt-4o-mini`
- Alternative: `anthropic/claude-3-haiku`

**Budget Projects:**
- Primary: `deepseek/deepseek-chat`
- Alternative: `openai/gpt-4o-mini`

**Maximum Quality (Cost No Object):**
- Primary: `anthropic/claude-3-opus`
- Alternative: `openai/gpt-4o`

**Fastest Responses:**
- Primary: `anthropic/claude-3-haiku`
- Alternative: `google/gemini-2.0-flash-001`

## Estimated Costs

Based on typical qPCR workflow (per session):

| Model | Light Use | Typical Use | Heavy Use |
|-------|-----------|-------------|-----------|
| `deepseek/deepseek-chat` | $0.01 | $0.05 | $0.15 |
| `openai/gpt-4o-mini` | $0.02 | $0.08 | $0.25 |
| `anthropic/claude-3-haiku` | $0.03 | $0.12 | $0.40 |
| `anthropic/claude-3.5-sonnet` | $0.25 | $1.00 | $3.50 |
| `openai/gpt-4o` | $0.20 | $0.85 | $3.00 |
| `anthropic/claude-3-opus` | $1.20 | $5.00 | $18.00 |

*Estimates based on typical workflows. Actual costs vary.*

## Configuration Files

**Main Config:** `OAI_CONFIG_LIST.json`
- Lists all available models and their API configurations
- Usually don't need to edit this

**Environment:** `.env`
- Your API keys
- Selected model name
- Application settings
- **This is what you edit to switch models**

**Template:** `.env.template`
- Template for creating `.env`
- Safe to share (no secrets)

## Troubleshooting

### Model not found
```
ValueError: Model 'xyz' not found in config_list
```

**Solution:** Check that `MODEL_NAME` in `.env` exactly matches a model in `OAI_CONFIG_LIST.json`

### No API keys
```
ERROR: No API keys found
```

**Solution:**
1. Check that `.env` file exists in `autogen_app/` directory
2. Verify `OPENROUTER_API_KEY` is set in `.env`
3. Ensure you have credits in your OpenRouter account

### Function calling issues

Some models have better function calling support than others.

**Best for this app:**
- ✅ `anthropic/claude-3.5-sonnet`
- ✅ `anthropic/claude-3-opus`
- ✅ `openai/gpt-4o`

**Good:**
- ⚠️ `openai/gpt-4o-mini`
- ⚠️ `anthropic/claude-3-haiku`

**Test Before Production:**
- ❓ Other models

### Slow responses

If responses are too slow:
1. Switch to faster model: `anthropic/claude-3-haiku`
2. Or: `openai/gpt-4o-mini`
3. Or: `google/gemini-2.0-flash-001`

### High costs

If costs are too high:
1. Switch to cheaper model: `deepseek/deepseek-chat`
2. Or: `openai/gpt-4o-mini`
3. Monitor usage at: https://openrouter.ai/

## Advanced Configuration

### Custom Headers (Optional)

To add OpenRouter-specific headers, edit `qpcr_assistant.py`:

```python
def _build_llm_config(self) -> Dict[str, Any]:
    config = {
        "config_list": filtered_config_list,
        "timeout": 120,
        "temperature": 0.7,
        "extra_headers": {
            "HTTP-Referer": "https://your-site.com",
            "X-Title": "MDK qPCR Assistant"
        }
    }
    return config
```

### Temperature Control

Adjust creativity/randomness in `.env`:

```bash
# Add to qpcr_assistant.py _build_llm_config:
"temperature": 0.7  # 0.0 = deterministic, 1.0 = creative
```

### Multiple Models

You can keep multiple API keys and switch between providers:

```bash
# In .env
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Switch between:
MODEL_NAME=anthropic/claude-3.5-sonnet  # Via OpenRouter
MODEL_NAME=gpt-4o                        # Via OpenAI direct
MODEL_NAME=gemini-2.5-flash-lite        # Via Google direct
```

## Resources

- **Quick Start:** [QUICKSTART_OPENROUTER.md](./QUICKSTART_OPENROUTER.md)
- **Full Guide:** [OPENROUTER_GUIDE.md](./OPENROUTER_GUIDE.md)
- **OpenRouter Models:** https://openrouter.ai/models
- **OpenRouter Pricing:** https://openrouter.ai/docs#models
- **OpenRouter Dashboard:** https://openrouter.ai/

## Questions?

Check the comprehensive guide: [OPENROUTER_GUIDE.md](./OPENROUTER_GUIDE.md)

Or visit:
- OpenRouter Discord: https://discord.gg/openrouter
- OpenRouter Docs: https://openrouter.ai/docs

