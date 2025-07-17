#!/usr/bin/env python3

"""
LangChain Production Patterns Example for JustiFi MCP Server

This example demonstrates production-ready LangChain patterns including:
- Robust error handling and retry logic
- Performance monitoring and metrics
- Agent deployment patterns
- Scalable agent architectures
- Security and rate limiting
- Logging and observability

Requirements:
    uv pip install langchain langchain-openai pydantic python-dotenv

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
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.callbacks.base import BaseCallbackHandler
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.outputs import LLMResult
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from justifi_mcp import JustiFiToolkit

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Track agent performance metrics."""

    session_id: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    tool_calls: int = 0
    avg_response_time: float = 0.0

    def add_request(
        self,
        success: bool,
        tokens: int = 0,
        cost: float = 0.0,
        response_time: float = 0.0,
    ):
        """Record a request."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.total_tokens += tokens
        self.total_cost += cost

        # Update average response time
        if self.total_requests > 1:
            self.avg_response_time = (
                (self.avg_response_time * (self.total_requests - 1)) + response_time
            ) / self.total_requests
        else:
            self.avg_response_time = response_time

    def finish(self):
        """Mark session as finished."""
        self.end_time = time.time()

    @property
    def duration(self) -> float:
        """Get session duration."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def success_rate(self) -> float:
        """Get success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests


class ProductionCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for production monitoring."""

    def __init__(self, metrics: AgentMetrics):
        self.metrics = metrics
        self.current_request_start = None

    def on_chain_start(
        self, serialized: dict[str, Any], inputs: dict[str, Any], **kwargs
    ):
        """Called when chain starts."""
        self.current_request_start = time.time()
        logger.debug(f"Chain started for session {self.metrics.session_id}")

    def on_chain_end(self, outputs: dict[str, Any], **kwargs):
        """Called when chain ends."""
        if self.current_request_start:
            response_time = time.time() - self.current_request_start
            self.metrics.add_request(success=True, response_time=response_time)
        logger.debug(f"Chain completed for session {self.metrics.session_id}")

    def on_chain_error(self, error: Exception, **kwargs):
        """Called when chain errors."""
        if self.current_request_start:
            response_time = time.time() - self.current_request_start
            self.metrics.add_request(success=False, response_time=response_time)
        logger.error(f"Chain error in session {self.metrics.session_id}: {error}")

    def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs):
        """Called when tool starts."""
        self.metrics.tool_calls += 1
        logger.debug(f"Tool call started: {serialized.get('name', 'unknown')}")

    def on_llm_end(self, response: LLMResult, **kwargs):
        """Called when LLM ends."""
        if response.llm_output and "token_usage" in response.llm_output:
            tokens = response.llm_output["token_usage"].get("total_tokens", 0)
            self.metrics.total_tokens += tokens


class ProductionAgentConfig(BaseModel):
    """Production agent configuration."""

    # Agent Configuration
    model_name: str = "gpt-4"
    temperature: float = 0.1
    max_iterations: int = 10
    max_execution_time: int = 300  # 5 minutes

    # Memory Configuration
    memory_window: int = 20
    enable_memory: bool = True

    # Rate Limiting
    requests_per_minute: int = 60
    max_concurrent_sessions: int = 10

    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0

    # Security
    allowed_tools: list[str] = [
        "list_payouts",
        "retrieve_payout",
        "get_payout_status",
        "get_recent_payouts",
    ]
    enable_input_validation: bool = True
    max_input_length: int = 5000

    # Monitoring
    enable_detailed_logging: bool = True
    log_tool_calls: bool = True
    log_responses: bool = False  # Be careful with PII


class ProductionPayoutAgent:
    """Production-ready payout analysis agent."""

    def __init__(self, config: ProductionAgentConfig):
        self.config = config
        self.active_sessions: dict[str, AgentMetrics] = {}
        self.rate_limiter = self._create_rate_limiter()

        # Initialize JustiFi toolkit
        self.toolkit = JustiFiToolkit(
            client_id=os.getenv("JUSTIFI_CLIENT_ID"),
            client_secret=os.getenv("JUSTIFI_CLIENT_SECRET"),
            enabled_tools=config.allowed_tools,
        )

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            request_timeout=60,
        )

        # Get tools
        self.tools = self.toolkit.get_langchain_tools()

        logger.info(f"Initialized ProductionPayoutAgent with {len(self.tools)} tools")

    def _create_rate_limiter(self):
        """Create a simple rate limiter."""
        return {
            "requests": [],
            "max_requests": self.config.requests_per_minute,
            "window": 60,  # seconds
        }

    async def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits."""
        current_time = time.time()

        self.rate_limiter["requests"] = [
            req_time
            for req_time in self.rate_limiter["requests"]
            if current_time - req_time < self.rate_limiter["window"]
        ]

        # Check if we can make another request
        if len(self.rate_limiter["requests"]) >= self.rate_limiter["max_requests"]:
            return False

        # Add current request
        self.rate_limiter["requests"].append(current_time)
        return True

    def _validate_input(self, user_input: str) -> bool:
        """Validate user input for security."""
        if not self.config.enable_input_validation:
            return True

        # Check length
        if len(user_input) > self.config.max_input_length:
            logger.warning(f"Input too long: {len(user_input)} chars")
            return False

        # Check for potentially malicious patterns
        dangerous_patterns = [
            "rm -rf",
            "DROP TABLE",
            "DELETE FROM",
            "UPDATE SET",
            "<script>",
            "javascript:",
            "eval(",
            "exec(",
        ]

        user_input_lower = user_input.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in user_input_lower:
                logger.warning(f"Potentially dangerous input detected: {pattern}")
                return False

        return True

    @asynccontextmanager
    async def _session_context(self, session_id: str):
        """Context manager for agent sessions."""

        # Check concurrent session limit
        if len(self.active_sessions) >= self.config.max_concurrent_sessions:
            raise Exception("Maximum concurrent sessions reached")

        metrics = AgentMetrics(session_id=session_id)
        self.active_sessions[session_id] = metrics

        try:
            logger.info(f"Starting session {session_id}")
            yield metrics
        except Exception as e:
            logger.error(f"Session {session_id} failed: {e}")
            raise
        finally:
            metrics.finish()
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

            logger.info(
                f"Session {session_id} completed: "
                f"duration={metrics.duration:.2f}s, "
                f"requests={metrics.total_requests}, "
                f"success_rate={metrics.success_rate:.2%}, "
                f"tokens={metrics.total_tokens}"
            )

    async def analyze_with_retry(
        self, user_input: str, session_id: str = None, context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Perform analysis with retry logic and comprehensive error handling."""

        if not session_id:
            session_id = str(uuid4())

        # Validate input
        if not self._validate_input(user_input):
            return {
                "success": False,
                "error": "Input validation failed",
                "session_id": session_id,
            }

        # Check rate limits
        if not await self._check_rate_limit():
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "session_id": session_id,
            }

        async with self._session_context(session_id) as metrics:
            # Setup memory if enabled
            memory = None
            if self.config.enable_memory:
                memory = ConversationBufferWindowMemory(
                    memory_key="chat_history",
                    output_key="output",
                    return_messages=True,
                    k=self.config.memory_window,
                )

            # Create agent with monitoring
            callback_handler = ProductionCallbackHandler(metrics)

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a professional financial analyst specializing in payout data analysis.

Provide thorough, accurate analysis with specific data points and actionable recommendations.
Always validate data before drawing conclusions and highlight any limitations in your analysis.

Available tools: {tools}

Context: {context}""",
                    ),
                    MessagesPlaceholder(variable_name="chat_history", optional=True),
                    ("user", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )

            agent = create_openai_tools_agent(self.llm, self.tools, prompt)

            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=memory,
                callbacks=[callback_handler],
                verbose=self.config.enable_detailed_logging,
                max_iterations=self.config.max_iterations,
                max_execution_time=self.config.max_execution_time,
                handle_parsing_errors=True,
                return_intermediate_steps=True,
            )

            # Retry logic
            last_exception = None

            for attempt in range(self.config.max_retries):
                try:
                    logger.debug(
                        f"Analysis attempt {attempt + 1} for session {session_id}"
                    )

                    result = await agent_executor.ainvoke(
                        {
                            "input": user_input,
                            "tools": [tool.name for tool in self.tools],
                            "context": context or {},
                        }
                    )

                    return {
                        "success": True,
                        "output": result["output"],
                        "intermediate_steps": result.get("intermediate_steps", []),
                        "session_id": session_id,
                        "metrics": {
                            "duration": metrics.duration,
                            "tool_calls": metrics.tool_calls,
                            "tokens": metrics.total_tokens,
                            "success_rate": metrics.success_rate,
                        },
                    }

                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1} failed for session {session_id}: {e}"
                    )

                    if attempt < self.config.max_retries - 1:
                        delay = self.config.retry_delay * (
                            self.config.backoff_multiplier**attempt
                        )
                        logger.debug(f"Retrying in {delay:.1f} seconds...")
                        await asyncio.sleep(delay)

            # All retries failed
            return {
                "success": False,
                "error": str(last_exception),
                "session_id": session_id,
                "metrics": {
                    "duration": metrics.duration,
                    "tool_calls": metrics.tool_calls,
                    "tokens": metrics.total_tokens,
                    "success_rate": metrics.success_rate,
                },
            }

    def get_system_status(self) -> dict[str, Any]:
        """Get current system status and metrics."""
        return {
            "active_sessions": len(self.active_sessions),
            "max_concurrent_sessions": self.config.max_concurrent_sessions,
            "rate_limit_status": {
                "current_requests": len(self.rate_limiter["requests"]),
                "max_requests": self.rate_limiter["max_requests"],
                "window_seconds": self.rate_limiter["window"],
            },
            "enabled_tools": self.config.allowed_tools,
            "configuration": {
                "model": self.config.model_name,
                "max_iterations": self.config.max_iterations,
                "memory_enabled": self.config.enable_memory,
            },
        }


async def demonstrate_production_deployment():
    """Demonstrate production deployment patterns."""
    print("🏭 Production Deployment Demo\n")

    # Create production configuration
    config = ProductionAgentConfig(
        model_name="gpt-4",
        temperature=0.0,  # Deterministic for production
        max_iterations=8,
        requests_per_minute=30,  # Conservative rate limit
        enable_detailed_logging=True,
        log_tool_calls=True,
    )

    # Initialize production agent
    agent = ProductionPayoutAgent(config)

    print(f"📊 System Status: {json.dumps(agent.get_system_status(), indent=2)}\n")

    # Example 1: Normal operation
    print("=" * 60)
    print("✅ Example 1: Normal Operation")
    print("=" * 60)

    result = await agent.analyze_with_retry(
        "Analyze our recent payout performance and identify any issues",
        session_id="prod_demo_001",
        context={"environment": "production", "user_role": "analyst"},
    )

    if result["success"]:
        print("✅ Analysis successful")
        print(f"📊 Metrics: {result['metrics']}")
        print(f"📋 Response: {result['output'][:200]}...")
    else:
        print(f"❌ Analysis failed: {result['error']}")

    # Example 2: Error handling
    print("\n" + "=" * 60)
    print("🛡️ Example 2: Error Handling")
    print("=" * 60)

    # Test with invalid input
    error_result = await agent.analyze_with_retry(
        "x" * 6000,
        session_id="prod_demo_002",  # Too long input
    )

    print(
        f"Input validation result: {'✅ Blocked' if not error_result['success'] else '❌ Allowed'}"
    )

    # Example 3: Rate limiting
    print("\n" + "=" * 60)
    print("⚡ Example 3: Rate Limiting")
    print("=" * 60)

    # Make multiple rapid requests
    tasks = []
    for i in range(5):
        task = agent.analyze_with_retry(
            f"Quick status check #{i}", session_id=f"rate_test_{i}"
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))

    print(f"Rate limiting test: {successful}/{len(tasks)} requests succeeded")

    print(
        f"\n📊 Final System Status: {json.dumps(agent.get_system_status(), indent=2)}"
    )


async def demonstrate_scalable_architecture():
    """Demonstrate scalable agent architecture patterns."""
    print("\n🏗️ Scalable Architecture Demo\n")

    # Configuration for different environments
    environments = {
        "development": ProductionAgentConfig(
            model_name="gpt-3.5-turbo",
            max_iterations=5,
            requests_per_minute=100,
            enable_detailed_logging=True,
        ),
        "staging": ProductionAgentConfig(
            model_name="gpt-4",
            max_iterations=8,
            requests_per_minute=60,
            enable_detailed_logging=True,
        ),
        "production": ProductionAgentConfig(
            model_name="gpt-4",
            max_iterations=10,
            requests_per_minute=30,
            enable_detailed_logging=False,
            log_responses=False,
        ),
    }

    # Demonstrate environment-specific configuration
    for env_name, config in environments.items():
        print(f"🌍 {env_name.title()} Environment:")
        print(f"   Model: {config.model_name}")
        print(f"   Rate limit: {config.requests_per_minute}/min")
        print(f"   Max iterations: {config.max_iterations}")
        print(f"   Detailed logging: {config.enable_detailed_logging}")

    print("\n✅ Environment configurations ready for deployment")


if __name__ == "__main__":

    async def main():
        await demonstrate_production_deployment()
        await demonstrate_scalable_architecture()

        print("\n🎯 Production Patterns Demonstrated:")
        print("   • Comprehensive error handling and retry logic")
        print("   • Performance monitoring and metrics collection")
        print("   • Rate limiting and concurrent session management")
        print("   • Input validation and security measures")
        print("   • Environment-specific configuration management")
        print("   • Scalable agent architecture patterns")
        print("   • Production-ready logging and observability")
        print("   • Session tracking and resource management")

    asyncio.run(main())
