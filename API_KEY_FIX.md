# API Key Resolution Fix

## Problem

AG2 (AutoGen 0.2.x) doesn't automatically resolve environment variable placeholders in `OAI_CONFIG_LIST.json`. When the config file contains:

```json
{
    "model": "gemini-2.5-flash-lite",
    "api_type": "google",
    "api_key": "env:GOOGLE_API_KEY"
}
```

AG2 would pass the literal string `"env:GOOGLE_API_KEY"` to the Gemini API, resulting in:

```
❌ ERROR: 400 INVALID_ARGUMENT
{'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.'}}
```

## Root Cause

Unlike some frameworks (like LangChain), AG2 doesn't have built-in support for the `"env:VAR_NAME"` syntax. It expects actual API key values in the config list.

## Solution

Added environment variable resolution logic in `qpcr_assistant.py` at startup (lines 901-920):

```python
# Resolve environment variables in config_list
# AG2 doesn't automatically resolve "env:VAR_NAME" syntax
for config in config_list:
    api_key = config.get("api_key", "")
    if isinstance(api_key, str) and api_key.startswith("env:"):
        env_var = api_key[4:]  # Remove "env:" prefix
        actual_key = os.getenv(env_var)
        if actual_key:
            config["api_key"] = actual_key
        else:
            # Remove config if key not available
            config["api_key"] = None

# Filter out configs with missing API keys
config_list = [cfg for cfg in config_list if cfg.get("api_key")]

if not config_list:
    print_colored("\n❌ ERROR: No valid API configurations found.", Colors.BRIGHT_RED, bold=True)
    print_colored("Please check that API keys are set in autogen_app/.env\n", Colors.WHITE)
    return
```

## How It Works

1. **Load config file**: Read `OAI_CONFIG_LIST.json`
2. **Check for placeholders**: Look for `api_key` values starting with `"env:"`
3. **Resolve variables**: Replace `"env:VAR_NAME"` with actual value from `os.getenv("VAR_NAME")`
4. **Filter invalid configs**: Remove any configs where the API key couldn't be resolved
5. **Validate**: Ensure at least one valid config remains

## Benefits

1. **Security**: API keys stay in `.env` file (not committed to git)
2. **Flexibility**: Easy to switch between models/providers
3. **Docker-friendly**: Environment variables work seamlessly in containers
4. **Error handling**: Clear error messages if keys are missing

## Example Configuration

### OAI_CONFIG_LIST.json
```json
[
    {
        "model": "gemini-2.5-flash-lite",
        "api_type": "google",
        "api_key": "env:GOOGLE_API_KEY"
    },
    {
        "model": "gpt-4",
        "api_type": "openai",
        "api_key": "env:OPENAI_API_KEY"
    }
]
```

### .env
```bash
GOOGLE_API_KEY=AIzaSyB26c5f6JdMiwZdSHnOwx-KKGEyBY7gEmE
OPENAI_API_KEY=sk-proj-unDYjpyGW48TUlLdpvtUbxR6...
```

### Result at Runtime
```python
config_list = [
    {
        "model": "gemini-2.5-flash-lite",
        "api_type": "google",
        "api_key": "AIzaSyB26c5f6JdMiwZdSHnOwx-KKGEyBY7gEmE"  # Resolved!
    },
    {
        "model": "gpt-4",
        "api_type": "openai",
        "api_key": "sk-proj-unDYjpyGW48TUlLdpvtUbxR6..."  # Resolved!
    }
]
```

## Testing

### 1. Verify Environment Variables
```bash
docker exec qpcr-assistant python -c "
import os
print('GOOGLE_API_KEY:', 'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET')
print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')
"
```

Expected output:
```
GOOGLE_API_KEY: SET
OPENAI_API_KEY: SET
```

### 2. Test Config Resolution
```bash
docker exec qpcr-assistant python -c "
import json
import os

with open('/app/OAI_CONFIG_LIST.json') as f:
    config_list = json.load(f)

# Resolve environment variables
for config in config_list:
    api_key = config.get('api_key', '')
    if api_key.startswith('env:'):
        config['api_key'] = os.getenv(api_key[4:])

# Check resolved keys
for cfg in config_list:
    key = cfg['api_key']
    print(f'{cfg[\"model\"]}: {key[:20]}...' if key and len(key) > 20 else f'{cfg[\"model\"]}: MISSING')
"
```

Expected output:
```
gemini-2.5-flash-lite: AIzaSyB26c5f6JdMiwZd...
gpt-4: sk-proj-unDYjpyGW48T...
```

### 3. Test Gemini API
```bash
docker exec qpcr-assistant python -c "
import os
import google.generativeai as genai

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash-lite')
response = model.generate_content('Say hello')
print('✅ Gemini works:', response.text)
"
```

Expected output:
```
✅ Gemini works: Hello! 👋 How can I help you today?
```

## Error Messages

### Missing API Key
```
❌ ERROR: No API keys found.
Please set GOOGLE_API_KEY or OPENAI_API_KEY in autogen_app/.env
```

### Invalid API Key After Resolution
```
❌ ERROR: No valid API configurations found.
Please check that API keys are set in autogen_app/.env
```

### API Key Invalid (from Gemini)
```
❌ ERROR: 400 INVALID_ARGUMENT
{'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.'}}
```

This last error means the API key was resolved but is invalid (expired, wrong key, etc.). Check your `.env` file.

## Alternative Approaches

### 1. Direct API Key in Config (Not Recommended)
```json
{
    "model": "gemini-2.5-flash-lite",
    "api_type": "google",
    "api_key": "AIzaSyB26c5f6JdMiwZdSHnOwx-KKGEyBY7gEmE"
}
```

**Problem**: API keys committed to git (security risk)

### 2. Separate Config for Each Environment
```bash
# Load different config based on environment
config_file = "OAI_CONFIG_LIST.prod.json" if is_production else "OAI_CONFIG_LIST.dev.json"
```

**Problem**: Multiple config files to maintain

### 3. Environment Variables Only (Current Solution)
```json
{
    "api_key": "env:GOOGLE_API_KEY"
}
```

**Benefits**:
- ✅ Secure (no keys in git)
- ✅ Single config file
- ✅ Docker-friendly
- ✅ Easy to switch environments

## Status

✅ **FIXED AND TESTED**
- Environment variable resolution working
- Gemini API calls successful
- Error handling in place
- Documentation complete

**Date**: 2025-10-01
**Version**: AG2 0.9.9 with custom env resolution

---

**API keys are now properly resolved from environment variables!** 🔐
