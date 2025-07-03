#!/usr/bin/env python3
"""JustiFi LangChain Integration Example

This example demonstrates how to use the JustiFi Agent Toolkit with LangChain
to create AI agents that can interact with JustiFi payout operations.

Requirements:
    pip install langchain-core langchain-openai

Environment Variables:
    JUSTIFI_CLIENT_ID - Your JustiFi client ID
    JUSTIFI_CLIENT_SECRET - Your JustiFi client secret
    OPENAI_API_KEY - Your OpenAI API key (for the example agent)
"""

import asyncio
import os

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from justifi_mcp import JustiFiToolkit


async def main():
    """Demonstrate JustiFi LangChain integration."""
    print("🚀 JustiFi LangChain Integration Example")
    print("=" * 50)

    # Check environment variables
    if not os.getenv("JUSTIFI_CLIENT_ID") or not os.getenv("JUSTIFI_CLIENT_SECRET"):
        print("❌ Missing JustiFi credentials!")
        print("Set JUSTIFI_CLIENT_ID and JUSTIFI_CLIENT_SECRET environment variables")
        return

    # Initialize JustiFi toolkit with configuration
    print("📦 Initializing JustiFi Toolkit...")
    toolkit = JustiFiToolkit(
        configuration={
            "tools": {
                "payouts": {
                    "retrieve": {"enabled": True},
                    "list": {"enabled": True},
                    "status": {"enabled": True},
                    "recent": {"enabled": False},  # Disable for this example
                }
            },
            "context": {
                "environment": "sandbox",
                "timeout": 30,
                "rate_limit": "standard",
            },
        }
    )

    # Get LangChain tools
    print("🔧 Creating LangChain tools...")
    try:
        langchain_tools = toolkit.get_langchain_tools()
        print(f"✅ Created {len(langchain_tools)} LangChain tools:")
        for tool in langchain_tools:
            print(f"   - {tool.name}: {tool.description}")
    except ImportError as e:
        print(f"❌ {e}")
        return

    # Display tool schemas
    print("\n📋 Tool Schemas:")
    for tool in langchain_tools:
        schema = tool.args_schema.model_json_schema()
        print(f"\n{tool.name}:")
        print(f"  Description: {tool.description}")
        print(f"  Required args: {schema.get('required', [])}")
        for prop_name, prop_info in schema.get("properties", {}).items():
            print(
                f"    - {prop_name}: {prop_info.get('type', 'unknown')} - {prop_info.get('description', 'No description')}"
            )

    # Example: Manual tool execution
    print("\n🎯 Example: Manual Tool Execution")
    print("-" * 30)

    # Find the list_payouts tool
    list_tool = next(
        (tool for tool in langchain_tools if tool.name == "list_payouts"), None
    )
    if list_tool:
        try:
            print("Executing list_payouts with limit=5...")
            # Note: This will make a real API call if credentials are valid
            # result = await list_tool.arun({"limit": 5})
            # print(f"Result: {result}")
            print("(Skipped actual execution - would make real API call)")
        except Exception as e:
            print(f"Error: {e}")

    # Example: LangChain Agent (if OpenAI API key is available)
    if os.getenv("OPENAI_API_KEY"):
        print("\n🤖 Example: LangChain Agent with JustiFi Tools")
        print("-" * 40)

        try:
            # Initialize OpenAI LLM
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

            # Create a simple agent-like interaction
            print("Creating AI agent with JustiFi tools...")

            # Bind tools to the LLM
            llm_with_tools = llm.bind_tools(langchain_tools)

            # Example query
            query = "What tools do you have available for working with payouts?"
            print(f"Query: {query}")

            response = await llm_with_tools.ainvoke([HumanMessage(content=query)])
            print(f"Response: {response.content}")

            # Check if the model wants to use tools
            if response.tool_calls:  # type: ignore[attr-defined]
                print(f"🔧 Model wants to use {len(response.tool_calls)} tools:")  # type: ignore[attr-defined]
                for tool_call in response.tool_calls:  # type: ignore[attr-defined]
                    print(f"   - {tool_call['name']}: {tool_call['args']}")

        except Exception as e:
            print(f"❌ Agent example failed: {e}")
    else:
        print("\n💡 Set OPENAI_API_KEY to see the LangChain agent example")

    # Configuration summary
    print("\n⚙️  Configuration Summary:")
    summary = toolkit.get_configuration_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    print("\n✅ Example completed!")
    print("\n📚 Next Steps:")
    print("   1. Set up your JustiFi API credentials")
    print("   2. Explore the available tools and their schemas")
    print("   3. Build custom LangChain agents with JustiFi capabilities")
    print("   4. Use configuration to control which tools are available")


if __name__ == "__main__":
    asyncio.run(main())
