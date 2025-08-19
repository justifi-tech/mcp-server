"""
JustiFi Payment Method Group Tools

Payment method group operations for organizing and managing tokenized payment methods.
Allows creating, listing, retrieving, updating, and removing payment methods from groups.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError
from .response_formatter import standardize_response


async def create_payment_method_group(
    client: JustiFiClient,
    name: str,
    description: str | None = None,
    payment_method_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new payment method group to organize tokenized payment methods.

    Args:
        client: JustiFi API client
        name: Name of the payment method group (required)
        description: Optional description of the group
        payment_method_ids: Optional list of payment method IDs to add to the group

    Returns:
        Created payment method group object with ID, name, and metadata

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If group creation fails
    """
    if not name or not isinstance(name, str):
        raise ValidationError(
            "name is required and must be a non-empty string",
            field="name",
            value=name,
        )

    if not name.strip():
        raise ValidationError(
            "name cannot be empty or whitespace",
            field="name",
            value=name,
        )

    if description is not None and not isinstance(description, str):
        raise ValidationError(
            "description must be a string if provided",
            field="description",
            value=description,
        )

    if payment_method_ids is not None:
        if not isinstance(payment_method_ids, list):
            raise ValidationError(
                "payment_method_ids must be a list if provided",
                field="payment_method_ids",
                value=payment_method_ids,
            )
        for i, pm_id in enumerate(payment_method_ids):
            if not isinstance(pm_id, str) or not pm_id.strip():
                raise ValidationError(
                    f"payment_method_ids[{i}] must be a non-empty string",
                    field=f"payment_method_ids[{i}]",
                    value=pm_id,
                )

    try:
        # Build request payload
        payload: dict[str, Any] = {"name": name.strip()}

        if description:
            payload["description"] = description.strip()

        if payment_method_ids:
            payload["payment_method_ids"] = [pm_id.strip() for pm_id in payment_method_ids]

        # Call JustiFi API to create payment method group
        result = await client.request("POST", "/v1/payment_method_groups", data=payload)
        return standardize_response(result, "create_payment_method_group")

    except Exception as e:
        raise ToolError(
            f"Failed to create payment method group: {str(e)}",
            error_type="PaymentMethodGroupCreationError",
        ) from e


async def list_payment_method_groups(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List payment method groups with optional pagination.

    Args:
        client: JustiFi API client
        limit: Number of groups to return (1-100, default: 25)
        after_cursor: Cursor for pagination - returns results after this cursor
        before_cursor: Cursor for pagination - returns results before this cursor

    Returns:
        Paginated list of payment method groups with page_info for navigation

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If group listing fails
    """
    # Validate limit
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ValidationError(
            "limit must be an integer between 1 and 100", field="limit", value=limit
        )

    # Validate cursors (if provided)
    if after_cursor is not None and not isinstance(after_cursor, str):
        raise ValidationError(
            "after_cursor must be a string if provided",
            field="after_cursor",
            value=after_cursor,
        )

    if before_cursor is not None and not isinstance(before_cursor, str):
        raise ValidationError(
            "before_cursor must be a string if provided",
            field="before_cursor",
            value=before_cursor,
        )

    # Cannot use both cursors at the same time
    if after_cursor and before_cursor:
        raise ValidationError(
            "Cannot specify both after_cursor and before_cursor",
            field="cursors",
            value={"after_cursor": after_cursor, "before_cursor": before_cursor},
        )

    try:
        # Build query parameters
        params: dict[str, Any] = {"limit": limit}

        if after_cursor:
            params["after_cursor"] = after_cursor
        if before_cursor:
            params["before_cursor"] = before_cursor

        # Call JustiFi API to list payment method groups
        result = await client.request("GET", "/v1/payment_method_groups", params=params)
        return standardize_response(result, "list_payment_method_groups")

    except Exception as e:
        raise ToolError(
            f"Failed to list payment method groups: {str(e)}",
            error_type="PaymentMethodGroupListError",
        ) from e


async def retrieve_payment_method_group(
    client: JustiFiClient, group_id: str
) -> dict[str, Any]:
    """Retrieve detailed information about a specific payment method group.

    Args:
        client: JustiFi API client
        group_id: The unique identifier for the payment method group

    Returns:
        Payment method group object with ID, name, payment methods, and metadata

    Raises:
        ValidationError: If group_id is invalid
        ToolError: If group retrieval fails
    """
    if not group_id or not isinstance(group_id, str):
        raise ValidationError(
            "group_id is required and must be a non-empty string",
            field="group_id",
            value=group_id,
        )

    if not group_id.strip():
        raise ValidationError(
            "group_id cannot be empty or whitespace",
            field="group_id",
            value=group_id,
        )

    try:
        # Call JustiFi API to retrieve payment method group
        result = await client.request("GET", f"/v1/payment_method_groups/{group_id}")
        return standardize_response(result, "retrieve_payment_method_group")

    except Exception as e:
        raise ToolError(
            f"Failed to retrieve payment method group {group_id}: {str(e)}",
            error_type="PaymentMethodGroupRetrievalError",
        ) from e


async def update_payment_method_group(
    client: JustiFiClient,
    group_id: str,
    name: str | None = None,
    description: str | None = None,
    payment_method_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Update an existing payment method group.

    Args:
        client: JustiFi API client
        group_id: The unique identifier for the payment method group
        name: New name for the group (optional)
        description: New description for the group (optional)
        payment_method_ids: New list of payment method IDs to set in the group (optional)

    Returns:
        Updated payment method group object with ID, name, and metadata

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If group update fails
    """
    if not group_id or not isinstance(group_id, str):
        raise ValidationError(
            "group_id is required and must be a non-empty string",
            field="group_id",
            value=group_id,
        )

    if not group_id.strip():
        raise ValidationError(
            "group_id cannot be empty or whitespace",
            field="group_id",
            value=group_id,
        )

    if name is not None:
        if not isinstance(name, str):
            raise ValidationError(
                "name must be a string if provided",
                field="name",
                value=name,
            )
        if not name.strip():
            raise ValidationError(
                "name cannot be empty or whitespace if provided",
                field="name",
                value=name,
            )

    if description is not None and not isinstance(description, str):
        raise ValidationError(
            "description must be a string if provided",
            field="description",
            value=description,
        )

    if payment_method_ids is not None:
        if not isinstance(payment_method_ids, list):
            raise ValidationError(
                "payment_method_ids must be a list if provided",
                field="payment_method_ids",
                value=payment_method_ids,
            )
        for i, pm_id in enumerate(payment_method_ids):
            if not isinstance(pm_id, str) or not pm_id.strip():
                raise ValidationError(
                    f"payment_method_ids[{i}] must be a non-empty string",
                    field=f"payment_method_ids[{i}]",
                    value=pm_id,
                )

    # At least one field must be provided for update
    if name is None and description is None and payment_method_ids is None:
        raise ValidationError(
            "At least one of name, description, or payment_method_ids must be provided",
            field="update_fields",
            value=None,
        )

    try:
        # Build request payload
        payload: dict[str, Any] = {}

        if name is not None:
            payload["name"] = name.strip()

        if description is not None:
            payload["description"] = description.strip()

        if payment_method_ids is not None:
            payload["payment_method_ids"] = [pm_id.strip() for pm_id in payment_method_ids]

        # Call JustiFi API to update payment method group
        result = await client.request("PATCH", f"/v1/payment_method_groups/{group_id}", data=payload)
        return standardize_response(result, "update_payment_method_group")

    except Exception as e:
        raise ToolError(
            f"Failed to update payment method group {group_id}: {str(e)}",
            error_type="PaymentMethodGroupUpdateError",
        ) from e


async def remove_payment_method_from_group(
    client: JustiFiClient, group_id: str, payment_method_id: str
) -> dict[str, Any]:
    """Remove a payment method from a payment method group.

    Args:
        client: JustiFi API client
        group_id: The unique identifier for the payment method group
        payment_method_id: The payment method ID to remove from the group

    Returns:
        Updated payment method group object after removal

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If payment method removal fails
    """
    if not group_id or not isinstance(group_id, str):
        raise ValidationError(
            "group_id is required and must be a non-empty string",
            field="group_id",
            value=group_id,
        )

    if not group_id.strip():
        raise ValidationError(
            "group_id cannot be empty or whitespace",
            field="group_id",
            value=group_id,
        )

    if not payment_method_id or not isinstance(payment_method_id, str):
        raise ValidationError(
            "payment_method_id is required and must be a non-empty string",
            field="payment_method_id",
            value=payment_method_id,
        )

    if not payment_method_id.strip():
        raise ValidationError(
            "payment_method_id cannot be empty or whitespace",
            field="payment_method_id",
            value=payment_method_id,
        )

    try:
        # Call JustiFi API to remove payment method from group
        result = await client.request(
            "DELETE", f"/v1/payment_method_groups/{group_id}/payment_methods/{payment_method_id}"
        )
        return standardize_response(result, "remove_payment_method_from_group")

    except Exception as e:
        raise ToolError(
            f"Failed to remove payment method {payment_method_id} from group {group_id}: {str(e)}",
            error_type="PaymentMethodGroupRemovalError",
        ) from e
