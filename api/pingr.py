#!/usr/bin/env python3
print("Script loaded successfully ✅")

import os
import time
import json
import requests
import numpy as np
from datetime import datetime, timezone

# -----------------------
# Load config from GitHub
# -----------------------
CONFIG_URL = "https://raw.githubusercontent.com/rajnet70/Binance-discord-alert/main/config.json"
GITHUB_TOKEN = "ghp_xxx"  # replace later (temporary only)

def load_config():
    try:
        print("🔄 Loading config from GitHub...")
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        r = requests.get(CONFIG_URL, headers=headers, timeout=10)
        r.raise_for_status()
        cfg = r.json()
        print("✅ Config loaded successfully.")
        return cfg
    except Exception as e:
        print(f"⚠️ Could not load config: {e}")
        return {}

config = load_config()

# -----------------------
# Proxy fallback setup
# -----------------------
BINANCE_BASE = "https://fapi.binance.com"
PROXIES = [
    "https://api.allorigins.win/raw?url=",
    "https://thingproxy.freeboard.io/fetch/",
]

def fetch_with_proxy(endpoint):
    for p in PROXIES + [""]:
        try:
            url = f"{p}{BINANCE_BASE}{endpoint}" if p else f"{BINANCE_BASE}{endpoint}"
            r = requests.get(url, timeout=10)
            if r.status_code == 451:
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"Proxy {p or 'direct'} failed: {e}")
            continue
    return None

# -----------------------
# Basic calculations
# -----------------------
def calculate_ema(values, period):
    if len(values) < period: return []
    ema = [sum(values[:period]) / period]
    k = 2 / (period + 1)
    for price in values[period:]:
        ema.append(price * k + ema[-1] * (1 - k))
    return ema

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return []
    deltas = np.diff(prices)
    up = np.where(deltas > 0, deltas, 0)
    down = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(up[:period])
    avg_loss = np.mean(down[:period])
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = [100 - (100 / (1 + rs))]
    for i in range(period, len(deltas)):
        gain = up[i]
        loss = down[i]
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi.append(100 - (100 / (1 + rs)))
    return rsi

def check_macd_cross(symbol):
    klines = fetch_with_proxy(f"/fapi/v1/klines?symbol={symbol}&interval=15m&limit=200")
    if not klines: return False
    closes = [float(k[4]) for k in klines]
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    macd = [a - b for a, b in zip(ema12[-len(ema26):], ema26)]
    if len(macd) < 10: return False
    signal = calculate_ema(macd, 9)
    return macd[-2] < signal[-2] and macd[-1] > signal[-1]

# -----------------------
# Core scanning logic
# -----------------------
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
FAVORITE_PAIRS = config.get("favorite_pairs", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
MIN_VOLUME = config.get("min_24h_volume_usdt", 40000000)

def send_discord(msg):
    if not DISCORD_WEBHOOK_URL:
        print("[No webhook] " + msg)
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=8)
    except Exception as e:
        print("Discord error:", e)

def scan_once():
    results = []
    for sym in FAVORITE_PAIRS[:5]:  # scan first 5 for test
        t24 = fetch_with_proxy(f"/fapi/v1/ticker/24hr?symbol={sym}")
        if not t24: 
            results.append(f"{sym}: ❌ Failed to fetch data")
            continue
        vol = float(t24.get("quoteVolume", 0))
        if vol < MIN_VOLUME:
            results.append(f"{sym}: skipped (low volume {vol:,.0f})")
            continue

        macd = check_macd_cross(sym)
        results.append(f"{sym}: ✅ {'MACD Bullish' if macd else 'No signal'}")
    return results

def handler(request=None):
    print("🚀 Running Pingr scan...")
    out = scan_once()
    summary = "\n".join(out)
    send_discord(f"**Pingr Scan Completed ✅**\n```\n{summary}\n```")
    return {"statusCode": 200, "body": json.dumps({"result": out})}

if __name__ == "__main__":
    handler()
