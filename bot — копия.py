import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Конфигурация
BOT_TOKEN = ""
VIDEO_FOLDER = "videos"

# Создаем папку для видео, если её нет
if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Хранилище данных пользователей
user_data = {}
timer_tasks = {}

# Состояния FSM
class UserStates(StatesGroup):
    waiting_for_russian = State()
    confirmed = State()

# Функция для проверки русского языка (простейшая проверка)
def is_russian_text(text: str) -> bool:
    russian_letters = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    text_lower = text.lower()
    
    # Проверяем, есть ли хотя бы одна русская буква
    has_russian = any(char in russian_letters for char in text_lower)
    
    # Проверяем процент русских символов (должно быть больше 50%)
    if has_russian:
        total_chars = len([c for c in text_lower if c.isalpha()])
        if total_chars > 0:
            russian_count = len([c for c in text_lower if c in russian_letters])
            return (russian_count / total_chars) > 0.5
    
    return False

# Функция для запуска таймера
async def start_timer(user_id: int, state: FSMContext):
    if user_id in timer_tasks and not timer_tasks[user_id].done():
        timer_tasks[user_id].cancel()
    
    # Сохраняем время начала попытки
    user_data[user_id]['attempt_start'] = datetime.now()
    
    async def timer_callback():
        await asyncio.sleep(60)  # 1 минута
        
        # Проверяем, подтвердил ли пользователь за это время
        current_state = await state.get_state()
        if current_state != UserStates.confirmed.state:
            user_data[user_id]['attempts_left'] -= 1
            
            if user_data[user_id]['attempts_left'] > 0:
                await bot.send_message(
                    user_id,
                    f"⏰ Время вышло! У вас осталось {user_data[user_id]['attempts_left']} попыток.\n"
                    f"Напишите любое сообщение на русском языке в течение минуты:"
                )
                # Запускаем таймер заново для новой попытки
                await start_timer(user_id, state)
            else:
                await bot.send_message(
                    user_id,
                    "❌ Попытки закончились. Вы не подтвердили, что вы русский."
                )
                await state.clear()
                if user_id in user_data:
                    del user_data[user_id]
    
    timer_tasks[user_id] = asyncio.create_task(timer_callback())

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if user_id in user_data:
        await message.answer("Вы уже зарегистрированы!")
        return
    
    # Регистрируем пользователя
    user_data[user_id] = {
        'attempts_left': 5,
        'registered': True,
        'attempt_start': None
    }
    
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Для продолжения вам нужно подтвердить, что вы русский.\n"
        "Напишите любое сообщение на русском языке в течение 1 минуты.\n\n"
        "У вас есть 5 попыток."
    )
    
    await state.set_state(UserStates.waiting_for_russian)
    await start_timer(user_id, state)

# Обработка текстовых сообщений для проверки русского языка
@dp.message(UserStates.waiting_for_russian, F.text)
async def check_russian(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        await message.answer("Сначала зарегистрируйтесь с помощью /start")
        return
    
    if is_russian_text(message.text):
        # Отменяем таймер
        if user_id in timer_tasks and not timer_tasks[user_id].done():
            timer_tasks[user_id].cancel()
        
        user_data[user_id]['confirmed'] = True
        await state.set_state(UserStates.confirmed)
        
        await message.answer(
            "✅ Отлично! Вы подтвердили, что вы русский.\n\n"
            "Теперь вам доступны функции:\n"
            "1. /status - Посмотреть количество видео на хостинге\n"
            "2. Просто отправьте видео в формате MP4 с описанием (название файла)"
        )
    else:
        user_data[user_id]['attempts_left'] -= 1
        
        if user_data[user_id]['attempts_left'] > 0:
            await message.answer(
                f"❌ Это не похоже на русский текст. Осталось попыток: {user_data[user_id]['attempts_left']}\n"
                f"Попробуйте еще раз в течение минуты:"
            )
            # Перезапускаем таймер для новой попытки
            await start_timer(user_id, state)
        else:
            await message.answer("❌ Попытки закончились. Вы не подтвердили, что вы русский.")
            await state.clear()
            if user_id in user_data:
                del user_data[user_id]

# Команда /status
@dp.message(Command("status"), UserStates.confirmed)
async def cmd_status(message: Message):
    video_files = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith('.mp4')]
    count = len(video_files)
    
    await message.answer(f"📁 В хостинге находится {count} видеофайлов в формате MP4.")
    
    if count > 0:
        file_list = "\n".join([f"{i+1}. {f}" for i, f in enumerate(video_files[:10])])
        if count > 10:
            file_list += f"\n... и еще {count-10} файлов"
        await message.answer(f"Список файлов:\n{file_list}")

# Обработка загрузки видео
@dp.message(UserStates.confirmed, F.video)
async def handle_video(message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        await message.answer("Сначала зарегистрируйтесь с помощью /start")
        return
    
    video = message.video
    
    # Проверяем формат
    if not video.mime_type == "video/mp4":
        await message.answer("❌ Пожалуйста, отправляйте видео только в формате MP4")
        return
    
    # Получаем название файла из описания или используем оригинальное название
    if message.caption:
        filename = message.caption.strip()
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        # Очищаем название от недопустимых символов
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '-', '_')).strip()
        if not filename:
            filename = video.file_name if video.file_name else f"video_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    else:
        filename = video.file_name if video.file_name else f"video_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    
    # Скачиваем видео
    file_info = await bot.get_file(video.file_id)
    file_path = os.path.join(VIDEO_FOLDER, filename)
    
    try:
        await bot.download_file(file_info.file_path, file_path)
        await message.answer(f"✅ Видео успешно сохранено как: {filename}")
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении видео: {str(e)}")

# Обработка не MP4 видео
@dp.message(UserStates.confirmed, F.content_type.in_({'video'}))
async def handle_non_mp4_video(message: Message):
    await message.answer("❌ Пожалуйста, отправляйте видео только в формате MP4")

# Запуск бота
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())