#!/usr/bin/env python3
"""
JustiFi MCP Agent Example - v1.0.23 Standardized Response Format

This example demonstrates how to properly handle the standardized response format
introduced in justifi-mcp-server v1.0.23. All tools now return responses with
a consistent "data" field structure.

Key Features:
- Proper handling of standardized response format
- Template-based response generation for different data types
- Support for payouts, payments, transactions, and other data types
- Error handling and fallback responses

Requirements:
    uv pip install langchain langchain-openai
    
Environment Variables:
    JUSTIFI_CLIENT_ID - Your JustiFi API client ID
    JUSTIFI_CLIENT_SECRET - Your JustiFi API client secret
    OPENAI_API_KEY - Your OpenAI API key
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from python import JustiFiToolkit


class JustiFiMCPAgent:
    """
    JustiFi MCP Agent with v1.0.23 standardized response handling.
    
    This agent properly handles the standardized response format where all
    tools return data in the "data" field, eliminating the need for tool-specific
    response parsing.
    """

    def __init__(self):
        """Initialize the agent with proper response format handling."""
        self.toolkit = JustiFiToolkit(
            client_id=os.getenv("JUSTIFI_CLIENT_ID"),
            client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        )
        
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.tools = self.toolkit.get_langchain_tools()
        self._setup_agent()

    def _setup_agent(self):
        """Setup the agent with standardized response format handling."""
        
        # System prompt with detailed formatting templates
        system_prompt = """You are a financial assistant specializing in JustiFi payment operations.

All JustiFi tools now return standardized responses in v1.0.23 format:
{
  "data": [...],           // Always contains the actual records
  "metadata": {
    "type": "payouts",     // Data type indicator  
    "count": 5,            // Number of records
    "tool": "list_payouts", // Source tool name
    "original_format": "api" // Original response format
  },
  "page_info": {...}       // Pagination info if applicable
}

IMPORTANT RESPONSE FORMATTING RULES:

For PAYOUT requests, format responses like this:
📊 **Payout Summary**
- **Total Payouts**: {count}
- **Combined Amount**: ${total_amount}
- **Status Breakdown**: {status_counts}

**Recent Payouts:**
{detailed_payout_list}

For PAYMENT requests, format responses like this:
💳 **Payment Summary** 
- **Total Payments**: {count}
- **Combined Amount**: ${total_amount}
- **Status Breakdown**: {status_counts}

**Recent Payments:**
{detailed_payment_list}

For TRANSACTION requests, format responses like this:
📈 **Transaction Summary**
- **Total Transactions**: {count}
- **Combined Amount**: ${total_amount}
- **Type Breakdown**: {type_counts}

**Recent Transactions:**
{detailed_transaction_list}

For DISPUTE/REFUND requests, provide appropriate summaries with:
- Total count and amounts
- Status breakdowns  
- Detailed item lists

RESPONSE PROCESSING:
1. Always extract data from response["data"] field
2. Use metadata["type"] to determine data type
3. Calculate totals, averages, and status breakdowns
4. Format using appropriate template above
5. Provide actionable insights and recommendations

Never return generic messages like "I've retrieved your payment information."
Always show actual data, amounts, statuses, and specific details."""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools, 
            prompt=prompt
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )

    async def process_request(self, user_input: str) -> str:
        """
        Process user request and return formatted response.
        
        This method demonstrates proper handling of standardized responses
        from JustiFi MCP tools v1.0.23.
        """
        try:
            result = await self.agent_executor.ainvoke({"input": user_input})
            return result["output"]
        except Exception as e:
            return f"❌ Error processing request: {str(e)}"

    def format_standardized_response(self, response: Dict[str, Any]) -> str:
        """
        Format standardized response based on data type.
        
        This demonstrates how to properly extract and format data from
        the v1.0.23 standardized response format.
        """
        if not isinstance(response, dict) or "data" not in response:
            return "⚠️ Invalid response format received"

        data = response["data"]
        metadata = response.get("metadata", {})
        data_type = metadata.get("type", "unknown")
        count = metadata.get("count", len(data) if isinstance(data, list) else 0)
        
        if data_type == "payouts":
            return self._format_payout_response(data, count, metadata)
        elif data_type == "payments": 
            return self._format_payment_response(data, count, metadata)
        elif data_type == "balance_transactions":
            return self._format_transaction_response(data, count, metadata)
        elif data_type in ["disputes", "refunds", "checkouts"]:
            return self._format_generic_response(data, count, metadata, data_type)
        else:
            return self._format_unknown_response(data, count, metadata)

    def _format_payout_response(self, data: List[Dict], count: int, metadata: Dict) -> str:
        """Format payout data using the standardized template."""
        if not data:
            return "📊 **Payout Summary**\nNo payouts found."

        total_amount = sum(payout.get("amount", 0) for payout in data) / 100
        status_counts = {}
        
        payout_details = []
        for payout in data:
            status = payout.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            amount = payout.get("amount", 0) / 100
            created = payout.get("created", "unknown")
            payout_id = payout.get("id", "unknown")
            
            payout_details.append(f"• ${amount:.2f} - {status} - {created} ({payout_id})")

        status_breakdown = ", ".join([f"{status}: {count}" for status, count in status_counts.items()])
        
        return f"""📊 **Payout Summary**
- **Total Payouts**: {count}
- **Combined Amount**: ${total_amount:.2f}
- **Status Breakdown**: {status_breakdown}

**Recent Payouts:**
{chr(10).join(payout_details[:10])}"""

    def _format_payment_response(self, data: List[Dict], count: int, metadata: Dict) -> str:
        """Format payment data using the standardized template."""
        if not data:
            return "💳 **Payment Summary**\nNo payments found."

        total_amount = sum(payment.get("amount", 0) for payment in data) / 100
        status_counts = {}
        
        payment_details = []
        for payment in data:
            status = payment.get("status", "unknown") 
            status_counts[status] = status_counts.get(status, 0) + 1
            
            amount = payment.get("amount", 0) / 100
            created = payment.get("created", "unknown")
            payment_id = payment.get("id", "unknown")
            
            payment_details.append(f"• ${amount:.2f} - {status} - {created} ({payment_id})")

        status_breakdown = ", ".join([f"{status}: {count}" for status, count in status_counts.items()])
        
        return f"""💳 **Payment Summary**
- **Total Payments**: {count}
- **Combined Amount**: ${total_amount:.2f}
- **Status Breakdown**: {status_breakdown}

**Recent Payments:**
{chr(10).join(payment_details[:10])}"""

    def _format_transaction_response(self, data: List[Dict], count: int, metadata: Dict) -> str:
        """Format transaction data using the standardized template.""" 
        if not data:
            return "📈 **Transaction Summary**\nNo transactions found."

        total_amount = sum(abs(tx.get("amount", 0)) for tx in data) / 100
        type_counts = {}
        
        transaction_details = []
        for tx in data:
            tx_type = tx.get("type", "unknown")
            type_counts[tx_type] = type_counts.get(tx_type, 0) + 1
            
            amount = tx.get("amount", 0) / 100
            created = tx.get("created", "unknown")  
            tx_id = tx.get("id", "unknown")
            
            transaction_details.append(f"• ${amount:.2f} - {tx_type} - {created} ({tx_id})")

        type_breakdown = ", ".join([f"{tx_type}: {count}" for tx_type, count in type_counts.items()])
        
        return f"""📈 **Transaction Summary**
- **Total Transactions**: {count}
- **Combined Amount**: ${total_amount:.2f}
- **Type Breakdown**: {type_breakdown}

**Recent Transactions:**
{chr(10).join(transaction_details[:10])}"""

    def _format_generic_response(self, data: List[Dict], count: int, metadata: Dict, data_type: str) -> str:
        """Format other data types with generic template."""
        if not data:
            return f"📋 **{data_type.title()} Summary**\nNo {data_type} found."

        details = []
        for item in data:
            item_id = item.get("id", "unknown")
            status = item.get("status", "N/A")
            amount = item.get("amount", 0)
            amount_str = f"${amount/100:.2f}" if amount else "N/A"
            
            details.append(f"• {item_id} - {status} - {amount_str}")

        return f"""📋 **{data_type.title()} Summary** 
- **Total {data_type.title()}**: {count}

**Recent {data_type.title()}:**
{chr(10).join(details[:10])}"""

    def _format_unknown_response(self, data: List[Dict], count: int, metadata: Dict) -> str:
        """Format unknown data types with fallback template."""
        data_type = metadata.get("type", "items")
        
        return f"""📄 **Data Summary**
- **Total {data_type}**: {count}
- **Data Type**: {data_type}

First few items:
{str(data[:3]) if data else "No data available"}"""


async def demonstrate_standardized_responses():
    """Demonstrate proper handling of v1.0.23 standardized responses."""
    print("🚀 JustiFi MCP Agent - v1.0.23 Standardized Response Demo\n")
    
    agent = JustiFiMCPAgent()
    
    # Test scenarios that should return properly formatted responses
    test_scenarios = [
        "Tell me about my last 5 payouts with details",
        "Show me recent payments and their status", 
        "Get my balance transactions for analysis",
        "List any recent disputes or issues",
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"📋 Test {i}: {scenario}")
        print("=" * 50)
        
        response = await agent.process_request(scenario)
        print(response)
        print("\n" + "=" * 50 + "\n")

async def demonstrate_direct_response_formatting():
    """Demonstrate direct formatting of standardized responses.""" 
    print("🔧 Direct Response Formatting Demo\n")
    
    agent = JustiFiMCPAgent()
    
    # Example standardized response from v1.0.23
    example_payout_response = {
        "data": [
            {
                "id": "po_123456",
                "amount": 150000,  # $1,500.00
                "status": "completed", 
                "created": "2025-08-07T12:00:00Z"
            },
            {
                "id": "po_789012",
                "amount": 250000,  # $2,500.00
                "status": "pending",
                "created": "2025-08-07T10:30:00Z"
            }
        ],
        "metadata": {
            "type": "payouts",
            "count": 2,
            "tool": "get_recent_payouts", 
            "original_format": "custom"
        }
    }
    
    formatted = agent.format_standardized_response(example_payout_response)
    print("📊 Formatted Payout Response:")
    print(formatted)
    
    # Example payment response  
    example_payment_response = {
        "data": [
            {
                "id": "py_abcdef",
                "amount": 99999,  # $999.99
                "status": "succeeded",
                "created": "2025-08-07T14:15:00Z"
            }
        ],
        "metadata": {
            "type": "payments", 
            "count": 1,
            "tool": "list_payments",
            "original_format": "api"
        }
    }
    
    formatted = agent.format_standardized_response(example_payment_response)
    print("\n💳 Formatted Payment Response:")
    print(formatted)


if __name__ == "__main__":
    async def main():
        print("🎯 JustiFi MCP Agent - v1.0.23 Standardized Response Format")
        print("=" * 60)
        print("This example demonstrates proper handling of the standardized")
        print("response format introduced in justifi-mcp-server v1.0.23.\n")
        
        # Check for required environment variables
        required_vars = ["JUSTIFI_CLIENT_ID", "JUSTIFI_CLIENT_SECRET", "OPENAI_API_KEY"] 
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("Please set these variables and try again.\n")
            return
            
        await demonstrate_direct_response_formatting()
        print("\n" + "=" * 60 + "\n")
        await demonstrate_standardized_responses()
        
        print("✅ Demo completed successfully!")
        print("\n🎯 Key Benefits of v1.0.23 Standardized Responses:")
        print("   • Consistent 'data' field across all tools")
        print("   • Eliminates tool-specific response parsing")
        print("   • Reliable data extraction and formatting")
        print("   • Better error handling and fallbacks")
        print("   • Improved agent response quality")

    asyncio.run(main())