import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Настройки
BOT_TOKEN = "8839010775:AAF1UnUqmDxJCgcg8NdWT55xQ9xdRDCjAYE"
SOURCE_CHANNEL = -1004298123113
ADMIN_ID = 918395366

# Читаем каналы из переменной окружения
target_channels_str = os.getenv("TARGET_CHANNELS", "")
TARGET_CHANNELS = [int(ch.strip()) for ch in target_channels_str.split(",") if ch.strip()]

# Состояние
active_channels = set(TARGET_CHANNELS)
forwarding_enabled = True

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Названия каналов
CHANNEL_NAMES = {}
for i, channel_id in enumerate(TARGET_CHANNELS, 1):
    if channel_id == -1004316696837:
        CHANNEL_NAMES[channel_id] = "ARPOZAN"
    else:
        CHANNEL_NAMES[channel_id] = f"Канал {i}"

@dp.message(Command("admin"))
async def admin_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Выбрать каналы", callback_data="select_channels")],
        [InlineKeyboardButton(text="🔄 Пересылка", callback_data="toggle_forward")],
        [InlineKeyboardButton(text="ℹ️ Статус", callback_data="status")],
    ])
    
    status = "🟢 Вкл" if forwarding_enabled else "🔴 Выкл"
    await message.answer(f"📋 Админ панель\\nПересылка: {status}", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "select_channels")
async def select_channels_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён!")
        return
    
    buttons = []
    for channel_id, name in CHANNEL_NAMES.items():
        status = "✅" if channel_id in active_channels else "⬜"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {name}",
            callback_data=f"toggle_ch_{channel_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="admin_menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("📺 Выберите каналы:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("toggle_ch_"))
async def toggle_channel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён!")
        return
    
    channel_id = int(callback.data.split("_")[2])
    
    if channel_id in active_channels:
        active_channels.remove(channel_id)
        await callback.answer("➖ Выключен")
    else:
        active_channels.add(channel_id)
        await callback.answer("➕ Включен")
    
    buttons = []
    for ch_id, name in CHANNEL_NAMES.items():
        status = "✅" if ch_id in active_channels else "⬜"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {name}",
            callback_data=f"toggle_ch_{ch_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="admin_menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_reply_markup(reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "toggle_forward")
async def toggle_forwarding(callback: types.CallbackQuery):
    global forwarding_enabled
    
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён!")
        return
    
    forwarding_enabled = not forwarding_enabled
    status = "🟢 Вкл" if forwarding_enabled else "🔴 Выкл"
    logger.info(f"Пересылка: {status}")
    await callback.answer(f"✅ Пересылка {status}")
    await callback.message.edit_text(f"📋 Админ панель\\nПересылка: {status}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Выбрать каналы", callback_data="select_channels")],
        [InlineKeyboardButton(text="🔄 Пересылка", callback_data="toggle_forward")],
        [InlineKeyboardButton(text="ℹ️ Статус", callback_data="status")],
    ]))

@dp.callback_query(lambda c: c.data == "status")
async def show_status(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён!")
        return
    
    forward_status = "🟢 Вкл" if forwarding_enabled else "🔴 Выкл"
    active_count = len(active_channels)
    
    status_text = f"📊 Статус\\n🔄 Пересылка: {forward_status}\\n📺 Активно: {active_count}/{len(CHANNEL_NAMES)}\\n\\nКаналы:"
    
    for channel_id, name in CHANNEL_NAMES.items():
        status = "✅" if channel_id in active_channels else "❌"
        status_text += f"\\n  {status} {name}"
    
    await callback.message.edit_text(status_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="admin_menu")]
    ]))
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_menu")
async def back_to_admin_menu(callback: types.CallbackQuery):
    status = "🟢 Вкл" if forwarding_enabled else "🔴 Выкл"
    await callback.message.edit_text(f"📋 Админ панель\\nПересылка: {status}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Выбрать каналы", callback_data="select_channels")],
        [InlineKeyboardButton(text="🔄 Пересылка", callback_data="toggle_forward")],
        [InlineKeyboardButton(text="ℹ️ Статус", callback_data="status")],
    ]))
    await callback.answer()

@dp.channel_post()
async def forward_message(message: types.Message):
    """Ловим все сообщения в канале"""
    logger.info(f"📨 Message in chat {message.chat.id}")
    
    if message.chat.id != SOURCE_CHANNEL:
        logger.info(f"❌ Wrong channel: {message.chat.id} != {SOURCE_CHANNEL}")
        return
    
    if not forwarding_enabled:
        logger.info("❌ Forwarding disabled")
        return
    
    logger.info(f"✅ Forwarding to {len(active_channels)} channels")
    
    try:
        for channel_id in active_channels:
            await message.copy_to(channel_id)
            logger.info(f"✅ Sent to {channel_id}")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

async def main():
    logger.info("=== BOT STARTED ===")
    logger.info(f"Source channel: {SOURCE_CHANNEL}")
    logger.info(f"Total target channels: {len(TARGET_CHANNELS)}")
    for ch_id, name in CHANNEL_NAMES.items():
        logger.info(f"  {name}: {ch_id}")
    
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())

