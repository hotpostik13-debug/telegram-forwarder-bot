import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Названия каналов (автоматически генерируются)
CHANNEL_NAMES = {}
for i, channel_id in enumerate(TARGET_CHANNELS, 1):
    if channel_id == -1004316696837:
        CHANNEL_NAMES[channel_id] = "ARPOZAN"
    else:
        CHANNEL_NAMES[channel_id] = f"Канал {i}"

@dp.message(Command("admin"))
async def admin_menu(message: types.Message):
    """Админ меню"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Выбрать каналы", callback_data="select_channels")],
        [InlineKeyboardButton(text="🔄 Переключить пересылку", callback_data="toggle_forward")],
        [InlineKeyboardButton(text="ℹ️ Статус", callback_data="status")],
    ])
    
    status = "🟢 Включена" if forwarding_enabled else "🔴 Отключена"
    await message.answer(f"📋 Админ панель\\n\\nПересылка: {status}", reply_markup=keyboard)

@dp.callback_query(F.data == "select_channels")
async def select_channels_menu(callback: types.CallbackQuery):
    """Выбор каналов"""
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
    await callback.message.edit_text("📺 Выберите каналы для пересылки:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("toggle_ch_"))
async def toggle_channel(callback: types.CallbackQuery):
    """Переключить канал"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён!")
        return
    
    channel_id = int(callback.data.split("_")[2])
    
    if channel_id in active_channels:
        active_channels.remove(channel_id)
        await callback.answer(f"➖ Канал отключен")
    else:
        active_channels.add(channel_id)
        await callback.answer(f"➕ Канал включен")
    
    # Обновляем меню
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

@dp.callback_query(F.data == "toggle_forward")
async def toggle_forwarding(callback: types.CallbackQuery):
    """Переключить пересылку"""
    global forwarding_enabled
    
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён!")
        return
    
    forwarding_enabled = not forwarding_enabled
    status = "🟢 Включена" if forwarding_enabled else "🔴 Отключена"
    
    await callback.answer(f"✅ Пересылка {status}")
    await callback.message.edit_text(f"📋 Админ панель\\n\\nПересылка: {status}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Выбрать каналы", callback_data="select_channels")],
        [InlineKeyboardButton(text="🔄 Переключить пересылку", callback_data="toggle_forward")],
        [InlineKeyboardButton(text="ℹ️ Статус", callback_data="status")],
    ]))

@dp.callback_query(F.data == "status")
async def show_status(callback: types.CallbackQuery):
    """Показать статус"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещён!")
        return
    
    forward_status = "🟢 Включена" if forwarding_enabled else "🔴 Отключена"
    active_count = len(active_channels)
    
    status_text = f"""📊 Статус бота
    
🔄 Пересылка: {forward_status}
📺 Активные каналы: {active_count}/{len(CHANNEL_NAMES)}

Каналы:"""
    
    for channel_id, name in CHANNEL_NAMES.items():
        status = "✅" if channel_id in active_channels else "❌"
        status_text += f"\\n  {status} {name}"
    
    await callback.message.edit_text(status_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад", callback_data="admin_menu")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_menu")
async def back_to_admin_menu(callback: types.CallbackQuery):
    """Вернуться в админ меню"""
    status = "🟢 Включена" if forwarding_enabled else "🔴 Отключена"
    await callback.message.edit_text(f"📋 Админ панель\\n\\nПересылка: {status}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Выбрать каналы", callback_data="select_channels")],
        [InlineKeyboardButton(text="🔄 Переключить пересылку", callback_data="toggle_forward")],
        [InlineKeyboardButton(text="ℹ️ Статус", callback_data="status")],
    ]))
    await callback.answer()

@dp.message()
async def forward_message(message: types.Message):
    """Пересылка сообщений"""
    # Проверяем источник и статус
    if message.chat.id != SOURCE_CHANNEL or not forwarding_enabled:
        return
    
    logger.info(f"Входящее сообщение из {message.chat.id}, пересылаем в {len(active_channels)} каналов")
    
    try:
        for channel_id in active_channels:
            await message.copy_to(channel_id)
            logger.info(f"✅ Сообщение переслано в {channel_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка пересылки: {e}")

async def main():
    logger.info(f"Бот запущен! Всего каналов: {len(TARGET_CHANNELS)}")
    for ch_id, name in CHANNEL_NAMES.items():
        logger.info(f"  {name}: {ch_id}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

