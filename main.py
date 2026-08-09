import os
import logging
import asyncio
import json
from pathlib import Path
from contextlib import asynccontextmanager, suppress

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
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))

SYNTX_URL = "https://syntx.ai/welcome/zEIpwfrW"
PAKOPAY_URL = "https://t.me/pakopay_bot?start=1626444641"
DATA_FILE = Path("/app/portfolio.json")

# Telegram хранит сами фото/видео. Мы сохраняем только их file_id.
portfolio = {"photo": [], "video": []}


def load_portfolio():
    global portfolio
    try:
        if DATA_FILE.exists():
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                portfolio["photo"] = data.get("photo", [])
                portfolio["video"] = data.get("video", [])
    except Exception:
        log.exception("Could not load portfolio")


def save_portfolio():
    try:
        DATA_FILE.write_text(
            json.dumps(portfolio, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        log.exception("Could not save portfolio")


load_portfolio()
tg = Application.builder().token(BOT_TOKEN).updater(None).build()
telegram_ready = False


def menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎨 AI-фото", callback_data="photo"),
            InlineKeyboardButton("🎬 AI-видео", callback_data="video"),
        ],
        [
            InlineKeyboardButton("🖼 Портфолио", callback_data="portfolio"),
            InlineKeyboardButton("💰 Услуги и цены", callback_data="prices"),
        ],
        [InlineKeyboardButton("📝 Оставить заявку", callback_data="lead")],
        [
            InlineKeyboardButton("⚡ SYNTX", url=SYNTX_URL),
            InlineKeyboardButton("💳 Оплата зарубежных сервисов", url=PAKOPAY_URL),
        ],
    ])


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить AI-фото", callback_data="admin_add_photo")],
        [InlineKeyboardButton("➕ Добавить AI-видео", callback_data="admin_add_video")],
        [InlineKeyboardButton("🗑 Очистить фото", callback_data="admin_clear_photo")],
        [InlineKeyboardButton("🗑 Очистить видео", callback_data="admin_clear_video")],
        [InlineKeyboardButton("👁 Посмотреть портфолио", callback_data="portfolio")],
    ])


def order_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Заказать", callback_data="lead")],
        [InlineKeyboardButton("⬅️ Главное меню", callback_data="home")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text(
        "👋 Добро пожаловать в RMED AI.\n\n"
        "Создаём AI-фото, AI-видео и рекламные креативы для бизнеса и соцсетей.\n\n"
        "Выберите нужный раздел:",
        reply_markup=menu(),
    )


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id != ADMIN_TELEGRAM_ID:
        return
    context.user_data.clear()
    await update.effective_message.reply_text(
        "⚙️ RMED AI — управление\n\n"
        f"Фото в портфолио: {len(portfolio['photo'])}\n"
        f"Видео в портфолио: {len(portfolio['video'])}\n\n"
        "Здесь ты можешь добавлять работы прямо из Telegram.",
        reply_markup=admin_menu(),
    )


async def show_items(message, kind=None):
    items = []
    if kind in (None, "photo"):
        items += [("photo", x) for x in portfolio["photo"]]
    if kind in (None, "video"):
        items += [("video", x) for x in portfolio["video"]]

    if not items:
        await message.reply_text(
            "Пока здесь нет загруженных работ. Скоро добавим примеры.",
            reply_markup=order_keyboard(),
        )
        return

    # Показываем последние 12 работ, чтобы не заваливать пользователя сообщениями.
    for item_kind, item in items[-12:]:
        caption = item.get("caption") or "RMED AI"
        try:
            if item_kind == "photo":
                await message.reply_photo(item["file_id"], caption=caption)
            else:
                await message.reply_video(item["file_id"], caption=caption)
        except Exception:
            log.exception("Could not send portfolio item")

    await message.reply_text("Хотите такой же проект?", reply_markup=order_keyboard())


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "home":
        context.user_data.clear()
        await q.message.reply_text("Главное меню:", reply_markup=menu())
        return

    if data == "photo":
        await q.message.reply_text(
            "🎨 AI-фото\n\n"
            "• рекламные изображения для бизнеса\n"
            "• персональные AI-фотосессии\n"
            "• карточки товаров и креативы\n"
            "• визуалы для соцсетей\n\n"
            "Ниже — примеры работ.",
        )
        await show_items(q.message, "photo")
        return

    if data == "video":
        await q.message.reply_text(
            "🎬 AI-видео\n\n"
            "• рекламные AI-ролики\n"
            "• оживление фотографий\n"
            "• cinematic и viral-креативы\n"
            "• ролики для Reels / Shorts / TikTok\n\n"
            "Ниже — примеры работ.",
        )
        await show_items(q.message, "video")
        return

    if data == "portfolio":
        await q.message.reply_text("🖼 Портфолио RMED AI\n\nПоследние работы:")
        await show_items(q.message)
        return

    if data == "prices":
        await q.message.reply_text(
            "💰 Услуги RMED AI\n\n"
            "🎨 AI-фото — стоимость зависит от количества изображений и сложности задачи.\n\n"
            "🎬 AI-видео — стоимость зависит от длительности, сценария и сложности генерации.\n\n"
            "🏢 Для бизнеса — рекламные креативы и пакеты контента рассчитываются индивидуально.\n\n"
            "Нажмите «Оставить заявку» — обсудим задачу и назовём точную стоимость.",
            reply_markup=order_keyboard(),
        )
        return

    if data == "lead":
        context.user_data.clear()
        context.user_data["waiting_lead"] = True
        await q.message.reply_text(
            "📝 Расскажите одним сообщением:\n\n"
            "1) что хотите сделать;\n"
            "2) фото или видео;\n"
            "3) ваш @username или телефон.\n\n"
            "Заявка сразу придёт Руслану."
        )
        return

    if data.startswith("admin_"):
        if not q.from_user or q.from_user.id != ADMIN_TELEGRAM_ID:
            return

        if data == "admin_add_photo":
            context.user_data.clear()
            context.user_data["admin_upload"] = "photo"
            await q.message.reply_text(
                "📸 Отправь мне фотографию, которую нужно добавить в портфолио.\n"
                "Подпись к фото можешь написать прямо в подписи сообщения."
            )
            return

        if data == "admin_add_video":
            context.user_data.clear()
            context.user_data["admin_upload"] = "video"
            await q.message.reply_text(
                "🎥 Отправь мне видео, которое нужно добавить в портфолио.\n"
                "Название/описание можешь написать в подписи сообщения."
            )
            return

        if data == "admin_clear_photo":
            portfolio["photo"] = []
            save_portfolio()
            await q.message.reply_text("✅ Все AI-фото удалены из портфолио.", reply_markup=admin_menu())
            return

        if data == "admin_clear_video":
            portfolio["video"] = []
            save_portfolio()
            await q.message.reply_text("✅ Все AI-видео удалены из портфолио.", reply_markup=admin_menu())
            return


async def admin_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id != ADMIN_TELEGRAM_ID:
        return

    expected = context.user_data.get("admin_upload")
    if not expected:
        return

    message = update.effective_message
    caption = (message.caption or "RMED AI").strip()

    if expected == "photo" and message.photo:
        portfolio["photo"].append({"file_id": message.photo[-1].file_id, "caption": caption})
        save_portfolio()
        context.user_data.clear()
        await message.reply_text(
            f"✅ Фото добавлено. Всего фото: {len(portfolio['photo'])}.",
            reply_markup=admin_menu(),
        )
        return

    if expected == "video" and message.video:
        portfolio["video"].append({"file_id": message.video.file_id, "caption": caption})
        save_portfolio()
        context.user_data.clear()
        await message.reply_text(
            f"✅ Видео добавлено. Всего видео: {len(portfolio['video'])}.",
            reply_markup=admin_menu(),
        )
        return

    await message.reply_text("Нужен именно тот тип файла, который выбран в админ-меню.")


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
            "🔥 Новая заявка RMED AI\n\n"
            f"Клиент: {user.full_name if user else 'неизвестно'}\n"
            f"Telegram: {username}\n"
            f"ID: {user.id if user else '-'}\n\n"
            f"{body}",
        )

    await update.effective_message.reply_text(
        "✅ Заявка отправлена. С вами свяжутся.",
        reply_markup=menu(),
    )


tg.add_handler(CommandHandler("start", start))
tg.add_handler(CommandHandler("admin", admin))
tg.add_handler(CallbackQueryHandler(button))
tg.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, admin_media))
tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lead_message))


async def start_telegram():
    global telegram_ready
    try:
        log.info("Starting Telegram initialization...")
        await tg.initialize()
        await tg.start()
        telegram_ready = True
        log.info("Telegram application initialized")

        if not PUBLIC_BASE_URL:
            log.error("PUBLIC_BASE_URL is empty. Webhook cannot be installed.")
            return

        webhook_url = f"{PUBLIC_BASE_URL}/telegram/webhook"
        await tg.bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        log.info("Telegram webhook installed: %s", webhook_url)
    except Exception:
        telegram_ready = False
        log.exception("Telegram initialization failed. HTTP server remains available.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    telegram_task = asyncio.create_task(start_telegram())
    log.info("HTTP application started. Telegram initialization is running in background.")
    yield

    if not telegram_task.done():
        telegram_task.cancel()
        with suppress(asyncio.CancelledError):
            await telegram_task

    if telegram_ready:
        with suppress(Exception):
            await tg.stop()
        with suppress(Exception):
            await tg.shutdown()


app = FastAPI(title="RMED AI Bot", lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "service": "RMED AI Bot",
        "status": "ok",
        "telegram": "ready" if telegram_ready else "starting",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not telegram_ready:
        raise HTTPException(status_code=503, detail="Telegram is starting")

    data = await request.json()
    update = Update.de_json(data, tg.bot)
    await tg.process_update(update)
    return {"ok": True}
