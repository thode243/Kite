import json
from kiteconnect import KiteConnect

# Load credentials
with open("config.json") as f:
    creds = json.load(f)

api_key = creds["api_key"]
api_secret = creds["api_secret"]

kite = KiteConnect(api_key=api_key)

print("Login URL:", kite.login_url())
request_token = input("Enter the request token you got from the URL: ")

data = kite.generate_session(request_token, api_secret=api_secret)

# Save only required fields
with open("access_token.json", "w") as f:
    json.dump({
        "access_token": data["access_token"],
        "user_id": data["user_id"]
    }, f, indent=2)

print("✅ Access token saved successfully in access_token.json")
