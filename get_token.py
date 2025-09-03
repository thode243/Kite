# get_token.py
from kiteconnect import KiteConnect
import json, os

api_key = os.getenv("ZERODHA_API_KEY")
api_secret = os.getenv("ZERODHA_API_SECRET")

kite = KiteConnect(api_key=api_key)

# Step 1: Login URL
print("Login URL:", kite.login_url())
print("👉 Open the above URL, login, and copy the request_token from the redirect URL.")

# Step 2: Paste request_token here after login
request_token = input("Enter request_token: ")

data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data["access_token"]

# Save access_token for later use
with open("access_token.json", "w") as f:
    json.dump({"access_token": access_token}, f)

print("✅ Saved access_token.json")
