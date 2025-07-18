#!/usr/bin/env python3

"""
OpenAI Advanced Workflows Example for JustiFi MCP Server

This example demonstrates advanced patterns including:
- Multi-step payout analysis workflows
- Error handling and retry logic
- Streaming responses
- Custom function orchestration

Requirements:
    uv pip install openai

Environment Variables:
    JUSTIFI_CLIENT_ID - Your JustiFi API client ID
    JUSTIFI_CLIENT_SECRET - Your JustiFi API client secret
    OPENAI_API_KEY - Your OpenAI API key
"""

import asyncio
import json
import os
from typing import Any

import openai

from python import JustiFiToolkit, get_tool_schemas


class PayoutAnalysisAssistant:
    """Advanced OpenAI assistant with JustiFi payout analysis capabilities."""

    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.justifi_toolkit = JustiFiToolkit(
            client_id=os.getenv("JUSTIFI_CLIENT_ID"),
            client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
            enabled_tools=[
                "list_payouts",
                "retrieve_payout",
                "get_payout_status",
                "get_recent_payouts",
            ],
        )

        # Convert schemas to OpenAI format
        self.tools = self._create_openai_tools()

    def _create_openai_tools(self) -> list[dict[str, Any]]:
        """Convert JustiFi schemas to OpenAI tools format."""
        tools = []
        tool_schemas = get_tool_schemas(
            self.justifi_toolkit
        )  # Get schemas from toolkit instance
        for tool_name in self.justifi_toolkit.get_enabled_tools():
            if tool_name in tool_schemas:
                schema = tool_schemas[tool_name]
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "description": schema["description"],
                            "parameters": schema.get(
                                "parameters", {"type": "object", "properties": {}}
                            ),
                        },
                    }
                )
        return tools

    async def analyze_payout_trends(self, user_query: str) -> str:
        """Perform advanced payout trend analysis based on user query."""

        system_prompt = """You are a financial analysis assistant specializing in payout data analysis.

        You have access to JustiFi payout tools to:
        - List payouts with pagination
        - Get detailed payout information
        - Check payout statuses
        - Retrieve recent payouts

        When analyzing payouts:
        1. Always start with recent payouts to understand current state
        2. Look for patterns in amounts, timing, and status
        3. Identify any failed or pending payouts that need attention
        4. Provide actionable insights and recommendations

        Be thorough but concise in your analysis."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]

        # Initial conversation turn
        response = await self.openai_client.chat.completions.create(
            model="gpt-4", messages=messages, tools=self.tools, tool_choice="auto"
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump())

        # Handle tool calls iteratively
        max_iterations = 5
        iteration = 0

        while assistant_message.tool_calls and iteration < max_iterations:
            print(f"🔄 Analysis iteration {iteration + 1}")

            # Execute all tool calls in parallel for efficiency
            tool_results = await self._execute_tool_calls_parallel(
                assistant_message.tool_calls
            )

            # Add all tool results to conversation
            for tool_call, result in zip(
                assistant_message.tool_calls, tool_results, strict=False
            ):
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, indent=2, default=str),
                    }
                )

            # Get next response
            response = await self.openai_client.chat.completions.create(
                model="gpt-4", messages=messages, tools=self.tools, tool_choice="auto"
            )

            assistant_message = response.choices[0].message
            messages.append(assistant_message.model_dump())
            iteration += 1

        return assistant_message.content or "Analysis completed"

    async def _execute_tool_calls_parallel(self, tool_calls) -> list[Any]:
        """Execute multiple tool calls in parallel for better performance."""
        tasks = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            print(f"  📞 Queuing: {function_name}({arguments})")

            # Create async task for each tool call
            task = self._execute_single_tool(function_name, arguments)
            tasks.append(task)

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  ❌ Tool {i} failed: {result}")
                processed_results.append({"error": str(result)})
            else:
                print(f"  ✅ Tool {i} succeeded")
                processed_results.append(result)

        return processed_results

    async def _execute_single_tool(
        self, function_name: str, arguments: dict[str, Any]
    ) -> Any:
        """Execute a single tool with error handling."""
        try:
            result = await self.justifi_toolkit.call_tool(function_name, arguments)
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {e}"}

    async def streaming_analysis(self, user_query: str):
        """Demonstrate streaming responses with tool calls."""
        print("🌊 Starting streaming analysis...\n")

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that analyzes payout data. Provide your analysis step by step.",
            },
            {"role": "user", "content": user_query},
        ]

        # Create streaming response
        stream = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            stream=True,
        )

        print("📝 Streaming response:")
        collected_content = ""

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                collected_content += content

        print("\n\n✅ Streaming complete!")
        return collected_content


async def demonstrate_advanced_workflows():
    """Demonstrate various advanced workflow patterns."""
    print("🚀 OpenAI Advanced Workflows Demo\n")

    assistant = PayoutAnalysisAssistant()

    # Example 1: Comprehensive payout analysis
    print("=" * 60)
    print("📊 Example 1: Comprehensive Payout Analysis")
    print("=" * 60)

    analysis_query = """
    I need a comprehensive analysis of our recent payout performance. Please:
    1. Get our recent payouts and analyze the trends
    2. Check for any failed or pending payouts
    3. Calculate total payout amounts and frequency
    4. Identify any patterns or anomalies
    5. Provide recommendations for optimization
    """

    try:
        result = await assistant.analyze_payout_trends(analysis_query)
        print(f"📋 Analysis Result:\n{result}\n")
    except Exception as e:
        print(f"❌ Analysis failed: {e}\n")

    # Example 2: Streaming analysis
    print("=" * 60)
    print("🌊 Example 2: Streaming Analysis")
    print("=" * 60)

    streaming_query = "Give me a quick overview of our recent payouts and their status"

    try:
        await assistant.streaming_analysis(streaming_query)
    except Exception as e:
        print(f"❌ Streaming analysis failed: {e}")

    # Example 3: Error handling demonstration
    print("\n" + "=" * 60)
    print("🛡️ Example 3: Error Handling")
    print("=" * 60)

    # Create a toolkit with invalid credentials to demonstrate error handling
    try:
        invalid_toolkit = JustiFiToolkit(
            client_id="invalid_id",
            client_secret="invalid_secret",
            enabled_tools=["list_payouts"],
        )

        # This should fail gracefully
        result = await invalid_toolkit.call_tool("list_payouts", {"limit": 5})
        print(f"Unexpected success: {result}")

    except Exception as e:
        print(f"✅ Error handled gracefully: {e}")

    print("\n✅ Advanced workflows demonstration complete!")


async def demonstrate_custom_orchestration():
    """Show custom function orchestration patterns."""
    print("\n🎭 Custom Function Orchestration Demo\n")

    # This shows how developers can build custom workflows
    # by orchestrating multiple JustiFi tools programmatically

    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["list_payouts", "retrieve_payout", "get_payout_status"],
    )

    print("🔧 Custom Workflow: Detailed Payout Health Check")

    try:
        print("  1️⃣ Fetching recent payouts...")
        recent_payouts = await toolkit.call_tool("get_recent_payouts", {"limit": 10})

        if recent_payouts and "data" in recent_payouts:
            payouts = recent_payouts["data"]
            print(f"     Found {len(payouts)} recent payouts")

            print("  2️⃣ Checking individual payout statuses...")

            for i, payout in enumerate(payouts[:3]):  # Check first 3
                payout_id = payout.get("id")
                if payout_id:
                    status_result = await toolkit.call_tool(
                        "get_payout_status", {"payout_id": payout_id}
                    )
                    status = (
                        status_result.get("status", "unknown")
                        if status_result
                        else "unknown"
                    )
                    amount = payout.get("amount", 0)
                    print(
                        f"     Payout {i + 1}: {payout_id} - Status: {status} - Amount: ${amount / 100:.2f}"
                    )

            print("  ✅ Health check complete!")

        else:
            print("     No payouts found")

    except Exception as e:
        print(f"  ❌ Health check failed: {e}")


if __name__ == "__main__":

    async def main():
        await demonstrate_advanced_workflows()
        await demonstrate_custom_orchestration()

        print("\n🎯 Key Advanced Patterns Demonstrated:")
        print("   • Multi-step AI-driven analysis workflows")
        print("   • Parallel tool execution for performance")
        print("   • Streaming responses with tool integration")
        print("   • Robust error handling and recovery")
        print("   • Custom programmatic tool orchestration")
        print("   • Iterative AI analysis with tool feedback")

    asyncio.run(main())
