#!/usr/bin/env python3

"""
Simple JustiFi LangChain Agent Example

This example shows how to integrate JustiFi payment tools directly into a LangChain agent
WITHOUT needing to run a separate MCP server. The tools are embedded directly in your agent.

Requirements:
    uv pip install langchain langchain-openai

Environment Variables:
    JUSTIFI_CLIENT_ID - Your JustiFi API client ID
    JUSTIFI_CLIENT_SECRET - Your JustiFi API client secret
    OPENAI_API_KEY - Your OpenAI API key
"""

import asyncio
import os

from justifi_mcp import JustiFiToolkit
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI


async def main():
    """Simple example of JustiFi + LangChain integration."""

    print("🚀 JustiFi LangChain Agent - No MCP Server Required!\n")

    # Step 1: Initialize JustiFi toolkit with your credentials
    # This creates the tools directly in your process - no external server needed
    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=[
            "list_payouts",
            "retrieve_payout",
            "get_payout_status",
            "list_payments",
            "retrieve_payment"
        ]
    )

    # Step 2: Get LangChain tools directly from the toolkit
    # These are native LangChain StructuredTool instances
    tools = toolkit.get_langchain_tools()

    print(f"✅ Loaded {len(tools)} JustiFi tools:")
    for tool in tools:
        print(f"   • {tool.name}: {tool.description}")
    print()

    # Step 3: Create your LangChain agent with the tools
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.1,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful financial assistant that can analyze payment data.
        
Available JustiFi tools:
- list_payouts: Get recent payouts
- retrieve_payout: Get detailed payout information
- get_payout_status: Check payout status
- list_payments: Get recent payments
- retrieve_payment: Get detailed payment information

Always provide clear, actionable insights based on the data you retrieve."""),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5
    )

    # Step 4: Use your agent with JustiFi tools
    queries = [
        "Show me our 3 most recent payouts and their status",
        "What's the total amount of recent payouts?",
        "Are there any failed or pending payouts I should know about?"
    ]

    for i, query in enumerate(queries, 1):
        print("=" * 60)
        print(f"Query {i}: {query}")
        print("=" * 60)

        try:
            result = await agent_executor.ainvoke({"input": query})
            print(f"🤖 Response: {result['output']}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

    print("✅ Demo complete! The JustiFi tools ran directly in your agent process.")
    print("💡 No MCP server was needed - everything runs in your LangChain agent!")


if __name__ == "__main__":
    asyncio.run(main())
