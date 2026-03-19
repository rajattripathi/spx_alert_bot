from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime

# ─────────────────────────────────────────
# CONFIG — fill these in before deploying
# ─────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# ─────────────────────────────────────────
# KEY LEVELS & THEIR DESCRIPTIONS
# ─────────────────────────────────────────
LEVELS = {
    # RESISTANCE — puts watch
    6840: {"type": "RESISTANCE", "label": "Bull/Bear Line",        "bias": "PUTS"},
    6715: {"type": "RESISTANCE", "label": "Red Band / 1H Resistance", "bias": "PUTS"},
    6692: {"type": "RESISTANCE", "label": "Broken Support",        "bias": "PUTS"},
    6658: {"type": "RESISTANCE", "label": "Swing High",            "bias": "PUTS"},
    # SUPPORT — calls watch
    6635: {"type": "SUPPORT",    "label": "Daily Support",         "bias": "CALLS"},
    6600: {"type": "SUPPORT",    "label": "Round Number",          "bias": "CALLS"},
    6580: {"type": "SUPPORT",    "label": "Daily 200MA 🔴 KEY",    "bias": "CALLS"},
    6550: {"type": "SUPPORT",    "label": "Midpoint Buffer",       "bias": "CALLS"},
    6500: {"type": "SUPPORT",    "label": "Weekly 50MA 🔴 MAJOR",  "bias": "CALLS"},
    6470: {"type": "SUPPORT",    "label": "Breakdown Level",       "bias": "ABORT"},
}

# RSI thresholds
RSI_OVERSOLD  = 32   # calls zone
RSI_OVERBOUGHT = 65  # puts zone


def send_telegram(message: str):
    """Send a message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def evaluate_setup(price: float, rsi_5m: float, rsi_1h: float, level: int, level_info: dict) -> dict:
    """Evaluate if this is an A+ setup."""
    bias = level_info["bias"]
    score = 0
    conditions = []
    missing = []

    # Condition 1 — Price at level
    distance = abs(price - level)
    if distance <= 12:
        score += 1
        conditions.append(f"✅ Price within 12pts of {level}")
    else:
        missing.append(f"❌ Price {distance:.0f}pts from level")

    # Condition 2 — RSI 5M
    if bias == "CALLS" and rsi_5m <= RSI_OVERSOLD:
        score += 1
        conditions.append(f"✅ 5M RSI oversold: {rsi_5m:.1f}")
    elif bias == "PUTS" and rsi_5m >= RSI_OVERBOUGHT:
        score += 1
        conditions.append(f"✅ 5M RSI overbought: {rsi_5m:.1f}")
    else:
        missing.append(f"❌ 5M RSI not confirming: {rsi_5m:.1f}")

    # Condition 3 — RSI 1H
    if bias == "CALLS" and rsi_1h <= 40:
        score += 1
        conditions.append(f"✅ 1H RSI low: {rsi_1h:.1f}")
    elif bias == "PUTS" and rsi_1h >= 55:
        score += 1
        conditions.append(f"✅ 1H RSI high: {rsi_1h:.1f}")
    else:
        missing.append(f"⚠️ 1H RSI neutral: {rsi_1h:.1f}")

    # Condition 4 — Key level quality
    if level_info["type"] in ("SUPPORT", "RESISTANCE"):
        score += 1
        conditions.append(f"✅ Key level: {level_info['label']}")

    grade = "NO SETUP"
    if score == 4:
        grade = "A+"
    elif score == 3:
        grade = "B"
    elif score == 2:
        grade = "C"

    return {
        "grade": grade,
        "score": score,
        "conditions": conditions,
        "missing": missing,
        "bias": bias,
    }


def build_message(price: float, rsi_5m: float, rsi_1h: float,
                  level: int, level_info: dict, setup: dict, alert_name: str) -> str:
    """Build the Telegram alert message."""
    now = datetime.now().strftime("%H:%M ET")
    bias = setup["bias"]
    grade = setup["grade"]

    # Emoji
    grade_emoji = {"A+": "🚨", "B": "⚡", "C": "👀", "NO SETUP": "ℹ️"}.get(grade, "ℹ️")
    bias_emoji  = {"CALLS": "🟢", "PUTS": "🔴", "ABORT": "⛔"}.get(bias, "⚪")

    # Strike suggestion
    strike_hint = ""
    if bias == "CALLS" and grade == "A+":
        strike = int(price) - 10
        strike_hint = f"\n💡 <b>Strike:</b> {strike} calls (ITM)\n💡 <b>Stop:</b> below {level - 20}"
    elif bias == "PUTS" and grade == "A+":
        strike = int(price) + 10
        strike_hint = f"\n💡 <b>Strike:</b> {strike} puts (ITM)\n💡 <b>Stop:</b> above {level + 20}"

    conditions_text = "\n".join(setup["conditions"])
    missing_text    = "\n".join(setup["missing"]) if setup["missing"] else ""

    msg = f"""{grade_emoji} <b>SPX ALERT — {grade} {bias_emoji} {bias}</b>
━━━━━━━━━━━━━━━━━━━
🕐 <b>Time:</b> {now}
📍 <b>Price:</b> {price:.2f}
🎯 <b>Level:</b> {level} — {level_info['label']}
📊 <b>RSI 5M:</b> {rsi_5m:.1f} | <b>RSI 1H:</b> {rsi_1h:.1f}
━━━━━━━━━━━━━━━━━━━
<b>CONDITIONS:</b>
{conditions_text}"""

    if missing_text:
        msg += f"\n\n<b>MISSING:</b>\n{missing_text}"

    if strike_hint:
        msg += f"\n━━━━━━━━━━━━━━━━━━━{strike_hint}"

    if grade == "A+":
        msg += f"\n━━━━━━━━━━━━━━━━━━━\n📸 <b>Screenshot 5M chart</b>\n📤 <b>Send to Claude NOW</b>"
    elif grade in ("B", "C"):
        msg += f"\n━━━━━━━━━━━━━━━━━━━\n👀 <b>WATCH — not A+ yet</b>\nWait for candle to CLOSE"
    elif bias == "ABORT":
        msg += f"\n━━━━━━━━━━━━━━━━━━━\n⛔ <b>BREAKDOWN WARNING</b>\nClose any longs immediately"

    return msg


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        """Receive webhook from TradingView."""
        try:
            length  = int(self.headers.get("Content-Length", 0))
            raw     = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))

            # ── Extract fields from TradingView alert ──
            # TradingView alert message format (set this in TV alert):
            # {"price": {{close}}, "rsi_5m": {{plot_0}}, "rsi_1h": {{plot_1}}, "level": 6580, "alert": "{{ticker}} {{close}}"}
            price      = float(payload.get("price", 0))
            rsi_5m     = float(payload.get("rsi_5m", 50))
            rsi_1h     = float(payload.get("rsi_1h", 50))
            level      = int(payload.get("level", 0))
            alert_name = str(payload.get("alert", "SPX Alert"))

            print(f"Received: price={price} rsi_5m={rsi_5m} rsi_1h={rsi_1h} level={level}")

            # Find matching level
            level_info = LEVELS.get(level)
            if not level_info:
                # Find closest level within 15 points
                closest = min(LEVELS.keys(), key=lambda l: abs(l - price))
                if abs(closest - price) <= 15:
                    level      = closest
                    level_info = LEVELS[closest]
                else:
                    level_info = {"type": "UNKNOWN", "label": "Unknown Level", "bias": "WATCH"}

            # Evaluate setup quality
            setup = evaluate_setup(price, rsi_5m, rsi_1h, level, level_info)

            # Only alert for A+, B, or ABORT
            if setup["grade"] in ("A+", "B") or level_info["bias"] == "ABORT":
                message = build_message(price, rsi_5m, rsi_1h, level, level_info, setup, alert_name)
                send_telegram(message)
                print(f"Alert sent: {setup['grade']}")
            else:
                print(f"No alert — grade: {setup['grade']}")

            # Respond to TradingView
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "grade": setup["grade"],
                "bias": setup["bias"],
            }).encode())

        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "SPX Alert Bot running",
            "levels_watching": list(LEVELS.keys()),
        }).encode())

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")
