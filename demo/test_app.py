#!/usr/bin/env python3
"""
Test script to demonstrate the bug in the FastAPI app.

This script sends requests to the /api/data endpoint with and without
the bug-triggering header to show the difference in behavior.
"""

import time

import httpx


def test_normal_request():
    """Test normal request without bug trigger."""
    print("\n" + "="*60)
    print("TEST 1: Normal Request (No Bug)")
    print("="*60)

    try:
        response = httpx.get("http://localhost:8000/api/data")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("[SUCCESS] Request successful")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")


def test_bug_trigger():
    """Test request with bug-triggering header."""
    print("\n" + "="*60)
    print("TEST 2: Bug Trigger Request (X-Trigger-Bug: true)")
    print("="*60)

    try:
        response = httpx.get(
            "http://localhost:8000/api/data",
            headers={"X-Trigger-Bug": "true"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 500:
            print("[SUCCESS] Bug triggered successfully (500 error as expected)")
            print("[INFO] Check app_logs.txt for error details")
        else:
            print("[WARNING] Expected 500 error but got different status")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")


def test_health_check():
    """Test health check endpoint."""
    print("\n" + "="*60)
    print("TEST 3: Health Check")
    print("="*60)

    try:
        response = httpx.get("http://localhost:8000/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("[SUCCESS] Health check successful")
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")


if __name__ == "__main__":
    print("\nStarting FastAPI App Tests")
    print("Make sure the app is running: python app.py")

    # Wait a moment for the app to be ready
    time.sleep(1)

    # Run tests
    test_health_check()
    test_normal_request()
    test_bug_trigger()

    print("\n" + "="*60)
    print("Tests completed! Check app_logs.txt for detailed logs.")
    print("="*60 + "\n")
