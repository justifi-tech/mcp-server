#!/usr/bin/env python3

"""
Enhanced LangChain Integration Example for JustiFi MCP Server

This example demonstrates the dedicated LangChain adapter introduced in Phase 2,
showcasing improved integration, error handling, and tool management.

Requirements:
    uv pip install langchain-core langchain-openai

Environment Variables:
    JUSTIFI_CLIENT_ID - Your JustiFi API client ID
    JUSTIFI_CLIENT_SECRET - Your JustiFi API client secret
    OPENAI_API_KEY - Your OpenAI API key (optional, for AI model)
"""

import asyncio
import os

from justifi_mcp import JustiFiToolkit
from justifi_mcp.adapters.langchain import LangChainAdapter
from justifi_mcp.config import JustiFiConfig


async def demonstrate_basic_langchain_integration():
    """Demonstrate basic LangChain integration with the new adapter."""
    print("🔧 Phase 2: Enhanced LangChain Integration Demo\n")

    # Method 1: Using the main toolkit (recommended)
    print("📦 Method 1: Using JustiFiToolkit (Recommended)")
    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["retrieve_payout", "list_payouts", "get_payout_status"],
    )

    try:
        # Get LangChain tools via toolkit
        tools = toolkit.get_langchain_tools()
        print(f"✅ Created {len(tools)} LangChain tools via toolkit")

        # Get tool schemas
        schemas = toolkit.get_langchain_schemas()
        print(f"📋 Retrieved {len(schemas)} tool schemas")

        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")

    except ImportError:
        print("❌ LangChain not installed. Install with: pip install langchain-core")
        return

    print()

    # Method 2: Using the adapter directly (advanced usage)
    print("🔧 Method 2: Using LangChainAdapter Directly (Advanced)")
    config = JustiFiConfig(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["retrieve_payout", "get_recent_payouts"],
    )

    adapter = LangChainAdapter(config)
    direct_tools = adapter.get_langchain_tools()
    print(f"✅ Created {len(direct_tools)} tools via direct adapter")

    for tool in direct_tools:
        print(f"   - {tool.name}: {tool.description}")

    print()


async def demonstrate_tool_execution():
    """Demonstrate direct tool execution with error handling."""
    print("🚀 Tool Execution Demo\n")

    config = JustiFiConfig(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools="all",
    )

    adapter = LangChainAdapter(config)

    # Test 1: Valid tool execution (will fail without real credentials)
    print("🔍 Test 1: Tool Execution")
    try:
        result = await adapter.execute_tool("list_payouts", limit=5)
        print(f"✅ Successfully retrieved payouts: {len(result.get('data', []))} items")
    except Exception as e:
        print(
            f"⚠️  Tool execution failed (expected with demo credentials): {type(e).__name__}"
        )

    # Test 2: Validation error handling
    print("\n🔍 Test 2: Validation Error Handling")
    try:
        await adapter.execute_tool("retrieve_payout", payout_id="")
    except Exception as e:
        print(f"✅ Caught validation error as expected: {e}")

    # Test 3: Disabled tool handling
    print("\n🔍 Test 3: Disabled Tool Handling")
    restricted_config = JustiFiConfig(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["retrieve_payout"],  # Only one tool enabled
    )
    restricted_adapter = LangChainAdapter(restricted_config)

    try:
        await restricted_adapter.execute_tool("list_payouts", limit=5)
    except Exception as e:
        print(f"✅ Caught disabled tool error as expected: {e}")

    print()


async def demonstrate_ai_agent_integration():
    """Demonstrate integration with an AI agent (requires OpenAI API key)."""
    print("🤖 AI Agent Integration Demo\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set, skipping AI agent demo")
        return

    try:
        from langchain_core.messages import HumanMessage
        from langchain_openai import ChatOpenAI
    except ImportError:
        print(
            "❌ LangChain OpenAI not installed. Install with: pip install langchain-openai"
        )
        return

    # Create toolkit with JustiFi tools
    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["retrieve_payout", "list_payouts", "get_payout_status"],
    )

    # Get LangChain tools
    justifi_tools = toolkit.get_langchain_tools()
    print(f"🔧 Loaded {len(justifi_tools)} JustiFi tools for AI agent")

    # Create AI model with tools
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    model_with_tools = model.bind_tools(justifi_tools)

    # Test conversation
    messages = [
        HumanMessage(content="Can you help me check the status of payout po_test123?")
    ]

    print("💬 Sending message to AI agent...")
    try:
        response = model_with_tools.invoke(messages)
        print(f"🤖 AI Response: {response.content}")

        # Check if the model wants to use tools
        if hasattr(response, "tool_calls") and response.tool_calls:
            print(f"🔧 Model wants to use {len(response.tool_calls)} tools:")
            for tool_call in response.tool_calls:
                print(f"   - {tool_call['name']}: {tool_call['args']}")
        else:
            print("💭 Model provided a text response without using tools")

    except Exception as e:
        print(f"❌ AI agent error: {e}")

    print()


async def demonstrate_configuration_flexibility():
    """Demonstrate configuration flexibility and tool filtering."""
    print("⚙️  Configuration Flexibility Demo\n")

    # Scenario 1: Development environment (all tools enabled)
    print("🔧 Scenario 1: Development Environment")
    dev_toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools="all",
    )
    dev_tools = dev_toolkit.get_langchain_tools()
    print(f"   Enabled tools: {[tool.name for tool in dev_tools]}")

    # Scenario 2: Production environment (restricted tools)
    print("\n🏭 Scenario 2: Production Environment (Read-only)")
    prod_toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["retrieve_payout", "list_payouts", "get_payout_status"],
    )
    prod_tools = prod_toolkit.get_langchain_tools()
    print(f"   Enabled tools: {[tool.name for tool in prod_tools]}")

    # Scenario 3: Custom configuration
    print("\n🎯 Scenario 3: Custom Configuration")
    custom_config = JustiFiConfig(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["get_recent_payouts"],
        context={
            "environment": "staging",
            "timeout": 15,
            "rate_limit": "standard",
        },
    )
    custom_toolkit = JustiFiToolkit(config=custom_config)
    custom_tools = custom_toolkit.get_langchain_tools()
    print(f"   Enabled tools: {[tool.name for tool in custom_tools]}")
    print(f"   Configuration: {custom_toolkit.get_configuration_summary()}")

    print()


async def main():
    """Run all demonstration examples."""
    print("🎉 JustiFi LangChain Adapter - Phase 2 Demonstration\n")
    print("=" * 60)

    await demonstrate_basic_langchain_integration()
    await demonstrate_tool_execution()
    await demonstrate_ai_agent_integration()
    await demonstrate_configuration_flexibility()

    print("=" * 60)
    print("✅ All demonstrations completed!")
    print("\n📚 Key improvements in Phase 2:")
    print("   • Dedicated LangChain adapter for better separation of concerns")
    print("   • Enhanced error handling with ValidationError and ToolError")
    print("   • Improved tool schema management")
    print("   • Better configuration flexibility")
    print("   • Lazy loading for performance optimization")


if __name__ == "__main__":
    asyncio.run(main())
