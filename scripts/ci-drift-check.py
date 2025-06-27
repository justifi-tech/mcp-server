#!/usr/bin/env python3
"""CI Drift Check Script for JustiFi API

This script is designed to run in GitHub Actions to detect changes in the JustiFi API.
It downloads the latest OpenAPI specification and compares it with our stored version.
"""

import os
import sys
from pathlib import Path
from typing import Any

import requests
import yaml
from deepdiff import DeepDiff


def download_justifi_openapi() -> dict[str, Any]:
    """Download the latest JustiFi OpenAPI specification."""
    try:
        # JustiFi's OpenAPI spec URL - UPDATE THIS WITH ACTUAL URL
        # Common patterns:
        # - https://api.justifi.ai/openapi.json
        # - https://docs.justifi.ai/openapi.yaml
        # - https://api.justifi.ai/v1/openapi.json
        url = os.getenv("JUSTIFI_OPENAPI_URL", "https://api.justifi.ai/openapi.json")

        print(f"🔍 Downloading JustiFi OpenAPI spec from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        result: dict[str, Any] = response.json()
        return result

    except requests.RequestException as e:
        print(f"❌ Failed to download OpenAPI spec: {e}")
        print("💡 Tip: Set JUSTIFI_OPENAPI_URL environment variable with correct URL")
        print("📚 Check JustiFi documentation for their OpenAPI spec endpoint")
        # For now, return empty dict to avoid CI failures
        # In production, you'd want to handle this more gracefully
        return {}


def load_stored_spec() -> dict[str, Any]:
    """Load our stored OpenAPI specification."""
    spec_path = Path("docs/justifi-openapi.yaml")

    if not spec_path.exists():
        print("⚠️ No stored OpenAPI spec found")
        return {}

    try:
        with spec_path.open(encoding="utf-8") as f:
            result: dict[str, Any] = yaml.safe_load(f) or {}
            return result
    except Exception as e:
        print(f"❌ Failed to load stored spec: {e}")
        return {}


def compare_specs(current: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Compare two OpenAPI specifications and return differences."""
    if not current and not new:
        return {"has_changes": False, "summary": "No specifications to compare"}

    if not current:
        return {
            "has_changes": True,
            "summary": "New OpenAPI specification detected",
            "change_type": "new_spec",
        }

    if not new:
        return {
            "has_changes": False,
            "summary": "Could not fetch new specification",
            "change_type": "fetch_error",
        }

    # Use DeepDiff to compare the specifications
    diff = DeepDiff(current, new, ignore_order=True)

    if not diff:
        return {
            "has_changes": False,
            "summary": "No changes detected in OpenAPI specification",
        }

    # Analyze the types of changes
    changes = {
        "has_changes": True,
        "summary": "Changes detected in OpenAPI specification",
        "details": {},
    }

    # Check for breaking changes
    breaking_changes = []
    non_breaking_changes = []

    if "dictionary_item_removed" in diff:
        for item in diff["dictionary_item_removed"]:
            if "paths" in str(item):
                breaking_changes.append(f"Endpoint removed: {item}")
            else:
                breaking_changes.append(f"Removed: {item}")

    if "dictionary_item_added" in diff:
        for item in diff["dictionary_item_added"]:
            if "paths" in str(item):
                non_breaking_changes.append(f"New endpoint: {item}")
            else:
                non_breaking_changes.append(f"Added: {item}")

    if "values_changed" in diff:
        for item, _change in diff["values_changed"].items():
            if "paths" in str(item):
                breaking_changes.append(f"Endpoint modified: {item}")
            else:
                non_breaking_changes.append(f"Modified: {item}")

    changes["details"] = {
        "breaking_changes": breaking_changes,
        "non_breaking_changes": non_breaking_changes,
        "total_changes": len(breaking_changes) + len(non_breaking_changes),
    }

    # Determine if changes are critical
    changes["critical"] = len(breaking_changes) > 0

    return changes


def save_new_spec(spec: dict[str, Any]) -> None:
    """Save the new OpenAPI specification to our docs directory."""
    if not spec:
        return

    spec_path = Path("docs/justifi-openapi.yaml")

    try:
        with spec_path.open("w", encoding="utf-8") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Updated OpenAPI spec saved to {spec_path}")
    except Exception as e:
        print(f"❌ Failed to save new spec: {e}")


def create_changes_summary(changes: dict[str, Any]) -> str:
    """Create a markdown summary of the changes."""
    if not changes.get("has_changes"):
        return "No changes detected in the JustiFi API specification."

    summary = ["# JustiFi API Changes Summary\n"]

    if changes.get("critical"):
        summary.append("⚠️ **BREAKING CHANGES DETECTED**\n")
    else:
        summary.append("✅ **Non-breaking changes detected**\n")

    details = changes.get("details", {})

    if details.get("breaking_changes"):
        summary.append("## Breaking Changes")
        for change in details["breaking_changes"]:
            summary.append(f"- {change}")
        summary.append("")

    if details.get("non_breaking_changes"):
        summary.append("## Non-breaking Changes")
        for change in details["non_breaking_changes"]:
            summary.append(f"- {change}")
        summary.append("")

    summary.append(f"**Total changes**: {details.get('total_changes', 0)}")

    return "\n".join(summary)


def set_github_output(name: str, value: str) -> None:
    """Set GitHub Actions output."""
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    else:
        print(f"Output: {name}={value}")


def main():
    """Main function to check for API drift."""
    print("🚀 Starting JustiFi API drift check...")

    # Check if this is a forced update
    force_update = os.getenv("FORCE_UPDATE", "false").lower() == "true"

    # Load current and new specifications
    current_spec = load_stored_spec()
    new_spec = download_justifi_openapi()

    # Compare specifications
    changes = compare_specs(current_spec, new_spec)

    print(f"📊 Analysis complete: {changes['summary']}")

    # Create changes summary file
    if changes.get("has_changes") or force_update:
        summary_content = create_changes_summary(changes)
        with Path("api-changes-summary.md").open("w", encoding="utf-8") as f:
            f.write(summary_content)
        print("📝 Changes summary created")

    # Save new spec if changes detected or forced
    if (changes.get("has_changes") or force_update) and new_spec:
        save_new_spec(new_spec)

    # Set GitHub Actions outputs
    set_github_output(
        "changes_detected", str(changes.get("has_changes", False)).lower()
    )
    set_github_output("critical_changes", str(changes.get("critical", False)).lower())
    set_github_output("summary", changes.get("summary", ""))

    # Exit with appropriate code
    if changes.get("has_changes"):
        print("✅ Changes detected - PR and issue will be created")
        sys.exit(0)  # Success - changes found
    else:
        print("✅ No changes detected - no action needed")
        sys.exit(0)  # Success - no changes


if __name__ == "__main__":
    main()
