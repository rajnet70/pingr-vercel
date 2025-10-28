from http.server import BaseHTTPRequestHandler
import json
import requests
import os
from datetime import datetime, timezone

# --- GitHub Config (private repo) ---
CONFIG_URL = "https://raw.githubusercontent.com/rajnet70/Binance-discord-alert/main/config.json"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get token from Vercel environment
            GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
            if not GITHUB_TOKEN:
                raise Exception("Missing GitHub Token (add GITHUB_TOKEN to Vercel Environment Variables)")

            # Fetch config from private GitHub
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(CONFIG_URL, headers=headers, timeout=10)
            response.raise_for_status()
            config = response.json()

            # Extract some info from config
            pairs = config.get("favorite_pairs", [])[:10]
            thresholds = {
                "heat_index_threshold": config.get("heat_index_threshold"),
                "volume_spike_threshold": config.get("volume_spike_threshold"),
                "price_change_threshold": config.get("price_change_threshold"),
            }

            data = {
                "status": "✅ Config loaded successfully from private GitHub",
                "pairs_sample": pairs,
                "thresholds": thresholds,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Send success JSON
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

        except Exception as e:
            # Handle any error gracefully
            error_data = {
                "status": "❌ Failed to load config",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(error_data, indent=2).encode("utf-8"))
