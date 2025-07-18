#!/usr/bin/env python3

"""
LangChain Basic Integration Example for JustiFi MCP Server

This example demonstrates how to use JustiFi tools with LangChain agents
using our dedicated LangChain adapter.

Requirements:
    uv pip install langchain langchain-openai langchain-community

Environment Variables:
    JUSTIFI_CLIENT_ID - Your JustiFi API client ID
    JUSTIFI_CLIENT_SECRET - Your JustiFi API client secret
    OPENAI_API_KEY - Your OpenAI API key (for LangChain agent)
"""

import asyncio
import os

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from python import JustiFiToolkit


async def demonstrate_langchain_basic_integration():
    """Demonstrate basic LangChain integration with JustiFi tools."""
    print("🦜 LangChain Basic Integration Demo\n")

    # Initialize JustiFi toolkit with payout tools
    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=[
            "list_payouts",
            "retrieve_payout",
            "get_payout_status",
            "get_recent_payouts",
        ],
    )

    # Get LangChain tools from our adapter
    langchain_tools = toolkit.get_langchain_tools()

    print(f"📋 Available LangChain Tools: {len(langchain_tools)}")
    for tool in langchain_tools:
        print(f"  • {tool.name}: {tool.description}")
    print()

    # Initialize LangChain LLM
    llm = ChatOpenAI(
        model="gpt-4", temperature=0.1, openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Create agent prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful financial assistant that can analyze payout data using JustiFi tools.

Available tools:
- list_payouts: Get a list of payouts with pagination
- retrieve_payout: Get detailed information about a specific payout
- get_payout_status: Check the status of a specific payout
- get_recent_payouts: Get the most recent payouts

When analyzing payouts:
1. Start with recent payouts to understand current state
2. Look for patterns in amounts, timing, and status
3. Identify any failed or pending payouts that need attention
4. Provide clear, actionable insights

Be thorough but concise in your analysis.""",
            ),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Create OpenAI tools agent
    agent = create_openai_tools_agent(llm, langchain_tools, prompt)

    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=langchain_tools,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True,
    )

    # Example queries
    queries = [
        "Can you show me our recent payouts and their status?",
        "Are there any failed or pending payouts I should be concerned about?",
        "What's the total amount of our recent payouts?",
    ]

    for i, query in enumerate(queries, 1):
        print("=" * 60)
        print(f"📝 Example {i}: {query}")
        print("=" * 60)

        try:
            # Execute query
            result = await agent_executor.ainvoke({"input": query})

            print(f"🤖 Agent Response:\n{result['output']}\n")

        except Exception as e:
            print(f"❌ Error: {e}\n")

    print("✅ LangChain basic integration demo complete!")


async def demonstrate_direct_tool_usage():
    """Demonstrate direct tool usage without an agent."""
    print("\n🔧 Direct Tool Usage Demo\n")

    # Initialize toolkit
    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["list_payouts", "get_recent_payouts"],
    )

    # Get LangChain tools
    langchain_tools = toolkit.get_langchain_tools()

    # Find the list_payouts tool
    list_payouts_tool = next(
        (tool for tool in langchain_tools if tool.name == "list_payouts"), None
    )

    if list_payouts_tool:
        print("🔧 Calling list_payouts tool directly...")

        try:
            # Call tool directly (sync version)
            result = list_payouts_tool.func(limit=5)
            print(f"📊 Direct tool result:\n{result}\n")

            # Call tool async version
            print("🔧 Calling list_payouts tool asynchronously...")
            async_result = await list_payouts_tool.arun({"limit": 3})
            print(f"📊 Async tool result:\n{async_result}\n")

        except Exception as e:
            print(f"❌ Tool execution error: {e}\n")

    print("✅ Direct tool usage demo complete!")


async def demonstrate_error_handling():
    """Demonstrate error handling in LangChain integration."""
    print("\n🛡️ Error Handling Demo\n")

    # Create toolkit with limited tools to test error scenarios
    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["retrieve_payout"],  # Only one tool enabled
    )

    langchain_tools = toolkit.get_langchain_tools()

    if langchain_tools:
        retrieve_tool = langchain_tools[0]

        # Test 1: Valid payout ID (might fail if payout doesn't exist)
        print("🧪 Test 1: Valid tool call with potentially non-existent payout")
        try:
            result = await retrieve_tool.arun({"payout_id": "po_test123"})
            print(f"Result: {result[:100]}...")
        except Exception as e:
            print(f"Expected error (payout not found): {e}")

        # Test 2: Invalid parameters
        print("\n🧪 Test 2: Invalid parameters")
        try:
            result = await retrieve_tool.arun({"invalid_param": "test"})
            print(f"Unexpected success: {result}")
        except Exception as e:
            print(f"Expected validation error: {e}")

        # Test 3: Missing required parameters
        print("\n🧪 Test 3: Missing required parameters")
        try:
            result = await retrieve_tool.arun({})
            print(f"Unexpected success: {result}")
        except Exception as e:
            print(f"Expected parameter error: {e}")

    print("\n✅ Error handling demo complete!")


if __name__ == "__main__":

    async def main():
        await demonstrate_langchain_basic_integration()
        await demonstrate_direct_tool_usage()
        await demonstrate_error_handling()

        print("\n🎯 Key LangChain Integration Features:")
        print("   • Seamless integration with LangChain agents")
        print("   • Both sync and async tool execution")
        print("   • Structured tool schemas with Pydantic validation")
        print("   • Comprehensive error handling and recovery")
        print("   • Direct tool access for custom workflows")
        print("   • Agent-based and programmatic usage patterns")

    asyncio.run(main())
