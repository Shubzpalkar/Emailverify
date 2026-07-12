import requests
import time

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def test_password_reset():
    email = "admin@example.com"
    print(f"--- Testing Password Reset Flow for {email} ---")
    
    # 1. Request forgot password
    print("Step 1: Requesting reset token...")
    res = requests.post(f"{BASE_URL}/auth/forgot-password", json={"email": email})
    print(f"Response: {res.json()}")
    
    print("\nIMPORTANT: Look at the backend terminal to get the reset link!")
    token = input("Please enter the 'token' value from the URL in the terminal: ")
    
    # 2. Reset password
    new_password = "newpassword123"
    print(f"\nStep 2: Resetting password to '{new_password}'...")
    res = requests.post(f"{BASE_URL}/auth/reset-password", json={"token": token, "new_password": new_password})
    print(f"Response: {res.json()}")
    
    # 3. Verify login with new password
    print("\nStep 3: Verifying login with new password...")
    login_data = {
        "username": email,
        "password": new_password
    }
    res = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if res.status_code == 200:
        print("✅ Login successful with new password!")
    else:
        print(f"❌ Login failed: {res.json()}")

    # 4. Optional: Reset back to 'admin' for convenience
    print("\nResetting back to 'admin' for convenience...")
    requests.post(f"{BASE_URL}/auth/reset-password", json={"token": token, "new_password": "admin"})
    print("Done.")

if __name__ == "__main__":
    test_password_reset()
