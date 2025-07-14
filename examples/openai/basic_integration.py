#!/usr/bin/env python3

"""
OpenAI Basic Integration Example for JustiFi MCP Server

This example demonstrates how to use JustiFi tools directly with OpenAI's
function calling feature, without needing a dedicated adapter.

Our tool schemas are already OpenAI-compatible JSON schemas!

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

import openai
from justifi_mcp import JustiFiToolkit
from justifi_mcp.tools import TOOL_SCHEMAS


async def demonstrate_openai_basic_integration():
    """Demonstrate basic OpenAI integration with JustiFi tools."""
    print("🤖 OpenAI Basic Integration Demo\n")

    # Initialize OpenAI client
    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Initialize JustiFi toolkit with payout tools
    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["list_payouts", "retrieve_payout", "get_payout_status"],
    )

    # Convert our schemas to OpenAI function format
    openai_functions = []
    for tool_name in ["list_payouts", "retrieve_payout", "get_payout_status"]:
        schema = TOOL_SCHEMAS[tool_name]
        openai_functions.append(
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

    print("📋 Available OpenAI Functions:")
    for func in openai_functions:
        print(f"  • {func['function']['name']}: {func['function']['description']}")
    print()

    # Example conversation
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can check payout information using JustiFi tools.",
        },
        {
            "role": "user",
            "content": "Can you show me the recent payouts and check the status of the first one?",
        },
    ]

    try:
        # Make initial request
        response = await client.chat.completions.create(
            model="gpt-4", messages=messages, tools=openai_functions, tool_choice="auto"
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump())

        # Handle function calls
        if assistant_message.tool_calls:
            print("🔧 AI is calling JustiFi tools...")

            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                print(f"  📞 Calling: {function_name}({arguments})")

                try:
                    # Execute the tool
                    result = await toolkit.call_tool(function_name, arguments)

                    # Add function result to conversation
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, indent=2),
                        }
                    )

                    print(f"  ✅ Result: {len(json.dumps(result))} characters")

                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error: {e}",
                        }
                    )

            # Get final response with function results
            final_response = await client.chat.completions.create(
                model="gpt-4", messages=messages
            )

            print(f"\n🤖 AI Response:\n{final_response.choices[0].message.content}")

        else:
            print(f"🤖 AI Response: {assistant_message.content}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n✅ OpenAI basic integration demo complete!")


if __name__ == "__main__":
    asyncio.run(demonstrate_openai_basic_integration())
