# JustiFi MCP Client Integration Examples

⚠️ **Important**: These are **CLIENT-SIDE** integration examples that show how to use JustiFi tools from applications that connect to the MCP server. These dependencies are NOT needed for the MCP server itself.

## MCP Architecture Overview

```
┌─────────────────┐    MCP Protocol     ┌──────────────────┐    JustiFi API
│   MCP Client    │◄──────────────────►│   MCP Server     │◄─────────────────►
│ (Your App)      │   (JSON-RPC/stdio) │ (This Project)   │   (Payment API)
│                 │                     │                 │
│ • OpenAI GPT    │                     │ • No AI models  │
│ • Claude        │                     │ • Only JustiFi  │
│ • LangChain     │                     │   credentials   │
│ • Custom AI     │                     │ • Tool provider │
└─────────────────┘                     └──────────────────┘
```

## What's What

### MCP Server (This Repository)
- **Purpose**: Provides JustiFi payment tools via MCP protocol
- **Dependencies**: Only needs JustiFi API credentials
- **No AI models**: Server doesn't need OpenAI/Claude/Anthropic API keys
- **Runs independently**: Can serve multiple clients simultaneously

### MCP Clients (These Examples)
- **Purpose**: Show how to integrate JustiFi tools into AI applications
- **Dependencies**: Each client needs its own AI model credentials
- **Framework-specific**: Different patterns for OpenAI, LangChain, etc.
- **Connect to server**: Use MCP protocol to access JustiFi tools

## Available Examples

### [OpenAI Integration](./openai/)
Examples showing direct usage of JustiFi tools with OpenAI's function calling:
- `basic_integration.py` - Simple function calling
- `advanced_workflows.py` - Complex payout analysis
- `production_patterns.py` - Error handling and monitoring

**Client Requirements**: OpenAI API key, `openai` Python package

### [LangChain Integration](./langchain/)
Examples using LangChain agents and tools framework:
- `basic_integration.py` - LangChain tools setup
- `agent_workflows.py` - Agent-based automation
- `production_patterns.py` - Production deployment patterns

**Client Requirements**: OpenAI/Anthropic API key, `langchain` packages

## Quick Start

1. **Start the MCP server** (in this repository):
   ```bash
   # Only needs JustiFi credentials in .env
   make dev
   ```

2. **Run client examples** (separate environment):
   ```bash
   # Each example has its own dependencies
   cd examples/openai/
   uv pip install openai python-dotenv
   export OPENAI_API_KEY="your_key_here"
   python basic_integration.py
   ```

## Key Points

✅ **MCP Server**: No AI model dependencies, only JustiFi API access  
✅ **Client Examples**: Each needs its own AI model credentials  
✅ **Separation**: Server and clients run independently  
✅ **Flexibility**: One server can serve many different client types  

The MCP protocol enables this clean separation between payment tools (server) and AI reasoning (clients). 