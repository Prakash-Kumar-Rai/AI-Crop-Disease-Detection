"""
Public Internet Tunnel Launcher for AI Crop Disease Detection.
Uses pyngrok to create a secure, public HTTPS URL accessible from anywhere on the internet.
"""

import os
import sys
from dotenv import load_dotenv
from pyngrok import ngrok

# Ensure safe UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

PORT = int(os.getenv("PORT", 5000))
AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "").strip()

print("=" * 65)
print("AI Crop Disease Detection - Public Internet Launcher")
print("=" * 65)

if AUTHTOKEN:
    ngrok.set_auth_token(AUTHTOKEN)
    print("[+] Ngrok authentication token configured.")
else:
    print("[i] Tip: To avoid session timeouts, you can add your free Ngrok token")
    print("    to your .env file as: NGROK_AUTHTOKEN=your_token_here")
    print("    Get one free at: https://dashboard.ngrok.com/get-started/your-authtoken\n")

try:
    print(f"[*] Opening public tunnel to port {PORT}...")
    public_url = ngrok.connect(PORT, "http").public_url
    print("\n" + "*" * 65)
    print(" SUCCESS! Your app is live on the internet at:")
    print(f" >>> {public_url} <<<")
    print("*" * 65 + "\n")
    print("Share this link with anyone, or open it on your smartphone browser!\n")
except Exception as e:
    print(f"\n[!] Note: Ngrok tunnel setup: {e}")
    print("\n[*] You can still access your app across your local network / Wi-Fi:")
    print("    Simply run 'python app.py' and use your local network IP!\n")

print("[*] Launching Flask app...")
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)

