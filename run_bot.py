import os
from kiteconnect import KiteConnect

api_key = os.environ["KITE_API_KEY"]
api_secret = os.environ["KITE_API_SECRET"]
access_token = os.environ.get("ACCESS_TOKEN")  # must update daily

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

profile = kite.profile()
print("Logged in as:", profile["user_name"])
