"""JustiFi Payment Intent Tools

Payment intent creation and management tools with PCI compliance.
All payment intent creation operations require test credentials for security.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError
from .response_formatter import standardize_response
from .utils.security import validate_test_mode_for_payments, log_security_event


async def create_payment_intent(
    client: JustiFiClient,
    amount: int,
    payment_method_id: str,
    description: str | None = None,
    currency: str = "usd",
    capture_method: str = "automatic",
    confirmation_method: str = "automatic",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a payment intent for deferred or manual capture.

    Payment intents allow you to separate authorization from capture,
    useful for scenarios like pre-authorization or manual review.

    Args:
        client: JustiFi API client
        amount: Payment amount in cents (e.g., 1000 for $10.00)
        payment_method_id: ID of existing payment method to use
        description: Optional description for the payment intent
        currency: Currency code (default: 'usd')
        capture_method: 'automatic' or 'manual' (default: 'automatic')
        confirmation_method: 'automatic' or 'manual' (default: 'automatic')
        metadata: Optional metadata dictionary

    Returns:
        Payment intent object with ID, status, amount, and details

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If payment intent creation fails
    """
    # Security validation - payment intent creation requires test mode
    validation_result = validate_test_mode_for_payments(client.base_url, client.client_id)
    
    # Log security event
    log_security_event("payment_intent_creation", {
        "operation": "create_payment_intent",
        "amount": amount,
        "currency": currency,
        "capture_method": capture_method,
        "environment_info": validation_result["environment_info"]
    })

    # Validate required parameters
    if not isinstance(amount, int) or amount <= 0:
        raise ValidationError(
            "amount must be a positive integer in cents",
            field="amount",
            value=amount,
        )

    if not payment_method_id or not isinstance(payment_method_id, str):
        raise ValidationError(
            "payment_method_id is required and must be a non-empty string",
            field="payment_method_id",
            value=payment_method_id,
        )

    # Validate optional parameters
    if not isinstance(currency, str) or len(currency) != 3:
        raise ValidationError(
            "currency must be a 3-character currency code",
            field="currency",
            value=currency,
        )

    if capture_method not in ["automatic", "manual"]:
        raise ValidationError(
            "capture_method must be 'automatic' or 'manual'",
            field="capture_method",
            value=capture_method,
        )

    if confirmation_method not in ["automatic", "manual"]:
        raise ValidationError(
            "confirmation_method must be 'automatic' or 'manual'",
            field="confirmation_method",
            value=confirmation_method,
        )

    if description is not None and not isinstance(description, str):
        raise ValidationError(
            "description must be a string if provided",
            field="description",
            value=description,
        )

    if metadata is not None and not isinstance(metadata, dict):
        raise ValidationError(
            "metadata must be a dictionary if provided",
            field="metadata",
            value=metadata,
        )

    try:
        # Build request payload
        payload: dict[str, Any] = {
            "amount": amount,
            "currency": currency.lower(),
            "payment_method_id": payment_method_id,
            "capture_method": capture_method,
            "confirmation_method": confirmation_method,
        }

        if description:
            payload["description"] = description

        if metadata:
            payload["metadata"] = metadata

        # Call JustiFi API to create payment intent
        result = await client.request("POST", "/v1/payment_intents", json=payload)
        return standardize_response(result, "create_payment_intent")

    except Exception as e:
        raise ToolError(
            f"Failed to create payment intent: {str(e)}",
            error_type="PaymentIntentCreationError",
        ) from e


async def capture_payment_intent(
    client: JustiFiClient,
    intent_id: str,
    amount: int | None = None,
) -> dict[str, Any]:
    """Capture a payment intent that was created with manual capture.

    Args:
        client: JustiFi API client
        intent_id: The payment intent ID to capture
        amount: Optional amount to capture (defaults to full authorized amount)

    Returns:
        Updated payment intent object showing captured status

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If payment intent capture fails
    """
    # Security validation - payment intent operations require test mode
    validation_result = validate_test_mode_for_payments(client.base_url, client.client_id)
    
    # Log security event
    log_security_event("payment_intent_capture", {
        "operation": "capture_payment_intent",
        "intent_id": intent_id,
        "capture_amount": amount,
        "environment_info": validation_result["environment_info"]
    })

    # Validate required parameters
    if not intent_id or not isinstance(intent_id, str):
        raise ValidationError(
            "intent_id is required and must be a non-empty string",
            field="intent_id",
            value=intent_id,
        )

    # Validate optional amount
    if amount is not None:
        if not isinstance(amount, int) or amount <= 0:
            raise ValidationError(
                "amount must be a positive integer in cents if provided",
                field="amount",
                value=amount,
            )

    try:
        # Build request payload
        payload: dict[str, Any] = {}
        if amount is not None:
            payload["amount"] = amount

        # Call JustiFi API to capture payment intent
        result = await client.request(
            "POST", f"/v1/payment_intents/{intent_id}/capture", json=payload
        )
        return standardize_response(result, "capture_payment_intent")

    except Exception as e:
        raise ToolError(
            f"Failed to capture payment intent {intent_id}: {str(e)}",
            error_type="PaymentIntentCaptureError",
        ) from e


async def cancel_payment_intent(
    client: JustiFiClient,
    intent_id: str,
    cancellation_reason: str | None = None,
) -> dict[str, Any]:
    """Cancel a payment intent that hasn't been captured.

    Args:
        client: JustiFi API client
        intent_id: The payment intent ID to cancel
        cancellation_reason: Optional reason for cancellation

    Returns:
        Updated payment intent object showing cancelled status

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If payment intent cancellation fails
    """
    # Security validation - payment intent operations require test mode
    validation_result = validate_test_mode_for_payments(client.base_url, client.client_id)
    
    # Log security event
    log_security_event("payment_intent_cancellation", {
        "operation": "cancel_payment_intent",
        "intent_id": intent_id,
        "reason": cancellation_reason,
        "environment_info": validation_result["environment_info"]
    })

    # Validate required parameters
    if not intent_id or not isinstance(intent_id, str):
        raise ValidationError(
            "intent_id is required and must be a non-empty string",
            field="intent_id",
            value=intent_id,
        )

    # Validate optional reason
    if cancellation_reason is not None and not isinstance(cancellation_reason, str):
        raise ValidationError(
            "cancellation_reason must be a string if provided",
            field="cancellation_reason",
            value=cancellation_reason,
        )

    try:
        # Build request payload
        payload: dict[str, Any] = {}
        if cancellation_reason:
            payload["cancellation_reason"] = cancellation_reason

        # Call JustiFi API to cancel payment intent
        result = await client.request(
            "POST", f"/v1/payment_intents/{intent_id}/cancel", json=payload
        )
        return standardize_response(result, "cancel_payment_intent")

    except Exception as e:
        raise ToolError(
            f"Failed to cancel payment intent {intent_id}: {str(e)}",
            error_type="PaymentIntentCancellationError",
        ) from e


async def confirm_payment_intent(
    client: JustiFiClient,
    intent_id: str,
    payment_method_id: str | None = None,
) -> dict[str, Any]:
    """Confirm a payment intent that was created with manual confirmation.

    Args:
        client: JustiFi API client
        intent_id: The payment intent ID to confirm
        payment_method_id: Optional payment method ID (if not already attached)

    Returns:
        Updated payment intent object showing confirmed status

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If payment intent confirmation fails
    """
    # Security validation - payment intent operations require test mode
    validation_result = validate_test_mode_for_payments(client.base_url, client.client_id)
    
    # Log security event
    log_security_event("payment_intent_confirmation", {
        "operation": "confirm_payment_intent",
        "intent_id": intent_id,
        "environment_info": validation_result["environment_info"]
    })

    # Validate required parameters
    if not intent_id or not isinstance(intent_id, str):
        raise ValidationError(
            "intent_id is required and must be a non-empty string",
            field="intent_id",
            value=intent_id,
        )

    # Validate optional payment method ID
    if payment_method_id is not None and not isinstance(payment_method_id, str):
        raise ValidationError(
            "payment_method_id must be a string if provided",
            field="payment_method_id",
            value=payment_method_id,
        )

    try:
        # Build request payload
        payload: dict[str, Any] = {}
        if payment_method_id:
            payload["payment_method_id"] = payment_method_id

        # Call JustiFi API to confirm payment intent
        result = await client.request(
            "POST", f"/v1/payment_intents/{intent_id}/confirm", json=payload
        )
        return standardize_response(result, "confirm_payment_intent")

    except Exception as e:
        raise ToolError(
            f"Failed to confirm payment intent {intent_id}: {str(e)}",
            error_type="PaymentIntentConfirmationError",
        ) from e