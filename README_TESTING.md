# Testing Guide for LangGraph WhatsApp Agent

This guide provides comprehensive testing strategies to verify your LangGraph WhatsApp agent is working correctly.

## Quick Start

### 1. Run All Tests
```bash
python scripts/test_runner.py --verbose
```

### 2. Interactive Testing
```bash
python scripts/manual_test.py
```

### 3. Individual Test Suites
```bash
# Test the core LangGraph agent
python tests/test_agent_direct.py

# Test the WhatsApp agent wrapper
python tests/test_whatsapp_agent.py

# Test the integration
python tests/test_whatsapp_integration.py
```

## Prerequisites

### Environment Setup

1. **Required Environment Variables:**
   ```bash
   # LangGraph Configuration
   export LANGGRAPH_URL="http://localhost:8123"
   export LANGGRAPH_ASSISTANT_ID="agent"
   export CONFIG="{}"
   
   # Twilio Configuration (for integration tests)
   export TWILIO_AUTH_TOKEN="your_twilio_token"
   export TWILIO_ACCOUNT_SID="your_twilio_sid"
   
   # MCP Server URLs (for agent functionality)
   export ZAPIER_URL_MCP="your_zapier_mcp_url"
   export SUPERMEMORY_URL_MCP="your_supermemory_mcp_url"
   ```

2. **Start LangGraph Server:**
   ```bash
   langgraph up
   ```

3. **Install Dependencies:**
   ```bash
   pip install -e .
   # or
   uv sync
   ```

## Testing Levels

### 1. Direct Agent Testing (`test_agent_direct.py`)

**Purpose:** Test the core LangGraph agent without WhatsApp integration.

**What it tests:**
- Agent initialization
- Message processing through LangGraph
- Calendar agent functionality
- Supervisor coordination

**When to use:** 
- Verify your agent logic works
- Debug agent responses
- Test new agent features

**Example output:**
```
🧪 Testing LangGraph Agent Direct...
✅ Agent initialized successfully
📤 Sending test message: Hello! Can you help me schedule a meeting for tomorrow at 2 PM?
✅ Agent responded successfully!
🤖 Response: I'd be happy to help you schedule a meeting for tomorrow at 2 PM...
```

### 2. WhatsApp Agent Testing (`test_whatsapp_agent.py`)

**Purpose:** Test the WhatsApp Agent class that communicates with LangGraph.

**What it tests:**
- Agent class initialization
- LangGraph SDK communication
- Message formatting
- Image handling
- Error handling

**When to use:**
- Verify LangGraph connectivity
- Test message formatting
- Debug SDK issues

**Example output:**
```
🧪 Testing Agent Initialization...
✅ Agent initialized successfully
📡 LangGraph URL: http://localhost:8123
🆔 Assistant ID: agent
```

### 3. Integration Testing (`test_whatsapp_integration.py`)

**Purpose:** Test the full WhatsApp flow without actual Twilio webhooks.

**What it tests:**
- WhatsApp message parsing
- Twilio request simulation
- TwiML response generation
- Image message handling
- FastAPI endpoint behavior

**When to use:**
- Test end-to-end flow
- Verify Twilio integration
- Debug message handling

**Example output:**
```
🧪 Testing Text Message Handling...
✅ Text message handled successfully
📱 TwiML Response length: 156 chars
🤖 Contains message: True
```

## Testing Tools

### Interactive Manual Testing

Use `scripts/manual_test.py` for hands-on testing:

```bash
python scripts/manual_test.py
```

**Features:**
- Chat directly with your agent
- Send test images
- View configuration
- Run predefined test scenarios

**Commands:**
- `/help` - Show available commands
- `/image` - Send a test image
- `/config` - Show current configuration
- `/quit` - Exit the session

### Comprehensive Test Runner

Use `scripts/test_runner.py` for automated testing:

```bash
# Run all tests
python scripts/test_runner.py

# Run specific tests
python scripts/test_runner.py --tests direct whatsapp

# Verbose output
python scripts/test_runner.py --verbose

# Interactive environment setup
python scripts/test_runner.py --setup-env
```

## Common Testing Scenarios

### 1. Basic Functionality Test
```python
# Test basic greeting
message = "Hello! How are you today?"
response = await agent.invoke("test-user", message)
```

### 2. Calendar Integration Test
```python
# Test calendar functionality
message = "Schedule a meeting for tomorrow at 2 PM"
response = await agent.invoke("test-user", message)
```

### 3. Image Processing Test
```python
# Test image handling
images = [{"image_url": {"url": "data:image/png;base64,..."}}]
response = await agent.invoke("test-user", "What's in this image?", images)
```

### 4. Error Handling Test
```python
# Test with invalid configuration
os.environ["LANGGRAPH_URL"] = "http://invalid-url:9999"
# Should handle the error gracefully
```

## Troubleshooting

### Common Issues

1. **"LangGraph server not accessible"**
   - Start LangGraph server: `langgraph up`
   - Check `LANGGRAPH_URL` environment variable
   - Verify server is running on correct port

2. **"Failed to parse CONFIG as JSON"**
   - Check `CONFIG` environment variable
   - Ensure it's valid JSON: `export CONFIG="{}"`

3. **"Twilio credentials are missing"**
   - Set `TWILIO_AUTH_TOKEN` and `TWILIO_ACCOUNT_SID`
   - Only required for integration tests

4. **"Missing environment variables"**
   - Run setup: `python scripts/test_runner.py --setup-env`
   - Check `.env` file configuration

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Environment Validation

Check your environment with:

```bash
python -c "
import os
print('LANGGRAPH_URL:', os.getenv('LANGGRAPH_URL'))
print('ASSISTANT_ID:', os.getenv('LANGGRAPH_ASSISTANT_ID'))
print('CONFIG:', os.getenv('CONFIG'))
"
```

## Production Testing

### Load Testing

For production readiness, consider:

1. **Concurrent Users:**
   ```python
   import asyncio
   
   async def load_test():
       tasks = []
       for i in range(10):
           task = agent.invoke(f"user-{i}", "Hello!")
           tasks.append(task)
       await asyncio.gather(*tasks)
   ```

2. **Rate Limiting:**
   - Test with rapid message sequences
   - Verify graceful degradation

3. **Error Recovery:**
   - Test with network interruptions
   - Verify retry mechanisms

### Security Testing

1. **Input Validation:**
   - Test with malformed messages
   - Verify XSS protection

2. **Authentication:**
   - Test Twilio signature validation
   - Verify unauthorized access prevention

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test LangGraph WhatsApp Agent

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -e .
      
      - name: Run tests
        run: python scripts/test_runner.py
        env:
          LANGGRAPH_URL: http://localhost:8123
          LANGGRAPH_ASSISTANT_ID: agent
          CONFIG: "{}"
```

## Best Practices

1. **Test Early and Often:** Run tests after each change
2. **Use Realistic Data:** Test with actual message formats
3. **Monitor Performance:** Track response times
4. **Test Edge Cases:** Empty messages, large images, etc.
5. **Automate Testing:** Use CI/CD for consistent testing
6. **Document Results:** Keep testing logs for debugging

## Getting Help

If tests fail:

1. Check the troubleshooting section above
2. Review the verbose test output
3. Verify your environment configuration
4. Test components individually
5. Check LangGraph server logs

For more help, refer to:
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/) 