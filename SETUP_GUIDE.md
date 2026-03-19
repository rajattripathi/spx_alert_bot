# SPX Alert Bot — Complete Setup Guide

## What This Does
Receives TradingView webhooks when price hits key levels,
evaluates RSI conditions, and sends Telegram alerts
graded A+, B, C, or NO SETUP.

---

## STEP 1 — Create Telegram Bot (5 minutes)

1. Open Telegram
2. Search for: @BotFather
3. Send: /newbot
4. Name it: SPX Alert Bot
5. Username: spx_alert_yourname_bot
6. BotFather gives you a TOKEN — save it

Then get your Chat ID:
1. Search: @userinfobot
2. Start it
3. It sends your Chat ID — save it

---

## STEP 2 — Deploy to Vercel (10 minutes)

1. Push this folder to GitHub:
   - Create new repo: spx-alert-bot
   - Upload all files
   - Commit

2. Go to vercel.com
   - New Project
   - Import from GitHub
   - Select spx-alert-bot repo
   - Click Deploy

3. Add Environment Variables in Vercel:
   - TELEGRAM_BOT_TOKEN = (your token from Step 1)
   - TELEGRAM_CHAT_ID = (your chat ID from Step 1)

4. Redeploy after adding env vars

5. Your webhook URL will be:
   https://spx-alert-bot.vercel.app/webhook

---

## STEP 3 — Set TradingView Alerts (15 minutes)

For EACH level, create a TradingView alert:

### Alert Settings:
- Condition: SPX crosses 6580 (or each level)
- Webhook URL: https://your-app.vercel.app/webhook
- Message (copy exactly):

```json
{
  "price": {{close}},
  "rsi_5m": {{plot_0}},
  "rsi_1h": {{plot_1}},
  "level": 6580,
  "alert": "SPX {{close}}"
}
```

### IMPORTANT — RSI Setup in TradingView:
- Add RSI indicator to your 5M chart (period 14)
- plot_0 = RSI value on 5M chart
- For 1H RSI: add second RSI, set to 1H timeframe
- plot_1 = RSI value on 1H chart

### Create alerts for ALL these levels:
| Level | Type    | Alert Name           |
|-------|---------|----------------------|
| 6840  | Crosses | Bull Bear Line       |
| 6715  | Crosses | Red Band Resistance  |
| 6692  | Crosses | Broken Support       |
| 6658  | Crosses | Swing High           |
| 6635  | Crosses | Daily Support        |
| 6580  | Crosses | Daily 200MA KEY      |
| 6550  | Crosses | Midpoint Buffer      |
| 6500  | Crosses | Weekly 50MA MAJOR    |
| 6470  | Crosses | Breakdown Level      |

---

## STEP 4 — Test It

1. Go to: https://your-app.vercel.app/health
   Should show: {"status": "SPX Alert Bot running"}

2. Send test webhook manually:
   Use Postman or curl:

```bash
curl -X POST https://your-app.vercel.app/webhook \
  -H "Content-Type: application/json" \
  -d '{"price": 6582, "rsi_5m": 28.5, "rsi_1h": 35.0, "level": 6580, "alert": "Test"}'
```

Should receive Telegram message immediately.

---

## STEP 5 — What You'll Receive

### A+ Setup Alert:
```
🚨 SPX ALERT — A+ 🟢 CALLS
━━━━━━━━━━━━━━━━━━━
🕐 Time: 10:23 ET
📍 Price: 6581.50
🎯 Level: 6580 — Daily 200MA 🔴 KEY
📊 RSI 5M: 28.4 | RSI 1H: 34.2
━━━━━━━━━━━━━━━━━━━
CONDITIONS:
✅ Price within 12pts of 6580
✅ 5M RSI oversold: 28.4
✅ 1H RSI low: 34.2
✅ Key level: Daily 200MA
━━━━━━━━━━━━━━━━━━━
💡 Strike: 6570 calls (ITM)
💡 Stop: below 6560
━━━━━━━━━━━━━━━━━━━
📸 Screenshot 5M chart
📤 Send to Claude NOW
```

### B Setup (Watch Only):
```
⚡ SPX ALERT — B 🔴 PUTS
...
👀 WATCH — not A+ yet
Wait for candle to CLOSE
```

### No Setup (Ignored):
Bot stays silent — no message sent

---

## STEP 6 — Your Workflow

```
1. TradingView alert fires at key level
2. Bot evaluates RSI conditions
3. IF A+ or B: Telegram message to phone
4. You screenshot 5M chart
5. Paste to Claude with: "Alert fired — [level]"
6. Claude confirms: enter / skip / wait
7. You execute or pass
```

---

## Updating Levels

To add/change levels, edit api/webhook.py:

```python
LEVELS = {
    6840: {"type": "RESISTANCE", "label": "Bull/Bear Line", "bias": "PUTS"},
    6580: {"type": "SUPPORT", "label": "Daily 200MA", "bias": "CALLS"},
    # Add new levels here
}
```

Push to GitHub → Vercel auto-deploys in 30 seconds.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No Telegram message | Check env vars in Vercel |
| Webhook not receiving | Check URL in TradingView |
| RSI not accurate | Check plot_0/plot_1 mapping |
| Always NO SETUP | Adjust RSI thresholds in webhook.py |

---

## Cost Summary

| Service | Cost |
|---------|------|
| Vercel hosting | FREE |
| Telegram bot | FREE |
| GitHub repo | FREE |
| TradingView alerts | FREE (basic) |
| **Total** | **$0/month** |

---

## Support
Send charts to Claude with:
"Alert fired at [level] — [A+/B grade]"
Claude reads chart and confirms entry.
