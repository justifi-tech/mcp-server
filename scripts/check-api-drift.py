#!/usr/bin/env python3
"""JustiFi API Drift Detection Script

This script checks for changes in the JustiFi OpenAPI specification
that could affect our MCP tools. It can be run locally for testing
or used in CI/CD pipelines.

Usage:
    python scripts/check-api-drift.py [--update-spec]

Options:
    --update-spec    Update the stored OpenAPI spec if no breaking changes
"""

import argparse
import json
import sys
from pathlib import Path

import requests
import yaml
from deepdiff import DeepDiff

# Our implemented endpoints that we need to monitor
MONITORED_ENDPOINTS = {
    # Payment endpoints (4 tools) - REMOVED list_refunds (endpoint doesn't exist)
    "POST /payments": "create_payment",
    "GET /payments/{id}": "retrieve_payment",
    "GET /payments": "list_payments",
    "POST /payments/{id}/refunds": "refund_payment",
    # Payment method endpoints (2 tools)
    "POST /payment_methods": "create_payment_method",
    "GET /payment_methods/{token}": "retrieve_payment_method",
    # Payout endpoints (2 tools)
    "GET /payouts/{id}": "retrieve_payout",
    "GET /payouts": "list_payouts",
    # Balance transaction endpoints (1 tool)
    "GET /balance_transactions": "list_balance_transactions",
}

JUSTIFI_OPENAPI_URL = "https://docs.justifi.tech/redocusaurus/plugin-redoc-0.yaml"
STORED_SPEC_PATH = Path("docs/justifi-openapi.yaml")


def download_latest_spec() -> dict | None:
    """Download the latest JustiFi OpenAPI specification"""
    print("🌐 Downloading latest JustiFi OpenAPI specification...")

    try:
        response = requests.get(JUSTIFI_OPENAPI_URL, timeout=30)
        response.raise_for_status()
        spec = yaml.safe_load(response.text)
        print(
            f"✅ Downloaded latest OpenAPI spec ({len(response.text.splitlines())} lines)"
        )
        return spec  # type: ignore[no-any-return]
    except requests.RequestException as e:
        print(f"❌ Failed to download OpenAPI spec: {e}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Failed to parse OpenAPI spec: {e}")
        return None


def load_stored_spec() -> dict | None:
    """Load the stored OpenAPI specification"""
    if not STORED_SPEC_PATH.exists():
        print(f"⚠️  Stored spec not found at {STORED_SPEC_PATH}")
        return None

    try:
        with STORED_SPEC_PATH.open() as f:
            return yaml.safe_load(f)  # type: ignore[no-any-return]
    except Exception as e:
        print(f"❌ Error loading stored spec: {e}")
        return None


def extract_endpoint_info(spec: dict, endpoint_key: str) -> dict | None:
    """Extract endpoint information from OpenAPI spec"""
    if not spec or "paths" not in spec:
        return None

    method, path = endpoint_key.split(" ", 1)
    method = method.lower()

    # Handle parameterized paths - try multiple variations
    path_variations = [
        path,
        path.replace("{id}", "{payment_id}").replace(
            "{token}", "{payment_method_token}"
        ),
        path.replace("{id}", "{paymentId}").replace("{token}", "{paymentMethodToken}"),
    ]

    for openapi_path in spec["paths"]:
        for path_var in path_variations:
            # Try exact match
            if openapi_path == path_var:
                path_info = spec["paths"][openapi_path]
                if method in path_info:
                    return path_info[method]  # type: ignore[no-any-return]

            # Try normalized comparison (remove parameter differences)
            normalized_spec_path = openapi_path.replace("{payment_id}", "{id}").replace(
                "{payment_method_token}", "{token}"
            )
            normalized_spec_path = normalized_spec_path.replace(
                "{paymentId}", "{id}"
            ).replace("{paymentMethodToken}", "{token}")

            if normalized_spec_path == path:
                path_info = spec["paths"][openapi_path]
                if method in path_info:
                    return path_info[method]  # type: ignore[no-any-return]

    return None


def analyze_endpoint_changes(stored_spec: dict, latest_spec: dict) -> tuple:
    """Analyze changes in monitored endpoints"""
    print("🔍 Analyzing OpenAPI spec changes...")

    changes_found = False
    critical_changes = []
    warnings = []

    for endpoint, tool_name in MONITORED_ENDPOINTS.items():
        print(f"\n📍 Checking {endpoint} ({tool_name})...")

        stored_endpoint = extract_endpoint_info(stored_spec, endpoint)
        latest_endpoint = extract_endpoint_info(latest_spec, endpoint)

        if stored_endpoint is None and latest_endpoint is None:
            warnings.append(f"⚠️  {endpoint} not found in either spec")
            print("   ⚠️  Not found in either spec")
            continue

        if stored_endpoint is None and latest_endpoint is not None:
            critical_changes.append(f"🆕 NEW: {endpoint} was added to the API")
            changes_found = True
            print("   🆕 NEW endpoint added!")
            continue

        if stored_endpoint is not None and latest_endpoint is None:
            critical_changes.append(f"🚨 REMOVED: {endpoint} was removed from the API")
            changes_found = True
            print("   🚨 ENDPOINT REMOVED!")
            continue

        # Compare endpoint details
        if stored_endpoint != latest_endpoint:
            diff = DeepDiff(stored_endpoint, latest_endpoint, ignore_order=True)
            if diff:
                changes_found = True
                critical_changes.append(f"🔄 CHANGED: {endpoint} has modifications")
                print("   🔄 Changes detected:")
                print(f"      {json.dumps(diff, indent=6, default=str)}")
        else:
            print("   ✅ No changes detected")

    return changes_found, critical_changes, warnings


def print_summary(changes_found: bool, critical_changes: list, warnings: list) -> None:
    """Print analysis summary"""
    print(f"\n{'='*60}")
    print("📊 JUSTIFI API DRIFT ANALYSIS SUMMARY")
    print(f"{'='*60}")

    if not changes_found:
        print("✅ No changes detected in monitored endpoints")
        print("🎯 All 9 JustiFi MCP tools remain compatible")
        print("🚀 Your MCP server is up to date!")
    else:
        print(f"⚠️  {len(critical_changes)} changes detected!")

        if critical_changes:
            print("\n🚨 CRITICAL CHANGES:")
            for change in critical_changes:
                print(f"   {change}")

        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"   {warning}")

        print("\n📋 RECOMMENDED ACTIONS:")
        print("   1. Review the changes above")
        print("   2. Update affected MCP tools if needed")
        print("   3. Run the full test suite: make test")
        print("   4. Update docs/justifi-openapi.yaml with latest spec")
        print("   5. Test with real API credentials")


def update_stored_spec(latest_spec: dict) -> bool:
    """Update the stored OpenAPI specification"""
    print(f"\n📝 Updating stored OpenAPI spec at {STORED_SPEC_PATH}...")

    try:
        # Ensure directory exists
        STORED_SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write the updated spec
        with STORED_SPEC_PATH.open("w") as f:
            yaml.dump(latest_spec, f, default_flow_style=False, sort_keys=False)

        print("✅ Stored OpenAPI spec updated successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to update stored spec: {e}")
        return False


def main() -> None:
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Check for JustiFi API drift that could affect MCP tools"
    )
    parser.add_argument(
        "--update-spec",
        action="store_true",
        help="Update the stored OpenAPI spec if no breaking changes",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    print("🔍 JustiFi API Drift Detection")
    print("=" * 40)

    # Load specs
    print("📥 Loading OpenAPI specifications...")
    stored_spec = load_stored_spec()
    latest_spec = download_latest_spec()

    if not latest_spec:
        print("❌ Cannot proceed without latest spec")
        sys.exit(1)

    if not stored_spec:
        print("⚠️  No stored spec found - treating as initial setup")
        if args.update_spec:
            update_stored_spec(latest_spec)
            print("✅ Initial OpenAPI spec stored")
        sys.exit(0)

    # Analyze changes
    changes_found, critical_changes, warnings = analyze_endpoint_changes(
        stored_spec, latest_spec
    )

    # Print summary
    print_summary(changes_found, critical_changes, warnings)

    # Update spec if requested and no critical changes
    if args.update_spec:
        if not critical_changes:
            update_stored_spec(latest_spec)
        else:
            print("\n❌ Not updating stored spec due to critical changes")
            print("   Review and resolve the changes first")

    # Exit with appropriate code
    if critical_changes:
        print(
            f"\n💥 Exiting with error code due to {len(critical_changes)} critical changes"
        )
        sys.exit(1)
    else:
        print("\n🎉 All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
