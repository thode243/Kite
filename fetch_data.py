# fetch_data.py
# import json, time
# from kiteconnect import KiteTicker

import os
import json
from kiteconnect import KiteConnect

api_key = os.getenv("ZERODHA_API_KEY")
api_secret = os.getenv("ZERODHA_API_SECRET")

kite = KiteConnect(api_key=api_key)

# You’ll still need a request_token / access_token flow here,
# but at least `os` error is fixed now.


api_key = os.getenv("ZERODHA_API_KEY")

# Load saved access_token
with open("access_token.json") as f:
    access_token = json.load(f)["access_token"]

kws = KiteTicker(api_key, access_token)

def on_ticks(ws, ticks):
    """Save ticks into JSON file"""
    with open("data/nifty.json", "w") as f:
        json.dump(ticks, f, indent=2)
    print("Updated nifty.json at", time.strftime("%H:%M:%S"))

def on_connect(ws, response):
    """Subscribe to instruments"""
    # Example: NIFTY 50 spot instrument_token
    ws.subscribe([738561])
    ws.set_mode(ws.MODE_FULL, [738561])

def on_close(ws, code, reason):
    print("❌ Connection closed:", code, reason)

# Assign callbacks
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Start streaming
kws.connect(threaded=True)

# Keep running forever
while True:
    time.sleep(1)
