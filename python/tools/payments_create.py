"""JustiFi Payment Creation Tools

Secure payment creation tools with PCI compliance and test-mode enforcement.
All payment creation operations require test credentials for security.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError
from .response_formatter import standardize_response
from .utils.payment_security import validate_payment_creation


async def create_payment(
    client: JustiFiClient,
    amount: int,
    payment_method_id: str,
    description: str | None = None,
    currency: str = "usd",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a payment using an existing payment method.

    Args:
        client: JustiFi API client
        amount: Payment amount in cents (e.g., 1000 for $10.00)
        payment_method_id: ID of existing payment method to charge
        description: Optional description for the payment
        currency: Currency code (default: 'usd')
        metadata: Optional metadata dictionary

    Returns:
        Payment object with ID, status, amount, and details

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If payment creation fails
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

    if not payment_method_id or not isinstance(payment_method_id, str):
        raise ValidationError(
            "payment_method_id is required and must be a non-empty string",
            field="payment_method_id",
            value=payment_method_id,
        )

    # Validate optional parameters
    if description is not None and not isinstance(description, str):
        raise ValidationError(
            "description must be a string if provided",
            field="description",
            value=description,
        )

    if not isinstance(currency, str) or len(currency) != 3:
        raise ValidationError(
            "currency must be a 3-character currency code",
            field="currency",
            value=currency,
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
        }

        if description:
            payload["description"] = description

        if metadata:
            payload["metadata"] = metadata

        # Call JustiFi API to create payment
        result = await client.request("POST", "/v1/payments", data=payload)
        return standardize_response(result, "create_payment")

    except Exception as e:
        raise ToolError(
            f"Failed to create payment: {str(e)}",
            error_type="PaymentCreationError",
        ) from e


async def tokenize_payment_method(
    client: JustiFiClient,
    card_number: str,
    exp_month: int,
    exp_year: int,
    cvc: str,
    name: str | None = None,
    address_line1: str | None = None,
    address_line2: str | None = None,
    address_city: str | None = None,
    address_state: str | None = None,
    address_postal_code: str | None = None,
    address_country: str = "US",
) -> dict[str, Any]:
    """Tokenize a payment method (card) for secure storage and future use.

    Args:
        client: JustiFi API client
        card_number: Credit card number
        exp_month: Expiration month (1-12)
        exp_year: Expiration year (4 digits)
        cvc: Card verification code
        name: Cardholder name
        address_line1: Address line 1
        address_line2: Address line 2
        address_city: City
        address_state: State/province
        address_postal_code: Postal/zip code
        address_country: Country code (default: 'US')

    Returns:
        Payment method object with token ID and card details

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If tokenization fails
    """
    # Security validation
    validate_payment_creation(client.base_url, client.client_id, card_number)

    # Validate card parameters
    if not card_number or not isinstance(card_number, str):
        raise ValidationError(
            "card_number is required and must be a string",
            field="card_number",
            value="[REDACTED]",
        )

    # Clean card number and validate length
    clean_card = "".join(c for c in card_number if c.isdigit())
    if len(clean_card) < 13 or len(clean_card) > 19:
        raise ValidationError(
            "card_number must be between 13 and 19 digits",
            field="card_number",
            value="[REDACTED]",
        )

    # Validate expiration month
    if not isinstance(exp_month, int) or exp_month < 1 or exp_month > 12:
        raise ValidationError(
            "exp_month must be an integer between 1 and 12",
            field="exp_month",
            value=exp_month,
        )

    # Validate expiration year
    if not isinstance(exp_year, int) or exp_year < 2000 or exp_year > 9999:
        raise ValidationError(
            "exp_year must be a 4-digit year",
            field="exp_year",
            value=exp_year,
        )

    # Validate CVC
    if not cvc or not isinstance(cvc, str):
        raise ValidationError(
            "cvc is required and must be a string",
            field="cvc",
            value="[REDACTED]",
        )

    if not cvc.isdigit() or len(cvc) < 3 or len(cvc) > 4:
        raise ValidationError(
            "cvc must be 3 or 4 digits",
            field="cvc",
            value="[REDACTED]",
        )

    try:
        # Build card payload
        card_payload: dict[str, Any] = {
            "number": clean_card,
            "exp_month": exp_month,
            "exp_year": exp_year,
            "cvc": cvc,
            "address_country": address_country,
        }

        if name:
            card_payload["name"] = name
        if address_line1:
            card_payload["address_line1"] = address_line1
        if address_line2:
            card_payload["address_line2"] = address_line2
        if address_city:
            card_payload["address_city"] = address_city
        if address_state:
            card_payload["address_state"] = address_state
        if address_postal_code:
            card_payload["address_postal_code"] = address_postal_code

        # Build request payload
        payload = {
            "card": card_payload,
        }

        # Call JustiFi API to tokenize payment method
        result = await client.request("POST", "/v1/payment_methods", data=payload)
        return standardize_response(result, "tokenize_payment_method")

    except Exception as e:
        raise ToolError(
            f"Failed to tokenize payment method: {str(e)}",
            error_type="PaymentMethodTokenizationError",
        ) from e


async def create_payment_with_card(
    client: JustiFiClient,
    amount: int,
    card_number: str,
    exp_month: int,
    exp_year: int,
    cvc: str,
    description: str | None = None,
    currency: str = "usd",
    name: str | None = None,
    address_line1: str | None = None,
    address_line2: str | None = None,
    address_city: str | None = None,
    address_state: str | None = None,
    address_postal_code: str | None = None,
    address_country: str = "US",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a payment directly with card details (tokenizes and charges in one step).

    Args:
        client: JustiFi API client
        amount: Payment amount in cents (e.g., 1000 for $10.00)
        card_number: Credit card number
        exp_month: Expiration month (1-12)
        exp_year: Expiration year (4 digits)
        cvc: Card verification code
        description: Optional description for the payment
        currency: Currency code (default: 'usd')
        name: Cardholder name
        address_line1: Address line 1
        address_line2: Address line 2
        address_city: City
        address_state: State/province
        address_postal_code: Postal/zip code
        address_country: Country code (default: 'US')
        metadata: Optional metadata dictionary

    Returns:
        Payment object with ID, status, amount, and details

    Raises:
        PaymentSecurityError: If test mode validation fails
        ValidationError: If parameters are invalid
        ToolError: If payment creation fails
    """
    # Security validation
    validate_payment_creation(client.base_url, client.client_id, card_number)

    # Validate amount
    if not isinstance(amount, int) or amount <= 0:
        raise ValidationError(
            "amount must be a positive integer in cents",
            field="amount",
            value=amount,
        )

    # Validate currency
    if not isinstance(currency, str) or len(currency) != 3:
        raise ValidationError(
            "currency must be a 3-character currency code",
            field="currency",
            value=currency,
        )

    # First tokenize the payment method
    payment_method = await tokenize_payment_method(
        client=client,
        card_number=card_number,
        exp_month=exp_month,
        exp_year=exp_year,
        cvc=cvc,
        name=name,
        address_line1=address_line1,
        address_line2=address_line2,
        address_city=address_city,
        address_state=address_state,
        address_postal_code=address_postal_code,
        address_country=address_country,
    )

    # Extract payment method ID from response
    payment_method_id = payment_method.get("data", {}).get("id")
    if not payment_method_id:
        raise ToolError(
            "Failed to extract payment method ID from tokenization response",
            error_type="TokenizationError",
        )

    # Create payment using the tokenized payment method
    return await create_payment(
        client=client,
        amount=amount,
        payment_method_id=payment_method_id,
        description=description,
        currency=currency,
        metadata=metadata,
    )
