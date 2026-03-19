from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

LEVELS = {
    6840: {"type": "RESISTANCE", "label": "Bull/Bear Line",      "bias": "PUTS"},
    6715: {"type": "RESISTANCE", "label": "Red Band Resistance", "bias": "PUTS"},
    6692: {"type": "RESISTANCE", "label": "Broken Support",      "bias": "PUTS"},
    6658: {"type": "RESISTANCE", "label": "Swing High",          "bias": "PUTS"},
    6635: {"type": "SUPPORT",    "label": "Daily Support",       "bias": "CALLS"},
    6600: {"type": "SUPPORT",    "label": "Round Number",        "bias": "CALLS"},
    6580: {"type": "SUPPORT",    "label": "Daily 200MA KEY",     "bias": "CALLS"},
    6550: {"type": "SUPPORT",    "label": "Midpoint Buffer",     "bias": "CALLS"},
    6500: {"type": "SUPPORT",    "label": "Weekly 50MA MAJOR",   "bias": "CALLS"},
    6470: {"type": "SUPPORT",    "label": "Breakdown Level",     "bias": "ABORT"},
}

RSI_OVERSOLD   = 35
RSI_OVERBOUGHT = 60


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing")
        return False
    url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       message,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            result = r.read()
            print(f"Telegram response: {result}")
            return r.status == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


def safe_float(val, default=50.0):
    try:
        return float(str(val).strip())
    except Exception:
        return default


def find_closest_level(price):
    closest = min(LEVELS.keys(), key=lambda l: abs(l - price))
    if abs(closest - price) <= 20:
        return closest, LEVELS[closest]
    return None, None


def evaluate_setup(price, rsi_5m, rsi_1h, level, level_info):
    bias  = level_info["bias"]
    score = 0
    met   = []
    miss  = []

    dist = abs(price - level)
    if dist <= 15:
        score += 1
        met.append(f"Price {dist:.0f}pts from {level}")
    else:
        miss.append(f"Price {dist:.0f}pts away from level")

    if bias == "CALLS" and rsi_5m <= RSI_OVERSOLD:
        score += 1
        met.append(f"5M RSI oversold: {rsi_5m:.1f}")
    elif bias == "PUTS" and rsi_5m >= RSI_OVERBOUGHT:
        score += 1
        met.append(f"5M RSI overbought: {rsi_5m:.1f}")
    else:
        miss.append(f"5M RSI not confirming: {rsi_5m:.1f}")

    if bias == "CALLS" and rsi_1h <= 42:
        score += 1
        met.append(f"1H RSI low: {rsi_1h:.1f}")
    elif bias == "PUTS" and rsi_1h >= 55:
        score += 1
        met.append(f"1H RSI high: {rsi_1h:.1f}")
    else:
        miss.append(f"1H RSI neutral: {rsi_1h:.1f}")

    score += 1
    met.append(f"Key level: {level_info['label']}")

    grade = "NO SETUP"
    if score == 4:   grade = "A+"
    elif score == 3: grade = "B"
    elif score == 2: grade = "C"

    return {"grade": grade, "score": score, "met": met, "miss": miss, "bias": bias}


def build_message(price, rsi_5m, rsi_1h, level, level_info, setup):
    now   = datetime.now().strftime("%H:%M ET")
    grade = setup["grade"]
    bias  = setup["bias"]

    icons = {"A+": "🚨", "B": "⚡", "C": "👀", "NO SETUP": "ℹ️"}
    bemoj = {"CALLS": "🟢", "PUTS": "🔴", "ABORT": "⛔"}

    met_text  = "\n".join([f"✅ {c}" for c in setup["met"]])
    miss_text = "\n".join([f"❌ {c}" for c in setup["miss"]])

    strike_hint = ""
    if grade == "A+" and bias == "CALLS":
        strike_hint = f"\n💡 Strike: {int(price)-10} calls\n💡 Stop: below {level-20}"
    elif grade == "A+" and bias == "PUTS":
        strike_hint = f"\n💡 Strike: {int(price)+10} puts\n💡 Stop: above {level+20}"

    action = ""
    if grade == "A+":
        action = "\n📸 Screenshot 5M\n📤 Send to Claude NOW"
    elif grade in ("B", "C"):
        action = "\n👀 WATCH — wait for candle close"
    elif bias == "ABORT":
        action = "\n⛔ BREAKDOWN — close longs now"

    msg = (
        f"{icons.get(grade,'ℹ️')} <b>SPX — {grade} {bemoj.get(bias,'')} {bias}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🕐 {now}\n"
        f"📍 Price: {price:.2f}\n"
        f"🎯 Level: {level} — {level_info['label']}\n"
        f"📊 RSI 5M: {rsi_5m:.1f} | 1H: {rsi_1h:.1f}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"{met_text}"
    )
    if miss_text:
        msg += f"\n{miss_text}"
    if strike_hint:
        msg += f"\n━━━━━━━━━━━━━━━━{strike_hint}"
    if action:
        msg += f"\n━━━━━━━━━━━━━━━━{action}"

    return msg


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            raw_text = raw.decode("utf-8", errors="replace")
            print(f"Raw payload received: {raw_text}")

            # Parse JSON safely
            try:
                payload = json.loads(raw_text)
            except Exception as je:
                print(f"JSON parse error: {je}")
                # Try to send raw alert anyway
                send_telegram(
                    f"⚡ <b>SPX Alert Fired</b>\n"
                    f"Could not parse data\n"
                    f"Raw: {raw_text[:150]}\n"
                    f"📸 Check chart manually"
                )
                self._respond(200, {"status": "raw_alert_sent"})
                return

            print(f"Parsed: {payload}")

            # Extract price flexibly
            price = safe_float(
                payload.get("price") or
                payload.get("close") or
                payload.get("last") or
                payload.get("p") or 0, 0
            )

            # Extract RSI
            rsi_5m = safe_float(payload.get("rsi_5m") or payload.get("rsi") or 50, 50)
            rsi_1h = safe_float(payload.get("rsi_1h") or 50, 50)

            # Extract level
            level = int(safe_float(payload.get("level") or 0, 0))

            print(f"price={price} rsi_5m={rsi_5m} rsi_1h={rsi_1h} level={level}")

            # If no price send basic alert
            if price == 0:
                send_telegram(
                    f"⚡ <b>SPX Alert Fired</b>\n"
                    f"Price not found in payload\n"
                    f"Data: {str(payload)[:150]}\n"
                    f"📸 Check chart manually"
                )
                self._respond(200, {"status": "basic_alert_sent"})
                return

            # Find level
            if not level or level not in LEVELS:
                level, level_info = find_closest_level(price)
            else:
                level_info = LEVELS.get(level)

            if not level or not level_info:
                send_telegram(
                    f"📍 <b>SPX Price Alert</b>\n"
                    f"Price: {price:.2f}\n"
                    f"Not at key level\n"
                    f"RSI 5M: {rsi_5m:.1f}\n"
                    f"👀 Watch chart"
                )
                self._respond(200, {"status": "ok", "note": "no_level"})
                return

            # Evaluate and send
            setup = evaluate_setup(price, rsi_5m, rsi_1h, level, level_info)
            msg   = build_message(price, rsi_5m, rsi_1h, level, level_info, setup)
            send_telegram(msg)

            self._respond(200, {"status": "ok", "grade": setup["grade"]})

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            try:
                send_telegram(f"⚠️ Bot Error\n{str(e)[:100]}\n📸 Check chart manually")
            except Exception:
                pass
            self._respond(500, {"error": str(e)})

    def do_GET(self):
        self._respond(200, {
            "status":              "SPX Alert Bot running",
            "levels_watching":     list(LEVELS.keys()),
            "telegram_configured": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
        })

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")
