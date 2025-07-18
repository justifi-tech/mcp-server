# OpenAI Integration Examples

This directory contains comprehensive examples demonstrating how to integrate JustiFi tools with OpenAI's function calling capabilities.

## 🎯 **Why No Adapter Needed?**

Unlike other frameworks, OpenAI function calling works directly with our existing tool schemas. Our `TOOL_SCHEMAS` are already in OpenAI-compatible JSON format, making integration seamless and lightweight.

## 📋 **Available Examples**

### 1. **Basic Integration** (`basic_integration.py`)
- **Purpose**: Simple OpenAI function calling with JustiFi tools
- **Features**:
  - Direct schema conversion to OpenAI format
  - Function call handling and execution
  - Error handling and response processing
- **Best for**: Getting started, understanding the basics

### 2. **Advanced Workflows** (`advanced_workflows.py`)
- **Purpose**: Sophisticated AI-driven payment analysis workflows
- **Features**:
  - Multi-step AI analysis with tool feedback
  - Parallel tool execution for performance
  - Streaming responses with tool integration
  - Custom PaymentAnalysisAssistant class
  - Iterative analysis with conversation memory
- **Best for**: Complex analysis tasks, production workflows

### 3. **Production Patterns** (`production_patterns.py`)
- **Purpose**: Enterprise-ready patterns for production deployment
- **Features**:
  - Comprehensive configuration management
  - Rate limiting and timeout handling
  - Retry logic with exponential backoff
  - Performance monitoring and metrics
  - Security best practices
  - Concurrent execution with semaphores
- **Best for**: Production deployments, enterprise applications

## 🚀 **Quick Start**

### Prerequisites
```bash
# Install required packages
uv pip install openai

# Set environment variables
export JUSTIFI_CLIENT_ID="your_client_id"
export JUSTIFI_CLIENT_SECRET="your_client_secret"
export OPENAI_API_KEY="your_openai_key"
```

### Run Examples
```bash
# Basic integration
python examples/openai/basic_integration.py

# Advanced workflows
python examples/openai/advanced_workflows.py

# Production patterns
python examples/openai/production_patterns.py
```

## 🔧 **Integration Pattern**

The core pattern for OpenAI integration:

```python
from python import JustiFiToolkit, get_tool_schemas
import openai

# 1. Initialize toolkit
toolkit = JustiFiToolkit(
    client_id="your_id",
    client_secret="your_secret",
    enabled_tools=["list_payouts", "retrieve_payout", "list_payments", "retrieve_payment"]
)

# 2. Convert schemas to OpenAI format
openai_functions = []
for tool_name in toolkit.get_enabled_tools():
    schema = TOOL_SCHEMAS[tool_name]
    openai_functions.append({
        "type": "function",
        "function": {
            "name": tool_name,
            "description": schema["description"],
            "parameters": schema["parameters"]
        }
    })

# 3. Use with OpenAI
client = openai.AsyncOpenAI()
response = await client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Analyze recent payments and payouts"}],
    tools=openai_functions,
    tool_choice="auto"
)

# 4. Handle function calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        # Execute with toolkit
        result = await toolkit.call_tool(function_name, arguments)
```

## 📊 **Example Use Cases**

### Financial Analysis
- Automated payment and payout performance reports
- Risk assessment and anomaly detection
- Trend analysis and forecasting
- Compliance monitoring

### Operations Management
- Payment and payout status monitoring
- Failed transaction investigation
- Performance optimization recommendations
- Automated alerting systems

### Business Intelligence
- Executive dashboards with AI insights
- Automated report generation
- Data-driven decision support
- KPI tracking and analysis

## 🛡️ **Security Considerations**

When using these examples in production:

1. **API Key Management**: Use environment variables or secure key management
2. **Input Validation**: Validate all user inputs before processing
3. **Rate Limiting**: Implement appropriate rate limits for your use case
4. **Error Handling**: Never expose internal errors to end users
5. **Logging**: Log security events but avoid logging sensitive data

## 🔗 **Related Resources**

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [JustiFi API Documentation](https://docs.justifi.ai/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)

## 💡 **Tips for Success**

1. **Start Simple**: Begin with `basic_integration.py` to understand the fundamentals
2. **Use Async**: Always use async/await for better performance
3. **Handle Errors**: Implement comprehensive error handling for production use
4. **Monitor Performance**: Track token usage and response times
5. **Test Thoroughly**: Test with various scenarios including edge cases 