# -----------------------------
# 1. Load Access Token
# -----------------------------


import os
from datetime import datetime
from kiteconnect import KiteConnect
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------
# 1. Load Access Token
# -----------------------------
ACCESS_TOKEN_FILE = "access_token.txt"
API_KEY = "API_KEY"  # put your Kite API key
API_SECRET = "API_SECRET"  # put your Kite API secret

if not os.path.exists(ACCESS_TOKEN_FILE):
    print("❌ Access token not found. Run access_token.py first.")
    exit()

with open(ACCESS_TOKEN_FILE, "r") as f:
    access_token = f.read().strip()

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(access_token)

# -----------------------------
# 2. Setup Google Sheets
# -----------------------------
SCOPE = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "credentials.json"  

creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
client = gspread.authorize(creds)

SHEET_NAME = "Kite Option Chain Data"
sheet = client.open(SHEET_NAME).sheet1

# -----------------------------
# 3. Load Existing OI Data
# -----------------------------
existing_values = sheet.get_all_values()
prev_oi_dict = {}

if existing_values:
    headers = existing_values[0]
    if "Strike" in headers and "Call OI" in headers and "Put OI" in headers:
        strike_col = headers.index("Strike")
        call_oi_col = headers.index("Call OI")
        put_oi_col = headers.index("Put OI")
        for row in existing_values[1:]:
            try:
                strike = float(row[strike_col])
                call_oi = int(row[call_oi_col]) if row[call_oi_col] else 0
                put_oi = int(row[put_oi_col]) if row[put_oi_col] else 0
                prev_oi_dict[strike] = {"call": call_oi, "put": put_oi}
            except:
                continue

# -----------------------------
# 4. Fetch Option Chain Data
# -----------------------------
expiry = "2025-09-16"
instruments = kite.instruments("NFO")

# All NIFTY options for given expiry
nifty_options = [i for i in instruments if i["name"] == "NIFTY" and i["expiry"].strftime("%Y-%m-%d") == expiry]

print(f"✅ Found {len(nifty_options)} NIFTY contracts for {expiry}")

# Group by strike
option_chain = {}
for inst in nifty_options:
    try:
        quote = kite.quote(inst["instrument_token"])
        ltp = quote[str(inst["instrument_token"])]["last_price"]
        oi = quote[str(inst["instrument_token"])].get("oi", 0)
        vol = quote[str(inst["instrument_token"])].get("volume", 0)

        strike = inst["strike"]
        typ = inst["instrument_type"]  # CE or PE

        if strike not in option_chain:
            option_chain[strike] = {"call": {}, "put": {}}

        if typ == "CE":
            prev_oi = prev_oi_dict.get(strike, {}).get("call", 0)
            option_chain[strike]["call"] = {
                "ltp": ltp,
                "oi": oi,
                "chg_oi": oi - prev_oi,
                "vol": vol
            }
        elif typ == "PE":
            prev_oi = prev_oi_dict.get(strike, {}).get("put", 0)
            option_chain[strike]["put"] = {
                "ltp": ltp,
                "oi": oi,
                "chg_oi": oi - prev_oi,
                "vol": vol
            }
    except Exception as e:
        print(f"⚠️ Error fetching {inst['tradingsymbol']}: {e}")

# -----------------------------
# 5. Prepare Rows
# -----------------------------
rows = []
for strike, data in sorted(option_chain.items()):
    call = data.get("call", {})
    put = data.get("put", {})
    rows.append([
        call.get("ltp", 0),
        call.get("oi", 0),
        call.get("chg_oi", 0),
        call.get("vol", 0),
        strike,
        expiry,
        put.get("ltp", 0),
        put.get("oi", 0),
        put.get("chg_oi", 0),
        put.get("vol", 0),
        ""  # VWAP placeholder
    ])

# -----------------------------
# 6. Write to Google Sheet
# -----------------------------
headers_row = [
    "Call LTP", "Call OI", "Call Chg OI", "Call Vol",
    "Strike", "Expiry",
    "Put LTP", "Put OI", "Put Chg OI", "Put Vol",
    "VWAP"
]

sheet.clear()
sheet.insert_row(headers_row, 1)
sheet.insert_rows(rows, 2)

print(f"✅ Logged {len(rows)} rows with Call/Put split format")
