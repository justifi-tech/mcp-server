"""
Base classes for JustiFi tools.

This module provides the foundation for all JustiFi tools with common
error handling, validation, and interface patterns.
"""

import functools
from abc import ABC, abstractmethod
from typing import Any

from ..core import JustiFiClient


class ToolError(Exception):
    """Base exception for tool errors."""

    def __init__(
        self,
        message: str,
        error_type: str = "ToolError",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}


class ValidationError(ToolError):
    """Raised when tool input validation fails."""

    def __init__(self, message: str, field: str | None = None, value: Any = None):
        super().__init__(message, "ValidationError", {"field": field, "value": value})
        self.field = field
        self.value = value


class BaseTool(ABC):
    """Base class for all JustiFi tools."""

    def __init__(self, client: JustiFiClient):
        self.client = client

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with given parameters."""
        pass

    def validate_required_param(self, value: Any, param_name: str) -> None:
        """Validate that a required parameter is provided and not empty."""
        if value is None:
            raise ValidationError(
                f"{param_name} is required", field=param_name, value=value
            )

        if isinstance(value, str) and not value.strip():
            raise ValidationError(
                f"{param_name} cannot be empty", field=param_name, value=value
            )

    def validate_positive_integer(
        self, value: Any, param_name: str, min_val: int = 1, max_val: int | None = None
    ) -> None:
        """Validate that a parameter is a positive integer within bounds."""
        if not isinstance(value, int):
            raise ValidationError(
                f"{param_name} must be an integer", field=param_name, value=value
            )

        if value < min_val:
            raise ValidationError(
                f"{param_name} must be at least {min_val}",
                field=param_name,
                value=value,
            )

        if max_val is not None and value > max_val:
            raise ValidationError(
                f"{param_name} must be at most {max_val}", field=param_name, value=value
            )


def handle_tool_errors(func: Any) -> Any:
    """Decorator to handle common tool errors and provide consistent error formatting."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions in ToolError
            error_type = type(e).__name__
            raise ToolError(str(e), error_type=error_type) from e

    return wrapper
