#!/usr/bin/env python3
import requests
import json
import os
import sys

# Set up our base URL
BASE_URL = "http://localhost:3000"

def test_debug_endpoint():
    """Test the debug/square-credentials endpoint"""
    
    # We need to log in first 
    session = requests.Session()
    
    # Step 1: Hit the debug endpoint (may fail if authentication is required)
    print("Testing debug endpoint...")
    response = session.get(f"{BASE_URL}/debug/square-credentials")
    
    # Check if authentication is required
    if response.status_code == 401 or response.status_code == 302:
        print("Authentication required. Attempting login...")
        
        # Get CSRF token from login page
        login_page = session.get(f"{BASE_URL}/login")
        import re
        csrf_token = re.search(r'name="csrf_token" value="(.+?)"', login_page.text)
        
        if not csrf_token:
            print("Failed to get CSRF token, page content:")
            print(login_page.text[:200])
            return
            
        csrf_token = csrf_token.group(1)
        print(f"Found CSRF token: {csrf_token}")
        
        # Log in with admin credentials
        login_data = {
            "username": "admin",
            "password": "admin",  # Default password, adjust as needed
            "csrf_token": csrf_token
        }
        
        login_response = session.post(f"{BASE_URL}/login", data=login_data)
        
        if login_response.status_code != 200 and "admin" not in login_response.text:
            print(f"Login failed with status code {login_response.status_code}")
            return
            
        print("Login successful, retrying debug endpoint...")
        
        # Try the debug endpoint again
        response = session.get(f"{BASE_URL}/debug/square-credentials")
    
    # Handle the debug response
    if response.status_code == 200:
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Check if credentials are working
            if data.get("credentials_method", {}).get("credentials_returned"):
                print("\nCredentials method is working correctly!")
            else:
                print("\nCredentials method is NOT working correctly!")
                
            if data.get("headers_check", {}).get("has_authorization"):
                print("Headers have authorization token - Square API should work!")
            else:
                print("Headers do NOT have authorization token - Square API will fail!")
                
        except ValueError:
            print(f"Failed to parse JSON from response: {response.text[:100]}...")
    else:
        print(f"Failed with status code {response.status_code}")
        print(f"Response: {response.text[:100]}...")

if __name__ == "__main__":
    test_debug_endpoint()