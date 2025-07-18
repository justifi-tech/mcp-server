#!/usr/bin/env python3

"""
LangChain Agent Workflows Example for JustiFi MCP Server

This example demonstrates advanced LangChain agent patterns including:
- ReAct agents for step-by-step reasoning
- Plan-and-execute agents for complex workflows
- Custom agent types with specialized prompts
- Multi-agent conversations
- Agent memory and state management

Requirements:
    uv pip install langchain langchain-openai langchain-community langchain-experimental

Environment Variables:
    JUSTIFI_CLIENT_ID - Your JustiFi API client ID
    JUSTIFI_CLIENT_SECRET - Your JustiFi API client secret
    OPENAI_API_KEY - Your OpenAI API key
"""

import asyncio
import os
from typing import Any

from langchain.agents import (
    AgentExecutor,
    create_openai_tools_agent,
    create_react_agent,
)
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI

from python import JustiFiToolkit


class PayoutAnalysisAgent:
    """Specialized agent for payout analysis with memory."""

    def __init__(self):
        self.toolkit = JustiFiToolkit(
            client_id=os.getenv("JUSTIFI_CLIENT_ID"),
            client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
            enabled_tools=[
                "list_payouts",
                "retrieve_payout",
                "get_payout_status",
                "get_recent_payouts",
            ],
        )

        self.llm = ChatOpenAI(
            model="gpt-4", temperature=0.1, openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        self.tools = self.toolkit.get_langchain_tools()

        # Add memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            output_key="output",
            return_messages=True,
            k=10,  # Remember last 10 exchanges
        )

        self._setup_agent()

    def _setup_agent(self):
        """Setup the specialized payout analysis agent."""

        # Create specialized prompt for payout analysis
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a specialized financial analyst focusing on payout data analysis.

Your expertise includes:
- Payout trend analysis and pattern recognition
- Risk assessment for payment operations
- Performance optimization recommendations
- Anomaly detection in payout data

Available JustiFi tools:
{tools}

Tool descriptions:
{tool_names}

When analyzing payouts:
1. Always start with recent data to understand current state
2. Look for patterns in amounts, timing, frequency, and status
3. Identify any failed, pending, or delayed payouts
4. Calculate key metrics (total amounts, success rates, average times)
5. Provide actionable insights and recommendations
6. Consider business impact of any issues found

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Previous conversation:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}""",
                ),
            ]
        )

        # Create ReAct agent for step-by-step reasoning
        self.agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=prompt)

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=8,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

    async def analyze(self, query: str) -> dict[str, Any]:
        """Perform payout analysis with memory."""
        try:
            result = await self.agent_executor.ainvoke({"input": query})
            return {
                "success": True,
                "output": result["output"],
                "intermediate_steps": result.get("intermediate_steps", []),
                "memory": self.memory.buffer_as_messages,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "memory": self.memory.buffer_as_messages,
            }


class PayoutReportingAgent:
    """Specialized agent for generating payout reports."""

    def __init__(self):
        self.toolkit = JustiFiToolkit(
            client_id=os.getenv("JUSTIFI_CLIENT_ID"),
            client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
            enabled_tools=[
                "list_payouts",
                "retrieve_payout",
                "get_payout_status",
                "get_recent_payouts",
            ],
        )

        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.0,  # More deterministic for reports
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        self.tools = self.toolkit.get_langchain_tools()
        self._setup_agent()

    def _setup_agent(self):
        """Setup the reporting agent with structured output."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a financial reporting specialist that creates comprehensive payout reports.

Your reports should include:
- Executive summary with key findings
- Detailed data analysis with specific numbers
- Risk assessment and recommendations
- Trends and patterns identified
- Action items for stakeholders

Format your reports in a clear, professional structure with:
1. Executive Summary
2. Key Metrics
3. Detailed Analysis
4. Risk Assessment
5. Recommendations
6. Next Steps

Always provide specific data points, percentages, and monetary amounts when available.
Be thorough but concise, focusing on actionable insights.""",
                ),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.agent = create_openai_tools_agent(
            llm=self.llm, tools=self.tools, prompt=prompt
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=6,
            handle_parsing_errors=True,
        )

    async def generate_report(
        self, report_type: str, parameters: dict[str, Any] = None
    ) -> str:
        """Generate a specific type of payout report."""

        report_prompts = {
            "weekly": "Generate a comprehensive weekly payout report including trends, totals, and any issues that need attention.",
            "status": "Create a payout status report showing the current state of all recent payouts, highlighting any failed or pending items.",
            "performance": "Analyze payout performance metrics including success rates, timing, and efficiency recommendations.",
            "risk": "Conduct a risk assessment of recent payout activities, identifying potential issues and mitigation strategies.",
        }

        prompt = report_prompts.get(
            report_type, f"Generate a {report_type} report for our payout data."
        )

        if parameters:
            prompt += f" Use these parameters: {parameters}"

        try:
            result = await self.agent_executor.ainvoke({"input": prompt})
            return result["output"]
        except Exception as e:
            return f"Report generation failed: {e}"


async def demonstrate_react_agent():
    """Demonstrate ReAct agent for step-by-step reasoning."""
    print("🧠 ReAct Agent Demo\n")

    agent = PayoutAnalysisAgent()

    # Example analysis with step-by-step reasoning
    query = """I need to understand our payout performance this week.
    Can you analyze our recent payouts and tell me:
    1. How many payouts we've processed
    2. What's our success rate
    3. Are there any concerning patterns
    4. What should I focus on?"""

    print(f"📋 Analysis Query: {query}\n")
    print("🔄 Agent is thinking step by step...\n")

    result = await agent.analyze(query)

    if result["success"]:
        print("✅ Analysis Complete!")
        print(f"📊 Final Answer:\n{result['output']}\n")

        if result["intermediate_steps"]:
            print("🔍 Reasoning Steps:")
            for i, (action, observation) in enumerate(result["intermediate_steps"], 1):
                print(f"  Step {i}: {action.tool} -> {str(observation)[:100]}...")
    else:
        print(f"❌ Analysis failed: {result['error']}")


async def demonstrate_conversation_memory():
    """Demonstrate agent memory across multiple interactions."""
    print("\n💭 Conversation Memory Demo\n")

    agent = PayoutAnalysisAgent()

    # First interaction
    print("🗣️ First question:")
    result1 = await agent.analyze("What's the status of our recent payouts?")
    if result1["success"]:
        print(f"🤖 Response: {result1['output'][:200]}...\n")

    # Follow-up question that relies on memory
    print("🗣️ Follow-up question:")
    result2 = await agent.analyze(
        "Based on what you just found, what should be our top priority?"
    )
    if result2["success"]:
        print(f"🤖 Response: {result2['output'][:200]}...\n")

    # Show memory contents
    print("🧠 Agent Memory:")
    memory_messages = agent.memory.buffer_as_messages
    for msg in memory_messages[-4:]:  # Show last 4 messages
        role = "Human" if isinstance(msg, HumanMessage) else "AI"
        print(f"  {role}: {str(msg.content)[:100]}...")


async def demonstrate_specialized_reporting():
    """Demonstrate specialized reporting agent."""
    print("\n📊 Specialized Reporting Agent Demo\n")

    reporting_agent = PayoutReportingAgent()

    # Generate different types of reports
    report_types = [
        ("status", "Current payout status overview"),
        ("performance", "Performance metrics analysis"),
    ]

    for report_type, description in report_types:
        print(f"📋 Generating {description}...")

        report = await reporting_agent.generate_report(report_type)

        print(f"📄 {report_type.title()} Report:")
        print(f"{report[:300]}...\n")


async def demonstrate_multi_agent_workflow():
    """Demonstrate coordination between multiple specialized agents."""
    print("\n👥 Multi-Agent Workflow Demo\n")

    analysis_agent = PayoutAnalysisAgent()
    reporting_agent = PayoutReportingAgent()

    print("🔄 Step 1: Analysis agent investigates recent payouts")
    analysis_result = await analysis_agent.analyze(
        "Analyze our recent payouts and identify the most critical issues that need immediate attention."
    )

    if analysis_result["success"]:
        print(f"📊 Analysis: {analysis_result['output'][:200]}...\n")

        print("🔄 Step 2: Reporting agent creates action plan based on analysis")

        # Pass analysis results to reporting agent
        f"""Based on this analysis: {analysis_result["output"][:500]}

        Create an executive summary report with:
        1. Key findings summary
        2. Immediate action items
        3. Risk mitigation steps
        4. Timeline for resolution"""

        report = await reporting_agent.generate_report(
            "executive", {"analysis": analysis_result["output"]}
        )

        print(f"📄 Executive Report:\n{report[:400]}...\n")

        print("✅ Multi-agent workflow completed!")
    else:
        print(f"❌ Analysis failed: {analysis_result['error']}")


async def demonstrate_custom_tool_integration():
    """Demonstrate creating custom tools alongside JustiFi tools."""
    print("\n🔧 Custom Tool Integration Demo\n")

    # Create a custom calculation tool
    def calculate_payout_metrics(data: str) -> str:
        """Calculate key payout metrics from payout data."""
        try:
            import json

            payouts = json.loads(data)

            if "data" in payouts:
                payout_list = payouts["data"]
                total_amount = sum(p.get("amount", 0) for p in payout_list)
                count = len(payout_list)
                avg_amount = total_amount / count if count > 0 else 0

                return json.dumps(
                    {
                        "total_payouts": count,
                        "total_amount_cents": total_amount,
                        "average_amount_cents": avg_amount,
                        "total_amount_usd": total_amount / 100,
                        "average_amount_usd": avg_amount / 100,
                    }
                )
            else:
                return "No payout data found"
        except Exception as e:
            return f"Calculation error: {e}"

    # Create custom LangChain tool
    metrics_tool = Tool(
        name="calculate_payout_metrics",
        description="Calculate key metrics (totals, averages) from payout data in JSON format",
        func=calculate_payout_metrics,
    )

    # Get JustiFi tools and add custom tool
    toolkit = JustiFiToolkit(
        client_id=os.getenv("JUSTIFI_CLIENT_ID"),
        client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
        enabled_tools=["list_payouts", "get_recent_payouts"],
    )

    justifi_tools = toolkit.get_langchain_tools()
    all_tools = justifi_tools + [metrics_tool]

    # Create agent with both JustiFi and custom tools
    llm = ChatOpenAI(model="gpt-4", temperature=0.1)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a financial analyst with access to payout data and calculation tools.

        When asked for metrics:
        1. First get the payout data using JustiFi tools
        2. Then use the calculate_payout_metrics tool to compute statistics
        3. Present the results in a clear, business-friendly format""",
            ),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_openai_tools_agent(llm, all_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)

    # Test the combined workflow
    result = await agent_executor.ainvoke(
        {
            "input": "Get our recent payouts and calculate key metrics like total amounts and averages"
        }
    )

    print(f"📊 Combined Analysis Result:\n{result['output']}")


if __name__ == "__main__":

    async def main():
        await demonstrate_react_agent()
        await demonstrate_conversation_memory()
        await demonstrate_specialized_reporting()
        await demonstrate_multi_agent_workflow()
        await demonstrate_custom_tool_integration()

        print("\n🎯 Advanced LangChain Patterns Demonstrated:")
        print("   • ReAct agents for step-by-step reasoning")
        print("   • Conversation memory and context retention")
        print("   • Specialized agents for different tasks")
        print("   • Multi-agent workflow coordination")
        print("   • Custom tool integration with JustiFi tools")
        print("   • Professional report generation")
        print("   • Error handling and recovery strategies")

    asyncio.run(main())
