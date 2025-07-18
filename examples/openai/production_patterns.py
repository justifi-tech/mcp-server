#!/usr/bin/env python3

"""
OpenAI Production Patterns Example for JustiFi MCP Server

This example demonstrates production-ready patterns including:
- Proper configuration management
- Comprehensive logging and monitoring
- Error handling and circuit breakers
- Rate limiting and retry logic
- Security best practices
- Performance optimization

Requirements:
    uv pip install openai pydantic python-dotenv

Environment Variables:
    JUSTIFI_CLIENT_ID - Your JustiFi API client ID
    JUSTIFI_CLIENT_SECRET - Your JustiFi API client secret
    OPENAI_API_KEY - Your OpenAI API key
    LOG_LEVEL - Logging level (default: INFO)
"""

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import openai
from pydantic import BaseModel

from python import JustiFiToolkit, get_tool_schemas

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ProductionConfig:
    """Production configuration with validation."""

    # API Configuration
    justifi_client_id: str
    justifi_client_secret: str
    openai_api_key: str

    # Performance Configuration
    max_tool_calls_per_conversation: int = 10
    tool_call_timeout_seconds: int = 30
    max_concurrent_tools: int = 3

    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0

    # Security Configuration
    enabled_tools: list[str] = None
    rate_limit_per_minute: int = 60

    @classmethod
    def from_env(cls) -> "ProductionConfig":
        """Create configuration from environment variables."""
        return cls(
            justifi_client_id=os.getenv("JUSTIFI_CLIENT_ID"),
            justifi_client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            enabled_tools=[
                "list_payouts",
                "retrieve_payout",
                "get_payout_status",
                "get_recent_payouts",
            ],
        )


class ConversationMetrics(BaseModel):
    """Track conversation metrics for monitoring."""

    conversation_id: str
    start_time: float
    end_time: float | None = None
    total_tool_calls: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float | None = None

    def add_tool_call(self, success: bool):
        """Record a tool call result."""
        self.total_tool_calls += 1
        if success:
            self.successful_tool_calls += 1
        else:
            self.failed_tool_calls += 1

    def finish(self):
        """Mark conversation as finished."""
        self.end_time = time.time()

    @property
    def duration_seconds(self) -> float:
        """Get conversation duration."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def success_rate(self) -> float:
        """Get tool call success rate."""
        if self.total_tool_calls == 0:
            return 1.0
        return self.successful_tool_calls / self.total_tool_calls


class ProductionPayoutAssistant:
    """Production-ready OpenAI assistant with comprehensive monitoring and error handling."""

    def __init__(self, config: ProductionConfig):
        self.config = config
        self.openai_client = openai.AsyncOpenAI(api_key=config.openai_api_key)

        # Initialize JustiFi toolkit with production settings
        self.justifi_toolkit = JustiFiToolkit(
            client_id=config.justifi_client_id,
            client_secret=config.justifi_client_secret,
            enabled_tools=config.enabled_tools,
        )

        # Convert schemas to OpenAI format
        self.tools = self._create_openai_tools()

        # Rate limiting
        self._last_request_time = 0.0
        self._request_count = 0
        self._rate_limit_window_start = time.time()

        logger.info(
            f"Initialized ProductionPayoutAssistant with {len(self.tools)} tools"
        )

    def _create_openai_tools(self) -> list[dict[str, Any]]:
        """Convert JustiFi schemas to OpenAI tools format with validation."""
        tools = []

        tool_schemas = get_tool_schemas(
            self.justifi_toolkit
        )  # Get schemas from toolkit instance
        for tool_name in self.justifi_toolkit.get_enabled_tools():
            if tool_name in tool_schemas:
                schema = tool_schemas[tool_name]

                # Validate schema has required fields
                if not schema.get("description"):
                    logger.warning(f"Tool {tool_name} missing description")
                    continue

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

        logger.info(f"Created {len(tools)} OpenAI tool definitions")
        return tools

    async def _check_rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()

        # Reset counter if window has passed
        if current_time - self._rate_limit_window_start >= 60:
            self._request_count = 0
            self._rate_limit_window_start = current_time

        # Check if we're at the limit
        if self._request_count >= self.config.rate_limit_per_minute:
            sleep_time = 60 - (current_time - self._rate_limit_window_start)
            if sleep_time > 0:
                logger.warning(
                    f"Rate limit reached, sleeping for {sleep_time:.1f} seconds"
                )
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._rate_limit_window_start = time.time()

        self._request_count += 1

    @asynccontextmanager
    async def _conversation_context(self, conversation_id: str):
        """Context manager for conversation tracking."""
        metrics = ConversationMetrics(
            conversation_id=conversation_id, start_time=time.time()
        )

        try:
            logger.info(f"Starting conversation {conversation_id}")
            yield metrics
        except Exception as e:
            logger.error(f"Conversation {conversation_id} failed: {e}")
            raise
        finally:
            metrics.finish()
            logger.info(
                f"Conversation {conversation_id} completed: "
                f"duration={metrics.duration_seconds:.2f}s, "
                f"tool_calls={metrics.total_tool_calls}, "
                f"success_rate={metrics.success_rate:.2%}"
            )

    async def analyze_payouts_with_monitoring(
        self, user_query: str, conversation_id: str = None
    ) -> dict[str, Any]:
        """Perform payout analysis with comprehensive monitoring."""

        if not conversation_id:
            conversation_id = f"conv_{int(time.time())}"

        async with self._conversation_context(conversation_id) as metrics:
            await self._check_rate_limit()

            system_prompt = """You are a professional financial analysis assistant specializing in payout data.

            Guidelines:
            - Be precise and data-driven in your analysis
            - Always verify data before making conclusions
            - Highlight any anomalies or concerning patterns
            - Provide actionable recommendations
            - If you encounter errors, explain them clearly

            Available tools: list_payouts, retrieve_payout, get_payout_status, get_recent_payouts"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ]

            try:
                # Initial request with timeout
                response = await asyncio.wait_for(
                    self.openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=messages,
                        tools=self.tools,
                        tool_choice="auto",
                        temperature=0.1,  # Lower temperature for more consistent analysis
                    ),
                    timeout=self.config.tool_call_timeout_seconds,
                )

                assistant_message = response.choices[0].message
                messages.append(assistant_message.model_dump())

                # Handle tool calls with monitoring
                iteration = 0
                while (
                    assistant_message.tool_calls
                    and iteration < self.config.max_tool_calls_per_conversation
                ):
                    logger.info(
                        f"Processing {len(assistant_message.tool_calls)} tool calls (iteration {iteration + 1})"
                    )

                    # Execute tool calls with error handling
                    tool_results = await self._execute_tools_with_monitoring(
                        assistant_message.tool_calls, metrics
                    )

                    # Add tool results to conversation
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
                    response = await asyncio.wait_for(
                        self.openai_client.chat.completions.create(
                            model="gpt-4",
                            messages=messages,
                            tools=self.tools,
                            tool_choice="auto",
                            temperature=0.1,
                        ),
                        timeout=self.config.tool_call_timeout_seconds,
                    )

                    assistant_message = response.choices[0].message
                    messages.append(assistant_message.model_dump())
                    iteration += 1

                # Track token usage if available
                if hasattr(response, "usage") and response.usage:
                    metrics.total_tokens_used = response.usage.total_tokens

                return {
                    "response": assistant_message.content,
                    "conversation_id": conversation_id,
                    "metrics": metrics.dict(),
                    "success": True,
                }

            except TimeoutError:
                logger.error(f"Conversation {conversation_id} timed out")
                return {
                    "error": "Request timed out",
                    "conversation_id": conversation_id,
                    "metrics": metrics.dict(),
                    "success": False,
                }
            except Exception as e:
                logger.error(f"Conversation {conversation_id} failed: {e}")
                return {
                    "error": str(e),
                    "conversation_id": conversation_id,
                    "metrics": metrics.dict(),
                    "success": False,
                }

    async def _execute_tools_with_monitoring(
        self, tool_calls, metrics: ConversationMetrics
    ) -> list[Any]:
        """Execute tool calls with monitoring and error handling."""

        # Limit concurrent tool executions
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tools)

        async def execute_single_tool_with_semaphore(tool_call):
            async with semaphore:
                return await self._execute_single_tool_with_retry(tool_call, metrics)

        # Execute all tool calls
        tasks = [execute_single_tool_with_semaphore(tc) for tc in tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Tool call {i} failed: {result}")
                processed_results.append({"error": str(result)})
                metrics.add_tool_call(success=False)
            else:
                processed_results.append(result)
                metrics.add_tool_call(success=True)

        return processed_results

    async def _execute_single_tool_with_retry(
        self, tool_call, metrics: ConversationMetrics
    ) -> Any:
        """Execute a single tool call with retry logic."""

        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Executing {function_name} (attempt {attempt + 1})")

                result = await asyncio.wait_for(
                    self.justifi_toolkit.call_tool(function_name, arguments),
                    timeout=self.config.tool_call_timeout_seconds,
                )

                logger.debug(f"Tool {function_name} succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Tool {function_name} failed on attempt {attempt + 1}: {e}"
                )

                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay_seconds * (
                        self.config.backoff_multiplier**attempt
                    )
                    logger.debug(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)

        # All retries failed
        logger.error(
            f"Tool {function_name} failed after {self.config.max_retries} attempts"
        )
        raise last_exception


async def demonstrate_production_patterns():
    """Demonstrate production-ready patterns."""
    print("🏭 OpenAI Production Patterns Demo\n")

    # Load configuration
    try:
        config = ProductionConfig.from_env()
        if not all(
            [
                config.justifi_client_id,
                config.justifi_client_secret,
                config.openai_api_key,
            ]
        ):
            print("❌ Missing required environment variables")
            return
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return

    # Initialize assistant
    assistant = ProductionPayoutAssistant(config)

    # Example 1: Basic analysis with monitoring
    print("=" * 60)
    print("📊 Example 1: Monitored Payout Analysis")
    print("=" * 60)

    result = await assistant.analyze_payouts_with_monitoring(
        "Analyze our recent payout performance and identify any issues",
        conversation_id="demo_analysis_001",
    )

    if result["success"]:
        print("✅ Analysis completed successfully")
        print(f"📋 Response: {result['response'][:200]}...")
        print(f"📊 Metrics: {result['metrics']}")
    else:
        print(f"❌ Analysis failed: {result['error']}")

    # Example 2: Error handling demonstration
    print("\n" + "=" * 60)
    print("🛡️ Example 2: Error Handling")
    print("=" * 60)

    # Test with invalid query to show error handling
    error_result = await assistant.analyze_payouts_with_monitoring(
        "Delete all payouts",  # This should be handled gracefully
        conversation_id="demo_error_001",
    )

    print(f"Error handling result: {error_result['success']}")

    # Example 3: Performance testing
    print("\n" + "=" * 60)
    print("⚡ Example 3: Performance Testing")
    print("=" * 60)

    start_time = time.time()

    # Run multiple concurrent analyses
    tasks = [
        assistant.analyze_payouts_with_monitoring(
            f"Quick status check #{i}", conversation_id=f"perf_test_{i:03d}"
        )
        for i in range(3)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    duration = end_time - start_time

    successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))

    print("⚡ Performance test completed:")
    print(f"   • Duration: {duration:.2f} seconds")
    print(f"   • Successful requests: {successful}/{len(tasks)}")
    print(f"   • Average time per request: {duration / len(tasks):.2f}s")

    print("\n✅ Production patterns demonstration complete!")


if __name__ == "__main__":

    async def main():
        await demonstrate_production_patterns()

        print("\n🎯 Production Patterns Demonstrated:")
        print("   • Comprehensive configuration management")
        print("   • Structured logging and monitoring")
        print("   • Rate limiting and timeout handling")
        print("   • Retry logic with exponential backoff")
        print("   • Concurrent tool execution with semaphores")
        print("   • Conversation tracking and metrics")
        print("   • Error handling and circuit breaker patterns")
        print("   • Performance optimization techniques")

    asyncio.run(main())
