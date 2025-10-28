# /api/pingr_light.py
import os
import json
import requests
from datetime import datetime, timezone

# -----------------------------
# CONFIG SOURCE
# -----------------------------
CONFIG_URL = "https://raw.githubusercontent.com/rajnet70/Binance-discord-alert/main/config.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def load_config():
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        r = requests.get(CONFIG_URL, headers=headers, timeout=10)
        r.raise_for_status()
        cfg = r.json()
        return cfg
    except Exception as e:
        return {"error": str(e), "timestamp": str(datetime.now(timezone.utc))}

# -----------------------------
# SIMPLE BINANCE FETCH
# -----------------------------
BINANCE_BASE = "https://fapi.binance.com"
def fetch_24h_ticker(symbol):
    try:
        url = f"{BINANCE_BASE}/fapi/v1/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}

# -----------------------------
# DISCORD ALERT
# -----------------------------
def send_discord_alert(msg):
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        return "No webhook set"
    try:
        requests.post(webhook, json={"content": msg}, timeout=10)
        return "Alert sent ✅"
    except Exception as e:
        return f"Error sending alert: {e}"

# -----------------------------
# MAIN HANDLER
# -----------------------------
def handler(request):
    config = load_config()
    if "error" in config:
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "❌ Config load failed", "error": config["error"]})
        }

    pairs = config.get("favorite_pairs", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])[:5]
    results = []
    heat_threshold = config.get("heat_index_threshold", 50)
    volume_threshold = config.get("volume_spike_threshold", 4)

    for sym in pairs:
        data = fetch_24h_ticker(sym)
        if "error" in data:
            results.append(data)
            continue

        price = float(data.get("lastPrice", 0))
        vol = float(data.get("quoteVolume", 0))
        pct = float(data.get("priceChangePercent", 0))

        strong_move = abs(pct) > 2 and vol > 4e7  # basic test filter
        if strong_move:
            msg = f"**{sym} Momentum Alert** 🚀\nPrice: {price} | 24h Δ {pct:.2f}% | Vol: {vol:,.0f}"
            send_discord_alert(msg)

        results.append({
            "symbol": sym,
            "price": price,
            "pct_change": pct,
            "quote_vol": vol,
            "strong_move": strong_move
        })

    response = {
        "status": "✅ Pingr Light Scan Complete",
        "timestamp": str(datetime.now(timezone.utc)),
        "pairs_checked": len(pairs),
        "results": results
    }

    return {"statusCode": 200, "body": json.dumps(response, indent=2)}

# -----------------------------
# VERCEL ENTRYPOINT
# -----------------------------
def main(request, response):
    result = handler(request)
    response.status_code = result["statusCode"]
    response.headers["Content-Type"] = "application/json"
    response.body = result["body"]
    return response
