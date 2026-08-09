import os
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rmed-ai-bot")

BOT_TOKEN = os.environ["BOT_TOKEN"]
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))

SYNTX_URL = "https://syntx.ai/welcome/zEIpwfrW"
PAKOPAY_URL = "https://t.me/pakopay_bot?start=1626444641"

tg = Application.builder().token(BOT_TOKEN).updater(None).build()

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 AI-фото", callback_data="photo"),
         InlineKeyboardButton("🎬 AI-видео", callback_data="video")],
        [InlineKeyboardButton("🖼 Портфолио", callback_data="portfolio"),
         InlineKeyboardButton("💰 Услуги и цены", callback_data="prices")],
        [InlineKeyboardButton("📝 Оставить заявку", callback_data="lead")],
        [InlineKeyboardButton("⚡ SYNТX", url=SYNTX_URL),
         InlineKeyboardButton("💳 Оплата зарубежных сервисов", url=PAKOPAY_URL)],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("waiting_lead", None)
    await update.effective_message.reply_text(
        "👋 Добро пожаловать в RMED AI.\n\n"
        "AI-фото, AI-видео и креативный контент для бизнеса и соцсетей.\n"
        "Выберите нужный раздел:",
        reply_markup=menu(),
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id != ADMIN_TELEGRAM_ID:
        return
    await update.effective_message.reply_text(
        "⚙️ RMED AI Admin\n\nБот запущен и принимает заявки."
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "photo":
        text = "🎨 AI-фото\n\nСоздание рекламных, портретных и креативных AI-изображений."
    elif q.data == "video":
        text = "🎬 AI-видео\n\nРекламные ролики, анимация изображений и AI-креативы."
    elif q.data == "portfolio":
        text = "🖼 Портфолио\n\nРаздел готов к наполнению вашими работами."
    elif q.data == "prices":
        text = "💰 Услуги и цены\n\nСтоимость зависит от задачи. Оставьте заявку — обсудим проект."
    elif q.data == "lead":
        context.user_data["waiting_lead"] = True
        await q.message.reply_text(
            "📝 Напишите одним сообщением:\n"
            "1) что хотите сделать;\n"
            "2) ваш контакт @username или телефон.\n\n"
            "Я передам заявку Руслану."
        )
        return
    else:
        return
    await q.message.reply_text(text, reply_markup=menu())

async def lead_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_lead"):
        return
    context.user_data["waiting_lead"] = False
    user = update.effective_user
    body = update.effective_message.text
    if ADMIN_TELEGRAM_ID:
        username = f"@{user.username}" if user and user.username else "без username"
        await context.bot.send_message(
            ADMIN_TELEGRAM_ID,
            f"🔥 Новая заявка RMED AI\n\n"
            f"Клиент: {user.full_name if user else 'неизвестно'}\n"
            f"Telegram: {username}\n"
            f"ID: {user.id if user else '-'}\n\n"
            f"{body}"
        )
    await update.effective_message.reply_text(
        "✅ Заявка отправлена. С вами свяжутся.",
        reply_markup=menu(),
    )

tg.add_handler(CommandHandler("start", start))
tg.add_handler(CommandHandler("admin", admin))
tg.add_handler(CallbackQueryHandler(button))
tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lead_message))

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not PUBLIC_BASE_URL:
        raise RuntimeError("PUBLIC_BASE_URL is required")
    await tg.initialize()
    await tg.start()
    webhook_url = f"{PUBLIC_BASE_URL}/telegram/webhook"
    await tg.bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
    log.info("Webhook installed: %s", webhook_url)
    yield
    await tg.bot.delete_webhook()
    await tg.stop()
    await tg.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"service": "RMED AI Bot", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    data = await request.json()
    await tg.process_update(Update.de_json(data, tg.bot))
    return {"ok": True}
