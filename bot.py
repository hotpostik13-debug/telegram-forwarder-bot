import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import BaseFilter, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL", "-1004298123113"))
TARGET_CHANNELS = [int(ch.strip()) for ch in os.getenv("TARGET_CHANNELS", "-1003926649756,-1003957721628,-1003744353491,-1004316696837,-1003991682451").split(",")]
ADMIN_ID = int(os.getenv("ADMIN_ID", "918395366"))
# ===================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояние бота (простой ручной тумблер)
IS_RUNNING = True 

class SourceChannelFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        if message.chat:
            return message.chat.id == SOURCE_CHANNEL
        return False

# Сборка пульта управления
def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    
    status_icon = "⏸" if IS_RUNNING else "▶️"
    builder.button(text=f"{status_icon} Ручной стоп/старт", callback_data="toggle_bot")
    builder.button(text="🔄 Перезагрузить бота", callback_data="reboot_bot")
    
    builder.adjust(1)
    return builder.as_markup()

@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_menu(message: types.Message):
    status_text = "Работает" if IS_RUNNING else "На паузе"
    await message.answer(
        f"Пульт управления бота.\n\n"
        f"Текущий статус: {status_text}\n",
        reply_markup=get_admin_keyboard()
    )

@dp.callback_query(F.from_user.id == ADMIN_ID)
async def handle_buttons(callback: types.CallbackQuery):
    global IS_RUNNING
    
    action = callback.data
    
    if action == "toggle_bot":
        IS_RUNNING = not IS_RUNNING
        await callback.answer(f"Статус изменен")
    
    elif action == "reboot_bot":
        await callback.answer("Бот уходит на перезагрузку...", show_alert=True)
        await bot.session.close()
        sys.exit(0)
    
    try:
        status_text = "Работает" if IS_RUNNING else "На паузе"
        await callback.message.edit_text(
            f"Пульт управления бота.\n\n"
            f"Текущий статус: {status_text}\n",
            reply_markup=get_admin_keyboard()
        )
    except Exception:
        pass

@dp.channel_post(SourceChannelFilter())
async def handle_channel_post(message: types.Message):
    # Если админ нажал паузу — ничего не пересылаем
    if not IS_RUNNING:
        return
    
    # Пересылаем сообщение во все целевые каналы в исходном виде
    for channel_id in TARGET_CHANNELS:
        try:
            await message.copy_to(channel_id)
        except Exception as e:
            logging.error(f"Ошибка отправки в канал {channel_id}: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

