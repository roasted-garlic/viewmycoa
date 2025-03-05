#!/usr/bin/env python
"""
Simple test script to verify Square credential handling via the public debug endpoint.
"""
import requests
import json

def test_square_public_debug():
    """Test the public Square debug endpoint"""
    print("Testing public Square debug endpoint...")
    
    # Define the base URL - use localhost:3000 for direct testing
    BASE_URL = "http://localhost:3000"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Request the debug endpoint directly (no auth required)
    response = session.get(f"{BASE_URL}/api/debug/square-test")
    
    # Handle the debug response
    if response.status_code == 200:
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Check credentials 
            if data.get("credentials_check", {}).get("credentials_returned"):
                print("\nCredentials method is working correctly!")
            else:
                print("\nCredentials method is NOT working correctly!")
                
            # Check headers
            if data.get("headers_check", {}).get("has_auth_header"):
                print("Headers have authorization token - Square API should work!")
            else:
                print("Headers do NOT have authorization token - Square API will fail!")
                
        except ValueError:
            print(f"Failed to parse JSON from response: {response.text[:100]}...")
    else:
        print(f"Failed with status code {response.status_code}")
        print(f"Response: {response.text[:100]}...")

if __name__ == "__main__":
    test_square_public_debug()