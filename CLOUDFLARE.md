# RMED AI Bot — Cloudflare Workers

This branch replaces the always-on FastAPI/Docker service with an event-driven Cloudflare Worker.

Required Worker secrets:
- BOT_TOKEN
- ADMIN_TELEGRAM_ID
- WEBHOOK_SECRET

Required binding:
- RMED_KV — Cloudflare KV namespace used for portfolio file IDs and temporary conversation state.

After deployment, set the Telegram webhook to:
`https://<worker-domain>/telegram/webhook`
using the same WEBHOOK_SECRET as Telegram's secret_token.

The old Docker/FastAPI implementation remains on main until the Worker is deployed and tested. Do not put Telegram tokens in GitHub.