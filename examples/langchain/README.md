# LangChain Integration Examples

This directory contains comprehensive examples demonstrating how to integrate JustiFi tools with LangChain agents and workflows using our dedicated LangChain adapter.

## 🎯 **Why a Dedicated Adapter?**

LangChain requires specific tool wrapping and schema formats. Our dedicated adapter provides:
- **StructuredTool integration** with Pydantic validation
- **Async/sync compatibility** for different LangChain patterns
- **Error handling** with LangChain-specific error types
- **Memory integration** for stateful conversations

## 📋 **Available Examples**

### 1. **Basic Integration** (`basic_integration.py`)
- **Purpose**: Fundamental LangChain agent integration with JustiFi tools
- **Features**:
  - OpenAI Tools Agent with JustiFi capabilities
  - Direct tool usage (sync and async)
  - Error handling demonstrations
  - Agent executor configuration
- **Best for**: Getting started, understanding LangChain basics

### 2. **Agent Workflows** (`agent_workflows.py`)
- **Purpose**: Advanced agent patterns and multi-agent coordination
- **Features**:
  - ReAct agents for step-by-step reasoning
  - Conversation memory and context retention
  - Specialized agents for different tasks
  - Multi-agent workflow coordination
  - Custom tool integration alongside JustiFi tools
- **Best for**: Complex workflows, specialized analysis tasks

### 3. **Production Patterns** (`production_patterns.py`)
- **Purpose**: Enterprise-ready LangChain deployment patterns
- **Features**:
  - Production configuration management
  - Performance monitoring with custom callbacks
  - Rate limiting and session management
  - Comprehensive error handling and retry logic
  - Scalable agent architectures
  - Security and input validation
- **Best for**: Production deployments, enterprise applications

## 🚀 **Quick Start**

### Prerequisites
```bash
# Install required packages
uv pip install langchain langchain-openai langchain-community

# Set environment variables
export JUSTIFI_CLIENT_ID="your_client_id"
export JUSTIFI_CLIENT_SECRET="your_client_secret"
export OPENAI_API_KEY="your_openai_key"
```

### Run Examples
```bash
# Basic integration
python examples/langchain/basic_integration.py

# Agent workflows
python examples/langchain/agent_workflows.py

# Production patterns
python examples/langchain/production_patterns.py
```

## 🔧 **Integration Pattern**

The core pattern for LangChain integration:

```python
from python import JustiFiToolkit
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

# 1. Initialize toolkit
toolkit = JustiFiToolkit(
    client_id="your_id",
    client_secret="your_secret",
    enabled_tools=["list_payouts", "retrieve_payout", "list_payments", "retrieve_payment"]
)

# 2. Get LangChain tools via adapter
langchain_tools = toolkit.get_langchain_tools()

# 3. Create LLM and prompt
llm = ChatOpenAI(model="gpt-4", temperature=0.1)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a financial analyst with access to comprehensive payment management tools."),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 4. Create agent
agent = create_openai_tools_agent(llm, langchain_tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=langchain_tools, verbose=True)

# 5. Execute
result = await agent_executor.ainvoke({"input": "Analyze recent payments and payouts"})
```

## 📊 **Agent Types Demonstrated**

### ReAct Agents
- **Purpose**: Step-by-step reasoning with tool calls
- **Best for**: Complex analysis requiring multiple steps
- **Features**: Explicit reasoning traces, tool call explanations

### OpenAI Tools Agents
- **Purpose**: Modern function calling with OpenAI models
- **Best for**: Efficient tool usage, parallel function calls
- **Features**: Optimized for GPT-4, structured tool schemas

### Specialized Agents
- **Purpose**: Domain-specific agents for particular tasks
- **Examples**: PaymentAnalysisAgent, PayoutReportingAgent, DisputeHandlingAgent
- **Features**: Custom prompts, specialized memory, task-focused tools

### Multi-Agent Systems
- **Purpose**: Coordination between multiple specialized agents
- **Pattern**: Analysis agent → Reporting agent → Action planning
- **Benefits**: Separation of concerns, specialized expertise

## 🧠 **Memory and State Management**

### Conversation Memory
```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    output_key="output",
    return_messages=True,
    k=10  # Remember last 10 exchanges
)
```

### Agent State Tracking
- Session management with unique IDs
- Performance metrics collection
- Error tracking and recovery
- Context preservation across interactions

## 🔧 **Custom Tool Integration**

Combine JustiFi tools with custom tools:

```python
from langchain_core.tools import Tool

# Custom calculation tool
def calculate_metrics(data: str) -> str:
    # Your custom logic here
    return json.dumps(metrics)

custom_tool = Tool(
    name="calculate_metrics",
    description="Calculate financial metrics",
    func=calculate_metrics
)

# Combine with JustiFi tools
all_tools = toolkit.get_langchain_tools() + [custom_tool]
```

## 📊 **Example Use Cases**

### Financial Analysis Workflows
- Multi-step payment and payout trend analysis
- Risk assessment with reasoning traces
- Compliance checking with audit trails
- Performance optimization recommendations

### Automated Reporting
- Executive summary generation
- Scheduled payment and payout status reports
- Anomaly detection and alerting
- Data-driven insights and recommendations

### Interactive Analysis
- Conversational payment exploration
- Follow-up questions with context
- Iterative analysis refinement
- Memory-based investigation flows

## 🛡️ **Production Considerations**

### Performance Optimization
- **Async execution**: Use `ainvoke` for better performance
- **Tool parallelization**: LangChain handles concurrent tool calls
- **Memory management**: Configure appropriate memory windows
- **Caching**: Implement result caching for repeated queries

### Error Handling
- **Graceful degradation**: Handle tool failures elegantly
- **Retry logic**: Implement exponential backoff for transient failures
- **Input validation**: Validate user inputs before processing
- **Error logging**: Comprehensive error tracking and monitoring

### Security
- **Input sanitization**: Validate and sanitize all user inputs
- **Tool restrictions**: Limit available tools per environment
- **Rate limiting**: Implement appropriate rate limits
- **Audit logging**: Log all tool calls and results

## 🔗 **Related Resources**

- [LangChain Documentation](https://python.langchain.com/)
- [LangChain Agents Guide](https://python.langchain.com/docs/modules/agents/)
- [JustiFi API Documentation](https://docs.justifi.ai/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

## 💡 **Tips for Success**

1. **Start with Basic**: Begin with `basic_integration.py` to understand the adapter
2. **Use Async**: Always use async patterns for better performance
3. **Monitor Performance**: Track agent execution times and tool usage
4. **Handle Errors**: Implement comprehensive error handling
5. **Test Thoroughly**: Test with various scenarios and edge cases
6. **Optimize Memory**: Configure memory settings based on your use case
7. **Specialize Agents**: Create domain-specific agents for better results 