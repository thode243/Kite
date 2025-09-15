import gspread
from oauth2client.service_account import ServiceAccountCredentials
from kiteconnect import KiteConnect
import os

# -----------------------------
# 1. Kite Setup
# -----------------------------
SHEET_ID = os.getenv("SHEET_ID", "secret")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "service_account.json")


# -----------------------------
# 2. Google Sheets Setup
# -----------------------------
SHEET_NAME = "OptionChain"
JSON_KEYFILE = "credentials.json"

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# -----------------------------
# 3. Load Existing OI & VWAP Data
# -----------------------------
existing_values = sheet.get_all_values()
prev_oi_dict = {}
prev_vwap_dict = {}

if existing_values:
    headers = existing_values[0]
    if "Strike" in headers:
        strike_col = headers.index("Strike")
        call_oi_col = headers.index("Call OI")
        call_vwap_col = headers.index("Call VWAP")
        put_oi_col = headers.index("Put OI")
        put_vwap_col = headers.index("Put VWAP")

        for row in existing_values[1:]:
            try:
                strike = float(row[strike_col])
                prev_oi_dict[strike] = {
                    "call": int(row[call_oi_col]) if row[call_oi_col] else 0,
                    "put": int(row[put_oi_col]) if row[put_oi_col] else 0
                }
                prev_vwap_dict[strike] = {
                    "call": float(row[call_vwap_col]) if row[call_vwap_col] else 0,
                    "put": float(row[put_vwap_col]) if row[put_vwap_col] else 0
                }
            except:
                continue

# -----------------------------
# 4. Fetch Option Chain Data
# -----------------------------
expiry = "2025-09-16"
instruments = kite.instruments("NFO")

nifty_options = [i for i in instruments if i["name"] == "NIFTY" and i["expiry"].strftime("%Y-%m-%d") == expiry]
print(f"✅ Found {len(nifty_options)} NIFTY contracts for {expiry}")

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
            prev_vwap = prev_vwap_dict.get(strike, {}).get("call", 0)
            # Calculate cumulative VWAP
            vwap = ((prev_vwap * prev_oi) + (ltp * vol)) / max(prev_oi + vol, 1)
            option_chain[strike]["call"] = {
                "ltp": ltp,
                "oi": oi,
                "chg_oi": oi - prev_oi,
                "vol": vol,
                "vwap": round(vwap, 2)
            }
        elif typ == "PE":
            prev_oi = prev_oi_dict.get(strike, {}).get("put", 0)
            prev_vwap = prev_vwap_dict.get(strike, {}).get("put", 0)
            vwap = ((prev_vwap * prev_oi) + (ltp * vol)) / max(prev_oi + vol, 1)
            option_chain[strike]["put"] = {
                "ltp": ltp,
                "oi": oi,
                "chg_oi": oi - prev_oi,
                "vol": vol,
                "vwap": round(vwap, 2)
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
        call.get("vwap", ""),  # VWAP for CE
        put.get("vwap", "")    # VWAP for PE
    ])

# -----------------------------
# 6. Write to Google Sheet
# -----------------------------
headers_row = [
    "Call LTP", "Call OI", "Call Chg OI", "Call Vol",
    "Strike", "Expiry",
    "Put LTP", "Put OI", "Put Chg OI", "Put Vol",
    "Call VWAP", "Put VWAP"
]

sheet.clear()
sheet.insert_row(headers_row, 1)
sheet.insert_rows(rows, 2)

print(f"✅ Logged {len(rows)} rows with Call/Put split format and VWAP")
