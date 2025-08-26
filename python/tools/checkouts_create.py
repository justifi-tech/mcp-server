"""JustiFi Checkout Creation Tools

Checkout creation and management tools with PCI compliance.
All checkout creation operations require test credentials for security.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError
from .response_formatter import standardize_response
from .utils.payment_security import validate_payment_creation


async def create_checkout(
    client: JustiFiClient,
    amount: int,
    description: str,
    payment_method_group_id: str,
    currency: str = "usd",
    success_url: str | None = None,
    cancel_url: str | None = None,
    metadata: dict[str, Any] | None = None,
    expires_at: str | None = None,
) -> dict[str, Any]:
    """Create a checkout session for payment processing.

    Checkouts provide a hosted payment page that handles payment collection
    and returns the customer to your application with the result.

    Args:
        client: JustiFi API client
        amount: Payment amount in cents (e.g., 1000 for $10.00)
        description: Description of what is being purchased
        payment_method_group_id: ID of payment method group to use
        currency: Currency code (default: 'usd')
        success_url: URL to redirect to after successful payment
        cancel_url: URL to redirect to if payment is cancelled
        metadata: Optional metadata dictionary
        expires_at: Optional expiration timestamp (ISO 8601 format)

    Returns:
        Checkout object with ID, URL, and details

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If checkout creation fails
    """
    # Security validation
    validate_payment_creation(client.base_url, client.client_id)

    # Validate required parameters
    if not isinstance(amount, int) or amount <= 0:
        raise ValidationError(
            "amount must be a positive integer in cents",
            field="amount",
            value=amount,
        )

    if not description or not isinstance(description, str):
        raise ValidationError(
            "description is required and must be a non-empty string",
            field="description",
            value=description,
        )

    if not payment_method_group_id or not isinstance(payment_method_group_id, str):
        raise ValidationError(
            "payment_method_group_id is required and must be a non-empty string",
            field="payment_method_group_id",
            value=payment_method_group_id,
        )

    # Validate optional parameters
    if not isinstance(currency, str) or len(currency) != 3:
        raise ValidationError(
            "currency must be a 3-character currency code",
            field="currency",
            value=currency,
        )

    if success_url is not None and not isinstance(success_url, str):
        raise ValidationError(
            "success_url must be a string if provided",
            field="success_url",
            value=success_url,
        )

    if cancel_url is not None and not isinstance(cancel_url, str):
        raise ValidationError(
            "cancel_url must be a string if provided",
            field="cancel_url",
            value=cancel_url,
        )

    if metadata is not None and not isinstance(metadata, dict):
        raise ValidationError(
            "metadata must be a dictionary if provided",
            field="metadata",
            value=metadata,
        )

    if expires_at is not None and not isinstance(expires_at, str):
        raise ValidationError(
            "expires_at must be an ISO 8601 timestamp string if provided",
            field="expires_at",
            value=expires_at,
        )

    try:
        # Build request payload
        payload: dict[str, Any] = {
            "amount": amount,
            "currency": currency.lower(),
            "description": description,
            "payment_method_group_id": payment_method_group_id,
        }

        if success_url:
            payload["success_url"] = success_url

        if cancel_url:
            payload["cancel_url"] = cancel_url

        if metadata:
            payload["metadata"] = metadata

        if expires_at:
            payload["expires_at"] = expires_at

        # Call JustiFi API to create checkout
        result = await client.request("POST", "/v1/checkouts", data=payload)
        return standardize_response(result, "create_checkout")

    except Exception as e:
        raise ToolError(
            f"Failed to create checkout: {str(e)}",
            error_type="CheckoutCreationError",
        ) from e


async def update_checkout(
    client: JustiFiClient,
    checkout_id: str,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
    expires_at: str | None = None,
) -> dict[str, Any]:
    """Update an existing checkout session.

    Args:
        client: JustiFi API client
        checkout_id: The checkout ID to update
        description: Updated description
        metadata: Updated metadata dictionary
        expires_at: Updated expiration timestamp (ISO 8601 format)

    Returns:
        Updated checkout object

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If checkout update fails
    """
    # Security validation
    validate_payment_creation(client.base_url, client.client_id)

    # Validate required parameters
    if not checkout_id or not isinstance(checkout_id, str):
        raise ValidationError(
            "checkout_id is required and must be a non-empty string",
            field="checkout_id",
            value=checkout_id,
        )

    # Validate optional parameters
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

    if expires_at is not None and not isinstance(expires_at, str):
        raise ValidationError(
            "expires_at must be an ISO 8601 timestamp string if provided",
            field="expires_at",
            value=expires_at,
        )

    # Ensure at least one field is being updated
    if all(param is None for param in [description, metadata, expires_at]):
        raise ValidationError(
            "At least one field must be provided for update",
            field="update_fields",
            value=None,
        )

    try:
        # Build request payload with only provided fields
        payload: dict[str, Any] = {}

        if description is not None:
            payload["description"] = description

        if metadata is not None:
            payload["metadata"] = metadata

        if expires_at is not None:
            payload["expires_at"] = expires_at

        # Call JustiFi API to update checkout
        result = await client.request(
            "PATCH", f"/v1/checkouts/{checkout_id}", data=payload
        )
        return standardize_response(result, "update_checkout")

    except Exception as e:
        raise ToolError(
            f"Failed to update checkout {checkout_id}: {str(e)}",
            error_type="CheckoutUpdateError",
        ) from e


async def complete_checkout(
    client: JustiFiClient,
    checkout_id: str,
    payment_method_id: str,
) -> dict[str, Any]:
    """Complete a checkout session with a payment method.

    Args:
        client: JustiFi API client
        checkout_id: The checkout ID to complete
        payment_method_id: ID of payment method to use for payment

    Returns:
        Completed checkout object with payment details

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If checkout completion fails
    """
    # Security validation
    validate_payment_creation(client.base_url, client.client_id)

    # Validate required parameters
    if not checkout_id or not isinstance(checkout_id, str):
        raise ValidationError(
            "checkout_id is required and must be a non-empty string",
            field="checkout_id",
            value=checkout_id,
        )

    if not payment_method_id or not isinstance(payment_method_id, str):
        raise ValidationError(
            "payment_method_id is required and must be a non-empty string",
            field="payment_method_id",
            value=payment_method_id,
        )

    try:
        # Build request payload
        payload = {
            "payment_method_id": payment_method_id,
        }

        # Call JustiFi API to complete checkout
        result = await client.request(
            "POST", f"/v1/checkouts/{checkout_id}/complete", data=payload
        )
        return standardize_response(result, "complete_checkout")

    except Exception as e:
        raise ToolError(
            f"Failed to complete checkout {checkout_id}: {str(e)}",
            error_type="CheckoutCompletionError",
        ) from e


async def expire_checkout(
    client: JustiFiClient,
    checkout_id: str,
) -> dict[str, Any]:
    """Expire a checkout session manually.

    Args:
        client: JustiFi API client
        checkout_id: The checkout ID to expire

    Returns:
        Expired checkout object

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If checkout expiration fails
    """
    # Security validation
    validate_payment_creation(client.base_url, client.client_id)

    # Validate required parameters
    if not checkout_id or not isinstance(checkout_id, str):
        raise ValidationError(
            "checkout_id is required and must be a non-empty string",
            field="checkout_id",
            value=checkout_id,
        )

    try:
        # Call JustiFi API to expire checkout
        result = await client.request("POST", f"/v1/checkouts/{checkout_id}/expire")
        return standardize_response(result, "expire_checkout")

    except Exception as e:
        raise ToolError(
            f"Failed to expire checkout {checkout_id}: {str(e)}",
            error_type="CheckoutExpirationError",
        ) from e
