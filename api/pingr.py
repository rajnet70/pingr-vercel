import json
import requests

BINANCE_BASE = "https://fapi.binance.com"

def handler(request, context):
    """Vercel-compatible handler for Pingr proxy"""
    try:
        # Extract symbol from query params, default to BTCUSDT
        query = request.get("queryStringParameters") or {}
        symbol = query.get("symbol", "BTCUSDT")

        url = f"{BINANCE_BASE}/fapi/v1/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "symbol": symbol,
                "priceChangePercent": data.get("priceChangePercent"),
                "volume": data.get("volume"),
                "quoteVolume": data.get("quoteVolume")
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
