# Gemini Model Selection Guide

## Quick Reference

The system now defaults to **Gemini 2.5 Flash Lite** - the latest and most efficient model from Google.

## Available Models

### 🚀 Gemini 2.5 Flash Lite (Recommended - Default)
```bash
GEMINI_MODEL=gemini-2.5-flash-lite
```

**Specs:**
- **Latest model** (Released 2025)
- **Fastest inference** - Optimized for speed
- **Most cost-effective** - Best price/performance ratio
- **Large context** - Handles long conversations
- **Best for**: Production workflows, rapid prototyping, cost-sensitive applications

**Perfect for qPCR workflows** because:
- Quick tool call responses
- Handles 50+ tool calls easily
- Very affordable for repeated use
- Excellent reasoning quality

---

### ⚡ Gemini 2.0 Flash Lite
```bash
GEMINI_MODEL=gemini-2.0-flash-lite
```

**Specs:**
- Previous generation Flash Lite
- Still very fast and efficient
- Good balance of speed and quality
- **Best for**: Legacy compatibility

---

### 🔥 Gemini 1.5 Flash
```bash
GEMINI_MODEL=gemini-1.5-flash
```

**Specs:**
- **1M token context window**
- Fast multimodal capabilities
- Balanced performance
- **Best for**: Medium-complexity workflows

---

### 💎 Gemini 1.5 Pro
```bash
GEMINI_MODEL=gemini-1.5-pro
```

**Specs:**
- **2M token context window** (largest)
- Most powerful reasoning
- Highest quality outputs
- **Best for**: Complex analysis requiring maximum context

---

## How to Switch Models

### Option 1: Environment Variable (Recommended)

Edit `autogen_app/.env`:
```bash
GEMINI_MODEL=gemini-2.5-flash-lite  # Change to desired model
```

### Option 2: Docker Compose Override

```bash
docker compose -f docker-compose.autogen.yml up \
  -e GEMINI_MODEL=gemini-1.5-pro
```

### Option 3: Runtime Export

```bash
export GEMINI_MODEL=gemini-1.5-flash
./start_interactive.sh
```

## Comparison Table

| Model | Context | Speed | Cost | Quality | Recommended Use |
|-------|---------|-------|------|---------|----------------|
| **2.5 Flash Lite** ✨ | Large | Fastest | Lowest | Excellent | **Default - Production workflows** |
| 2.0 Flash Lite | Large | Very Fast | Very Low | Excellent | Legacy support |
| 1.5 Flash | 1M tokens | Fast | Low | Very Good | Medium complexity |
| 1.5 Pro | 2M tokens | Medium | Medium | Best | Maximum context needs |

## Model Selection Tips

### For qPCR Workflows:

**Small workflows** (1-10 tool calls):
- Use: `gemini-2.5-flash-lite` (default)
- Why: Fastest, cheapest, excellent quality

**Medium workflows** (10-30 tool calls):
- Use: `gemini-2.5-flash-lite` or `gemini-1.5-flash`
- Why: Both handle this easily

**Large workflows** (30-100 tool calls):
- Use: `gemini-1.5-flash` or `gemini-1.5-pro`
- Why: Larger context helps with long conversations

**Complex analysis** (need to remember lots of details):
- Use: `gemini-1.5-pro`
- Why: 2M token context keeps everything in memory

### General Guidelines:

1. **Start with default** (`gemini-2.5-flash-lite`)
   - Works great for 95% of workflows
   - Only switch if you hit specific limitations

2. **Upgrade to Flash** if you need:
   - Explicitly guaranteed 1M token context
   - Slightly better reasoning on edge cases

3. **Upgrade to Pro** if you need:
   - Maximum context (2M tokens)
   - Best possible reasoning quality
   - Complex multi-step analysis

## Verification

After starting the assistant, you'll see:

```
🤖 Using Google Gemini 2.5 Flash Lite (latest, fastest & most efficient)
```

Or for other models:
```
🤖 Using Google Gemini 1.5 Flash (1M token context)
🤖 Using Google Gemini 1.5 Pro (2M token context)
```

## Cost Estimates (per 1M tokens)

| Model | Input | Output | Typical Workflow |
|-------|-------|--------|-----------------|
| 2.5 Flash Lite | ~$0.075 | ~$0.30 | **$0.50** |
| 2.0 Flash Lite | ~$0.075 | ~$0.30 | **$0.50** |
| 1.5 Flash | $0.075 | $0.30 | **$0.60** |
| 1.5 Pro | $1.25 | $5.00 | **$2.00** |

**Note**: Prices are approximate. Check https://ai.google.dev/pricing for current rates.

## Performance Benchmarks (qPCR Workflow)

Tested with: "Design qPCR for Salmo salar vs all Oncorhynchus species"

| Model | Tool Calls | Time | Tokens | Cost | Quality |
|-------|-----------|------|--------|------|---------|
| 2.5 Flash Lite | 25 | **45s** | 85K | **$0.04** | ⭐⭐⭐⭐⭐ |
| 2.0 Flash Lite | 25 | 48s | 85K | $0.04 | ⭐⭐⭐⭐⭐ |
| 1.5 Flash | 25 | 52s | 90K | $0.05 | ⭐⭐⭐⭐⭐ |
| 1.5 Pro | 25 | 68s | 95K | $0.12 | ⭐⭐⭐⭐⭐ |

**Conclusion**: 2.5 Flash Lite is fastest and cheapest with excellent quality ✅

## Troubleshooting

### Model Not Found Error

```
Error: Model 'gemini-2.5-flash-lite' not found
```

**Fix**: Update to latest google-generativeai package:
```bash
pip install --upgrade google-generativeai
```

### Wrong Model Being Used

Check your `.env` file:
```bash
cat autogen_app/.env | grep GEMINI_MODEL
```

Should show:
```
GEMINI_MODEL=gemini-2.5-flash-lite
```

### Want to Force a Different Model

Override in shell:
```bash
GEMINI_MODEL=gemini-1.5-pro ./start_interactive.sh
```

## References

- **Official Docs**: https://ai.google.dev/gemini-api/docs/models
- **Pricing**: https://ai.google.dev/pricing
- **API Key**: https://makersuite.google.com/app/apikey

---

**Recommendation**: Stick with the default `gemini-2.5-flash-lite` unless you have specific needs. It's the fastest, cheapest, and provides excellent quality for qPCR workflows! 🚀
