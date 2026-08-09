import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from fastapi import FastAPI, Header, HTTPException, Request


BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_TELEGRAM_ID = int(os.environ.get("ADMIN_TELEGRAM_ID", "0"))
PUBLIC_BASE_URL = os.environ["PUBLIC_BASE_URL"].rstrip("/")
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

SYNTX_URL = os.environ.get(
    "SYNTX_URL",
    "https://syntx.ai/welcome/zEIpwfrW",
)
PAYMENT_URL = os.environ.get(
    "PAYMENT_URL",
    "https://t.me/pakopay_bot?start=1626444641",
)
CONTACT_URL = os.environ.get(
    "CONTACT_URL",
    "https://t.me/RMEDAI",
)

WEBHOOK_URL = f"{PUBLIC_BASE_URL}/telegram/webhook/{WEBHOOK_SECRET}"

bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


class OrderForm(StatesGroup):
    service = State()
    description = State()
    contact = State()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 AI-фото", callback_data="photo"),
                InlineKeyboardButton(text="🎬 AI-видео", callback_data="video"),
            ],
            [
                InlineKeyboardButton(text="✨ Портфолио", callback_data="portfolio"),
                InlineKeyboardButton(text="💎 Услуги и цены", callback_data="prices"),
            ],
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="order")],
            [
                InlineKeyboardButton(text="🤖 SYNTX", url=SYNTX_URL),
                InlineKeyboardButton(text="💳 Оплата зарубежных сервисов", url=PAYMENT_URL),
            ],
            [InlineKeyboardButton(text="📩 Связаться с RMED AI", url=CONTACT_URL)],
        ]
    )


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="home")]
        ]
    )


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статус", callback_data="admin_status")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")],
        ]
    )


WELCOME = (
    "🟣 <b>RMED AI</b>\n\n"
    "AI-фото, AI-видео и рекламный контент.\n"
    "Выберите нужный раздел:"
)


async def show_home(target: Message | CallbackQuery):
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(WELCOME, reply_markup=main_menu())
        await target.answer()
    else:
        await target.answer(WELCOME, reply_markup=main_menu())


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await show_home(message)


@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Заявка отменена.", reply_markup=main_menu())


@dp.message(Command("admin"))
async def admin_handler(message: Message):
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        return
    await message.answer(
        "🛠 <b>RMED AI — админка</b>\n\n"
        "Первая рабочая версия.",
        reply_markup=admin_menu(),
    )


@dp.callback_query(F.data == "home")
async def home_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_home(callback)


@dp.callback_query(F.data == "photo")
async def photo_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "📸 <b>AI-фото</b>\n\n"
        "Фотореалистичные портреты, рекламные изображения, fashion, "
        "персонажи и креативные визуалы.\n\n"
        "Для заказа вернитесь в меню и нажмите «Оставить заявку».",
        reply_markup=back_menu(),
    )
    await callback.answer()


@dp.callback_query(F.data == "video")
async def video_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎬 <b>AI-видео</b>\n\n"
        "Кинематографичные ролики, реклама, Reality Glitch, "
        "персонажные сцены и анимация изображений.\n\n"
        "Для заказа вернитесь в меню и нажмите «Оставить заявку».",
        reply_markup=back_menu(),
    )
    await callback.answer()


@dp.callback_query(F.data == "portfolio")
async def portfolio_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "✨ <b>Портфолио RMED AI</b>\n\n"
        "Сюда следующим этапом добавим лучшие фото и видео, "
        "а затем — загрузку новых работ прямо через Telegram-админку.",
        reply_markup=back_menu(),
    )
    await callback.answer()


@dp.callback_query(F.data == "prices")
async def prices_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "💎 <b>Услуги и цены</b>\n\n"
        "Стоимость зависит от задачи, количества сцен и сложности генерации.\n\n"
        "Оставьте заявку — RMED AI уточнит задачу и предложит вариант.",
        reply_markup=back_menu(),
    )
    await callback.answer()


@dp.callback_query(F.data == "order")
async def order_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderForm.service)
    await callback.message.edit_text(
        "📝 <b>Новая заявка</b>\n\n"
        "Что вам нужно?\n"
        "Например: AI-видео, AI-фото, рекламный ролик, оформление."
    )
    await callback.answer()


@dp.message(OrderForm.service)
async def order_service(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Напишите тип услуги текстом.")
        return
    await state.update_data(service=message.text.strip())
    await state.set_state(OrderForm.description)
    await message.answer(
        "Опишите задачу. Можно указать сюжет, формат, длительность и стиль."
    )


@dp.message(OrderForm.description)
async def order_description(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Опишите задачу текстом.")
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(OrderForm.contact)
    await message.answer(
        "Оставьте контакт для связи: @username, телефон или другой способ."
    )


@dp.message(OrderForm.contact)
async def order_contact(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Укажите контакт текстом.")
        return

    await state.update_data(contact=message.text.strip())
    data = await state.get_data()

    username = f"@{message.from_user.username}" if message.from_user.username else "нет"
    admin_text = (
        "🔥 <b>Новая заявка RMED AI</b>\n\n"
        f"<b>Telegram ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>Username:</b> {username}\n"
        f"<b>Имя:</b> {message.from_user.full_name}\n\n"
        f"<b>Услуга:</b> {data['service']}\n\n"
        f"<b>Задача:</b> {data['description']}\n\n"
        f"<b>Контакт:</b> {data['contact']}"
    )

    if ADMIN_TELEGRAM_ID:
        try:
            await bot.send_message(ADMIN_TELEGRAM_ID, admin_text)
        except Exception:
            pass

    await state.clear()
    await message.answer(
        "✅ <b>Заявка принята.</b>\n\nRMED AI получил данные и сможет связаться с вами.",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "admin_status")
async def admin_status(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_TELEGRAM_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(
        "✅ Бот работает.\n"
        "Webhook подключён.\n"
        "SYNTX и PakoPay подключены."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(
        WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=False,
    )
    yield
    await bot.session.close()


app = FastAPI(title="RMED AI Bot", version="0.3.0", lifespan=lifespan)


@app.get("/")
async def root():
    return {"service": "RMED AI Telegram Bot", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/telegram/webhook/{path_secret}")
async def telegram_webhook(
    path_secret: str,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if path_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=404, detail="Not found")
    if x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid Telegram secret")

    payload = await request.json()
    update = Update.model_validate(payload, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
