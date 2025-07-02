# MCP Server Quality Assurance

This directory contains quality assurance resources for the JustiFi MCP Server, focused on MCP-specific testing rather than traditional AI evaluations.

## Philosophy

Unlike traditional AI agents, MCP servers are **infrastructure components** that provide tools to AI models. We don't control tool selection or reasoning - that's handled by the AI model (Claude, GPT-4, etc.). 

Therefore, our quality focus is on:
- **Tool reliability**: Do our tools work correctly?
- **MCP compliance**: Do we follow the MCP protocol properly?
- **Developer experience**: Are our tools easy to use and understand?
- **Integration quality**: Do tools work well together?

## Quality Measures

### 1. Unit & Integration Tests (Primary)
- **Location**: `tests/` directory
- **Coverage**: 70/70 tests passing
- **Focus**: Tool functionality, configuration, error handling

### 2. MCP Protocol Compliance
- **Tool schema validation**
- **MCP message format compliance**
- **Resource and prompt handling**

### 3. Tool Design Quality
- **Clear, descriptive tool names**
- **Comprehensive parameter schemas**
- **Helpful descriptions with examples**
- **Proper error messages**

### 4. Usage Documentation
- **Common usage patterns**
- **Integration examples**
- **Best practices**

## Usage Pattern Examples

The `payout_operations.jsonl` file contains common usage patterns that help:
- **Developers** understand expected tool usage
- **Documentation** with realistic examples  
- **Integration testing** scenarios
- **Tool design validation**

These are **not AI evaluations** but rather **usage specifications** and **integration test cases**.

## Quality Gates

Before releases, we verify:
- [ ] All unit/integration tests pass
- [ ] MCP protocol compliance validated
- [ ] Tool schemas are complete and clear
- [ ] Usage examples are up-to-date
- [ ] Performance benchmarks met
- [ ] Security scans clean

## Tools vs AI Models

**What we test:**
- Tool functionality and reliability
- MCP server behavior
- Integration with MCP clients
- Tool schema quality

**What we don't test:**
- AI model reasoning (not our responsibility)
- Tool selection accuracy (model-dependent)
- Natural language understanding (model capability)
- Conversation context (model feature)

This separation of concerns ensures we focus on what we can control and improve. 