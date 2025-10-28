from http.server import BaseHTTPRequestHandler
import json
import requests
from datetime import datetime, timezone

# --- GitHub Config URL ---
CONFIG_URL = "https://raw.githubusercontent.com/rajnet70/Binance-discord-alert/main/config.json"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Fetch config from GitHub
            response = requests.get(CONFIG_URL, timeout=10)
            response.raise_for_status()
            config = response.json()

            # Extract key info (for example: pairs & thresholds)
            pairs = config.get("favorite_pairs", [])[:10]  # show first 10 only
            heat_threshold = config.get("heat_index_threshold", "N/A")

            data = {
                "status": "✅ Config loaded successfully",
                "pairs": pairs,
                "heat_index_threshold": heat_threshold,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Send JSON response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

        except Exception as e:
            # Handle any failure (GitHub / JSON / timeout)
            error_data = {
                "status": "❌ Failed to load config",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(error_data, indent=2).encode("utf-8"))
