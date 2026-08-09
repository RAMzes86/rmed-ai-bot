# RMED AI BOT — v0.4 Timeweb

Deployment-ready Telegram bot for RMED AI.

## Included
- Telegram webhook mode
- FastAPI health endpoint `/health`
- Docker container on port 8080
- SYNТX referral link
- PakoPay referral link
- Lead collection with notification to admin
- `/admin` command
- Webhook secret verification

## Required environment variables
- `BOT_TOKEN`
- `ADMIN_TELEGRAM_ID`
- `PUBLIC_BASE_URL`
- `WEBHOOK_SECRET`

Never commit a real Telegram bot token to GitHub.

## Deployment
Deploy the repository using its Dockerfile. The container listens on port `8080`.
After the hosting platform assigns an HTTPS domain, set `PUBLIC_BASE_URL` to that
full origin (without a trailing slash) and redeploy.

## Test
1. Open `/health` — it should return `{"status":"ok"}`.
2. Open the Telegram bot and send `/start`.
3. Test the lead form and confirm the admin receives it.
