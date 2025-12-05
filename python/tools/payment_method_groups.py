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


def _validate_sub_account_id(sub_account_id: str) -> None:
    """Validate sub_account_id parameter.

    Args:
        sub_account_id: The sub account ID to validate

    Raises:
        ValidationError: If sub_account_id is invalid
    """
    if not sub_account_id or not isinstance(sub_account_id, str):
        raise ValidationError(
            "sub_account_id is required and must be a non-empty string",
            field="sub_account_id",
            value=sub_account_id,
        )

    if not sub_account_id.strip():
        raise ValidationError(
            "sub_account_id cannot be empty or whitespace",
            field="sub_account_id",
            value=sub_account_id,
        )


async def create_payment_method_group(
    client: JustiFiClient,
    sub_account_id: str,
    name: str,
    description: str | None = None,
    payment_method_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new payment method group to organize tokenized payment methods.

    Use this to organize a customer's saved payment methods into logical groups.
    Groups help manage multiple payment methods per customer—for example, separating
    personal cards from business cards, or organizing by billing purpose. Useful for
    subscription billing or marketplaces where customers have multiple payment options.

    Related tools:
    - Use `list_payment_method_groups` to see existing groups for a sub account
    - Use `retrieve_payment_method_group` to see group details and members
    - Use `update_payment_method_group` to modify group properties or members
    - Use `remove_payment_method_from_group` to remove a specific payment method

    Args:
        client: JustiFi API client
        sub_account_id: The sub account ID this group belongs to (e.g., 'acc_ABC123XYZ').
            Required to scope the group to a specific merchant.
        name: Display name for the payment method group (e.g., 'Primary Cards', 'Work Accounts').
        description: Optional description explaining the group's purpose.
        payment_method_ids: Optional list of payment method tokens to add initially.
            Can also add payment methods later via `update_payment_method_group`.

    Returns:
        Payment method group object containing:
        - id: Unique group identifier
        - name: Group display name
        - description: Group description (if provided)
        - payment_methods: Array of payment method objects in the group
        - created_at: ISO 8601 timestamp

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If group creation fails
    """
    _validate_sub_account_id(sub_account_id)

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
            payload["payment_method_ids"] = [
                pm_id.strip() for pm_id in payment_method_ids
            ]

        # Call JustiFi API to create payment method group
        result = await client.request(
            "POST",
            "/v1/payment_method_groups",
            data=payload,
            sub_account_id=sub_account_id.strip(),
        )
        return standardize_response(result, "create_payment_method_group")

    except Exception as e:
        raise ToolError(
            f"Failed to create payment method group: {str(e)}",
            error_type="PaymentMethodGroupCreationError",
        ) from e


async def list_payment_method_groups(
    client: JustiFiClient,
    sub_account_id: str,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List payment method groups for a sub account with cursor-based pagination.

    Use this to see all payment method groups created for a specific merchant.
    Groups organize customers' saved payment methods for easier management.

    Pagination: Use `page_info.end_cursor` as `after_cursor` to fetch subsequent pages.

    Related tools:
    - Use `retrieve_payment_method_group` with a group ID for complete details
    - Use `create_payment_method_group` to create new groups
    - Use `retrieve_payment_method` to see individual payment method details

    Args:
        client: JustiFi API client
        sub_account_id: The sub account ID to list groups for (e.g., 'acc_ABC123XYZ').
            Required to scope results to a specific merchant.
        limit: Number of groups to return per page (1-100, default: 25).
        after_cursor: Pagination cursor for fetching the next page of results.
        before_cursor: Pagination cursor for fetching the previous page of results.

    Returns:
        Object containing:
        - data: Array of payment method group objects with id, name, description
        - page_info: Pagination metadata for navigating through results

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If group listing fails
    """
    # Validate sub_account_id
    _validate_sub_account_id(sub_account_id)

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
        result = await client.request(
            "GET",
            "/v1/payment_method_groups",
            params=params,
            sub_account_id=sub_account_id.strip(),
        )
        return standardize_response(result, "list_payment_method_groups")

    except Exception as e:
        raise ToolError(
            f"Failed to list payment method groups: {str(e)}",
            error_type="PaymentMethodGroupListError",
        ) from e


async def retrieve_payment_method_group(
    client: JustiFiClient, sub_account_id: str, group_id: str
) -> dict[str, Any]:
    """Retrieve detailed information about a payment method group including its members.

    Use this to see all payment methods within a group, along with the group's
    metadata. Essential for displaying a customer's organized payment options
    or verifying group membership before processing a payment.

    Related tools:
    - Use `list_payment_method_groups` first to find group IDs
    - Use `retrieve_payment_method` for detailed info on a specific payment method
    - Use `update_payment_method_group` to modify group members or properties
    - Use `remove_payment_method_from_group` to remove a specific payment method

    Args:
        client: JustiFi API client
        sub_account_id: The sub account ID that owns the group (e.g., 'acc_ABC123XYZ').
        group_id: The unique identifier for the payment method group (e.g., 'pmg_ABC123XYZ').
            Obtain from `list_payment_method_groups`.

    Returns:
        Payment method group object containing:
        - id: Unique group identifier
        - name: Group display name
        - description: Group description
        - payment_methods: Array of full payment method objects in this group
        - created_at: ISO 8601 timestamp
        - updated_at: Last modification timestamp

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If group retrieval fails
    """
    _validate_sub_account_id(sub_account_id)

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
        result = await client.request(
            "GET",
            f"/v1/payment_method_groups/{group_id}",
            sub_account_id=sub_account_id.strip(),
        )
        return standardize_response(result, "retrieve_payment_method_group")

    except Exception as e:
        raise ToolError(
            f"Failed to retrieve payment method group {group_id}: {str(e)}",
            error_type="PaymentMethodGroupRetrievalError",
        ) from e


async def update_payment_method_group(
    client: JustiFiClient,
    sub_account_id: str,
    group_id: str,
    name: str | None = None,
    description: str | None = None,
    payment_method_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Update an existing payment method group's properties or members.

    Use this to rename a group, update its description, or replace its entire
    payment method membership. To remove a single payment method without affecting
    others, use `remove_payment_method_from_group` instead.

    Note: When providing `payment_method_ids`, this REPLACES the entire membership.
    Any payment methods not in the new list will be removed from the group.

    Related tools:
    - Use `retrieve_payment_method_group` to see current group state before updating
    - Use `remove_payment_method_from_group` to remove just one payment method
    - Use `list_payment_method_groups` to find group IDs

    Args:
        client: JustiFi API client
        sub_account_id: The sub account ID that owns the group (e.g., 'acc_ABC123XYZ').
        group_id: The unique identifier for the payment method group (e.g., 'pmg_ABC123XYZ').
        name: New display name for the group. Only updates if provided.
        description: New description for the group. Only updates if provided.
        payment_method_ids: Complete list of payment method tokens that should be in the group.
            This REPLACES all existing members—omitted payment methods will be removed.

    Returns:
        Updated payment method group object containing:
        - id: Unique group identifier
        - name: Updated group name
        - description: Updated description
        - payment_methods: Array of payment method objects now in the group
        - updated_at: Timestamp of this update

    Raises:
        ValidationError: If parameters are invalid or no update fields provided
        ToolError: If group update fails
    """
    _validate_sub_account_id(sub_account_id)

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
            payload["payment_method_ids"] = [
                pm_id.strip() for pm_id in payment_method_ids
            ]

        # Call JustiFi API to update payment method group
        result = await client.request(
            "PATCH",
            f"/v1/payment_method_groups/{group_id}",
            data=payload,
            sub_account_id=sub_account_id.strip(),
        )
        return standardize_response(result, "update_payment_method_group")

    except Exception as e:
        raise ToolError(
            f"Failed to update payment method group {group_id}: {str(e)}",
            error_type="PaymentMethodGroupUpdateError",
        ) from e


async def remove_payment_method_from_group(
    client: JustiFiClient, sub_account_id: str, group_id: str, payment_method_id: str
) -> dict[str, Any]:
    """Remove a single payment method from a group without affecting other members.

    Use this to remove one payment method from a group while keeping all other
    members intact. The payment method itself is not deleted—it's just removed
    from this group's membership. Use this instead of `update_payment_method_group`
    when you only need to remove one item.

    Related tools:
    - Use `retrieve_payment_method_group` to see current group members
    - Use `update_payment_method_group` to replace the entire membership list
    - Use `retrieve_payment_method` to verify the payment method exists

    Args:
        client: JustiFi API client
        sub_account_id: The sub account ID that owns the group (e.g., 'acc_ABC123XYZ').
        group_id: The unique identifier for the payment method group (e.g., 'pmg_ABC123XYZ').
        payment_method_id: The payment method token to remove (e.g., 'pm_ABC123XYZ').
            The payment method must currently be in the group.

    Returns:
        Updated payment method group object containing:
        - id: Unique group identifier
        - payment_methods: Array of remaining payment method objects
        - updated_at: Timestamp of this removal

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If payment method removal fails (e.g., not in group)
    """
    _validate_sub_account_id(sub_account_id)

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
            "DELETE",
            f"/v1/payment_method_groups/{group_id}/payment_methods/{payment_method_id}",
            sub_account_id=sub_account_id.strip(),
        )
        return standardize_response(result, "remove_payment_method_from_group")

    except Exception as e:
        raise ToolError(
            f"Failed to remove payment method {payment_method_id} from group {group_id}: {str(e)}",
            error_type="PaymentMethodGroupRemovalError",
        ) from e
