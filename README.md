# SPX Alert Bot

Real-time A+ setup scanner for SPX intraday trading.

## How It Works
```
TradingView → Webhook → Vercel → RSI Check → Telegram Alert → Claude Analysis
```

## Quick Start
1. Create Telegram bot via @BotFather
2. Deploy to Vercel
3. Add env vars: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
4. Set TradingView webhooks at key levels
5. Receive A+ alerts on phone

## Full Guide
See SETUP_GUIDE.md

## Levels Monitored
- 6840 Bull/Bear Line
- 6715 Red Band Resistance  
- 6692 Broken Support
- 6658 Swing High
- 6635 Daily Support
- 6580 Daily 200MA (KEY)
- 6550 Midpoint
- 6500 Weekly 50MA (MAJOR)
- 6470 Breakdown Level

## Alert Grades
- A+ = All conditions met → trade it
- B  = Watching → wait for confirmation  
- C  = Ignored → bot stays silent
