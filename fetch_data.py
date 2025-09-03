from kiteconnect import KiteConnect
import json, os, datetime

api_key = os.getenv("ZERODHA_API_KEY")
api_secret = os.getenv("ZERODHA_API_SECRET")

kite = KiteConnect(api_key=api_key)

# Step 1: You must log in manually to get request_token once per day
print("Login URL:", kite.login_url())

# ⚠️ Manual Step:
# 1. Open this URL in browser
# 2. Login with Zerodha
# 3. Copy request_token from redirected URL
# 4. Paste below
request_token = "PASTE_REQUEST_TOKEN_HERE"

data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data["access_token"]
kite.set_access_token(access_token)

# Example: Get NIFTY spot quote
nifty = kite.quote(["NSE:NIFTY 50"])
filename = "data/nifty.json"

with open(filename, "w") as f:
    json.dump(nifty, f, indent=2)

print(f"Saved {filename} at {datetime.datetime.now()}")
