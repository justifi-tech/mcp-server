#!/usr/bin/env python3

"""
OpenAI Direct Integration Example for JustiFi MCP Server

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


async def demonstrate_openai_direct_integration():
    """Demonstrate direct OpenAI integration without an adapter."""
    print("🤖 OpenAI Direct Integration Demo\n")

    # Initialize JustiFi toolkit
    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["retrieve_payout", "list_payouts", "get_payout_status"],
    )

    # Get enabled tool schemas - they're already OpenAI-compatible!
    enabled_tools = toolkit.get_enabled_tools()
    openai_functions = []

    for tool_name in enabled_tools:
        if tool_name in TOOL_SCHEMAS:
            schema = TOOL_SCHEMAS[tool_name]
            # Our schemas are already in OpenAI format!
            openai_functions.append(
                {
                    "name": schema["name"],
                    "description": schema["description"],
                    "parameters": schema["parameters"],
                }
            )

    print(f"✅ Created {len(openai_functions)} OpenAI function definitions")
    for func in openai_functions:
        print(f"   - {func['name']}: {func['description']}")

    print()

    # Initialize OpenAI client
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Skipping AI model demonstration.")
        return

    client = openai.OpenAI()

    # Example conversation with function calling
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can retrieve payout information using JustiFi tools.",
        },
        {"role": "user", "content": "Can you get the status of payout po_test123?"},
    ]

    print("🔄 Making OpenAI API call with function definitions...")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            functions=openai_functions,
            function_call="auto",
        )

        message = response.choices[0].message

        if message.function_call:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)

            print(f"🎯 OpenAI wants to call: {function_name}")
            print(f"📋 With arguments: {function_args}")

            # Execute the function using our toolkit
            result = await toolkit.call_tool(function_name, function_args)

            print("✅ Function executed successfully!")
            print("📊 Result format: MCP TextContent (can be parsed for OpenAI)")

            # Extract the JSON from MCP result for OpenAI
            if result and len(result) > 0:
                result_text = result[0].text
                # Find the JSON part (after "✅ Success: tool_name\n\n")
                json_start = result_text.find("{")
                if json_start != -1:
                    json_result = result_text[json_start:]
                    print(f"📄 Parsed result: {json_result[:200]}...")

        else:
            print("💬 OpenAI response (no function call):")
            print(message.content)

    except Exception as e:
        print(f"❌ OpenAI API error: {e}")


async def demonstrate_tool_schema_compatibility():
    """Show that our tool schemas are OpenAI-compatible."""
    print("🔍 Tool Schema Compatibility Demo\n")

    print("Our TOOL_SCHEMAS are already OpenAI function calling compatible:")
    print("=" * 60)

    for tool_name, schema in TOOL_SCHEMAS.items():
        print(f"\n🛠️  {tool_name}:")
        print(f"   Name: {schema['name']}")
        print(f"   Description: {schema['description']}")
        print(f"   Parameters: {json.dumps(schema['parameters'], indent=6)}")

    print("\n" + "=" * 60)
    print("✅ No adapter needed - direct compatibility!")


async def demonstrate_custom_integration():
    """Show how developers can build custom OpenAI integrations."""
    print("\n🔧 Custom Integration Pattern\n")

    # This is how a developer would integrate JustiFi with their OpenAI app
    code_example = """
# Custom OpenAI + JustiFi Integration
import openai
from justifi_mcp import JustiFiToolkit, TOOL_SCHEMAS

class PaymentAssistant:
    def __init__(self, justifi_client_id, justifi_secret, openai_key):
        self.toolkit = JustiFiToolkit(
            client_id=justifi_client_id, 
            client_secret=justifi_secret
        )
        self.openai_client = openai.OpenAI(api_key=openai_key)
        
        # Get function definitions from our schemas
        self.functions = [
            {
                "name": schema["name"],
                "description": schema["description"], 
                "parameters": schema["parameters"]
            }
            for schema in TOOL_SCHEMAS.values()
        ]
    
    async def chat_with_payments(self, user_message):
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}],
            functions=self.functions,
            function_call="auto"
        )
        
        if response.choices[0].message.function_call:
            # Execute JustiFi tool
            func_name = response.choices[0].message.function_call.name
            func_args = json.loads(response.choices[0].message.function_call.arguments)
            result = await self.toolkit.call_tool(func_name, func_args)
            return result
        
        return response.choices[0].message.content
"""

    print("💡 Custom Integration Pattern:")
    print(code_example)


async def main():
    """Run all demonstrations."""
    print("🎉 JustiFi + OpenAI Direct Integration Examples\n")
    print("=" * 60)

    await demonstrate_tool_schema_compatibility()
    await demonstrate_openai_direct_integration()
    await demonstrate_custom_integration()

    print("=" * 60)
    print("✅ All demonstrations completed!")
    print("\n📚 Key benefits of direct integration:")
    print("   • No adapter needed - our schemas are already OpenAI-compatible")
    print("   • Simpler codebase - less complexity to maintain")
    print("   • Direct tool access - maximum flexibility")
    print("   • Standard OpenAI patterns - familiar to developers")
    print("   • Lightweight integration - minimal overhead")


if __name__ == "__main__":
    asyncio.run(main())
