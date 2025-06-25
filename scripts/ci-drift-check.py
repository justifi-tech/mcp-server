#!/usr/bin/env python3
"""
CI-specific JustiFi API Drift Detection Script

This script is designed for GitHub Actions CI/CD workflows.
It downloads the latest JustiFi OpenAPI spec, compares it with the stored version,
and outputs GitHub Actions-compatible results.

Usage:
    python scripts/ci-drift-check.py

Outputs:
    - Sets GitHub Actions outputs via $GITHUB_OUTPUT
    - Exits with code 0 for no changes, 1 for critical changes
    - Prints detailed analysis to stdout
"""

import json
import os
import sys
import requests
import yaml
from pathlib import Path
from deepdiff import DeepDiff

# Our implemented endpoints that we need to monitor
MONITORED_ENDPOINTS = {
    # Payment endpoints (5 tools)
    "POST /payments": "create_payment",
    "GET /payments/{id}": "retrieve_payment", 
    "GET /payments": "list_payments",
    "POST /payments/{id}/refunds": "refund_payment",
    "GET /payments/{id}/refunds": "list_refunds",
    
    # Payment method endpoints (2 tools)
    "POST /payment_methods": "create_payment_method",
    "GET /payment_methods/{token}": "retrieve_payment_method",
    
    # Payout endpoints (2 tools)
    "GET /payouts/{id}": "retrieve_payout",
    "GET /payouts": "list_payouts",
    
    # Balance transaction endpoints (1 tool)
    "GET /balance_transactions": "list_balance_transactions"
}

JUSTIFI_OPENAPI_URL = "https://docs.justifi.tech/redocusaurus/plugin-redoc-0.yaml"
STORED_SPEC_PATH = Path("docs/justifi-openapi.yaml")

def set_github_output(key: str, value: str):
    """Set GitHub Actions output variable"""
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{key}={value}\n")
    else:
        print(f"::set-output name={key}::{value}")

def download_latest_spec() -> dict:
    """Download the latest JustiFi OpenAPI specification"""
    print("🌐 Downloading latest JustiFi OpenAPI specification...")
    
    try:
        response = requests.get(JUSTIFI_OPENAPI_URL, timeout=30)
        response.raise_for_status()
        spec = yaml.safe_load(response.text)
        print(f"✅ Downloaded latest OpenAPI spec ({len(response.text.splitlines())} lines)")
        return spec
    except requests.RequestException as e:
        print(f"❌ Failed to download OpenAPI spec: {e}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Failed to parse OpenAPI spec: {e}")
        return None

def load_stored_spec() -> dict:
    """Load the stored OpenAPI specification"""
    if not STORED_SPEC_PATH.exists():
        print(f"❌ Stored spec not found at {STORED_SPEC_PATH}")
        return None
    
    try:
        with open(STORED_SPEC_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading stored spec: {e}")
        return None

def extract_endpoint_info(spec: dict, endpoint_key: str) -> dict:
    """Extract endpoint information from OpenAPI spec"""
    if not spec or 'paths' not in spec:
        return None
        
    method, path = endpoint_key.split(' ', 1)
    method = method.lower()
    
    # Handle parameterized paths - try multiple variations
    path_variations = [
        path,
        path.replace('{id}', '{payment_id}').replace('{token}', '{payment_method_token}'),
        path.replace('{id}', '{paymentId}').replace('{token}', '{paymentMethodToken}'),
    ]
    
    for openapi_path in spec['paths']:
        for path_var in path_variations:
            # Try exact match
            if openapi_path == path_var:
                path_info = spec['paths'][openapi_path]
                if method in path_info:
                    return path_info[method]
            
            # Try normalized comparison
            normalized_spec_path = openapi_path.replace('{payment_id}', '{id}').replace('{payment_method_token}', '{token}')
            normalized_spec_path = normalized_spec_path.replace('{paymentId}', '{id}').replace('{paymentMethodToken}', '{token}')
            
            if normalized_spec_path == path:
                path_info = spec['paths'][openapi_path]
                if method in path_info:
                    return path_info[method]
    
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
            print(f"   ⚠️  Not found in either spec")
            continue
        
        if stored_endpoint is None and latest_endpoint is not None:
            critical_changes.append(f"🆕 NEW: {endpoint} was added to the API")
            changes_found = True
            print(f"   🆕 NEW endpoint added!")
            continue
        
        if stored_endpoint is not None and latest_endpoint is None:
            critical_changes.append(f"🚨 REMOVED: {endpoint} was removed from the API")
            changes_found = True
            print(f"   🚨 ENDPOINT REMOVED!")
            continue
        
        # Compare endpoint details
        if stored_endpoint != latest_endpoint:
            diff = DeepDiff(stored_endpoint, latest_endpoint, ignore_order=True)
            if diff:
                changes_found = True
                critical_changes.append(f"🔄 CHANGED: {endpoint} has modifications")
                print(f"   🔄 Changes detected:")
                print(f"      {json.dumps(diff, indent=6, default=str)}")
        else:
            print(f"   ✅ No changes detected")
    
    return changes_found, critical_changes, warnings

def save_latest_spec(latest_spec: dict):
    """Save the latest spec for potential updating"""
    try:
        with open('justifi-openapi-latest.yaml', 'w') as f:
            yaml.dump(latest_spec, f, default_flow_style=False, sort_keys=False)
        print("✅ Latest spec saved for potential update")
    except Exception as e:
        print(f"❌ Failed to save latest spec: {e}")

def main():
    """Main CI drift check function"""
    print("🔍 JustiFi API Drift Detection (CI Mode)")
    print("=" * 50)
    
    # Load specs
    print("📥 Loading OpenAPI specifications...")
    stored_spec = load_stored_spec()
    latest_spec = download_latest_spec()
    
    if not latest_spec:
        print("❌ Cannot proceed without latest spec")
        set_github_output("CHANGES_DETECTED", "error")
        set_github_output("SUMMARY", "Failed to download latest OpenAPI spec")
        sys.exit(1)
    
    if not stored_spec:
        print("⚠️  No stored spec found - treating as initial setup")
        save_latest_spec(latest_spec)
        set_github_output("CHANGES_DETECTED", "false")
        set_github_output("CRITICAL_CHANGES", "0")
        set_github_output("SUMMARY", "Initial setup - no stored spec to compare")
        sys.exit(0)
    
    # Analyze changes
    changes_found, critical_changes, warnings = analyze_endpoint_changes(
        stored_spec, latest_spec
    )
    
    # Save latest spec for potential update
    save_latest_spec(latest_spec)
    
    # Print summary
    print(f"\n{'='*50}")
    print("📊 DRIFT ANALYSIS SUMMARY")
    print(f"{'='*50}")
    
    if not changes_found:
        print("✅ No changes detected in monitored endpoints")
        print("🎯 All 10 JustiFi MCP tools remain compatible")
        
        # Set GitHub Actions outputs
        set_github_output("CHANGES_DETECTED", "false")
        set_github_output("CRITICAL_CHANGES", "0")
        set_github_output("SUMMARY", "No changes detected - all tools remain compatible")
        
        print("\n🎉 All checks passed!")
        sys.exit(0)
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
        
        # Set GitHub Actions outputs
        set_github_output("CHANGES_DETECTED", "true")
        set_github_output("CRITICAL_CHANGES", str(len(critical_changes)))
        set_github_output("SUMMARY", "API changes detected in monitored endpoints")
        
        # Create summary for issue creation
        changes_summary = "\n".join(critical_changes)
        if warnings:
            changes_summary += "\n\nWarnings:\n" + "\n".join(warnings)
        
        set_github_output("CHANGES_DETAIL", changes_summary)
        
        print(f"\n💥 Exiting with error code due to {len(critical_changes)} critical changes")
        sys.exit(1)

if __name__ == "__main__":
    main() 