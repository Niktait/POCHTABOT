import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from config import BOT_TOKEN

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Подключаемся к базе данных
conn = sqlite3.connect('post_tracking.db')
cursor = conn.cursor()




# Создаем таблицу для хранения информации о посылках, если она еще не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS parcels
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   tracking_number TEXT,
                   owner_name TEXT,
                   phone_number TEXT,
                   status TEXT)''')

# Функция для добавления посылки в базу данных
def add_parcel(tracking_number, owner_name, phone_number, status):
    cursor.execute('''INSERT INTO parcels (tracking_number, owner_name, phone_number, status) VALUES (?, ?, ?, ?)''',
                   (tracking_number, owner_name, phone_number, status))
    conn.commit()

# Функция для поиска посылки по трек-номеру
def find_parcel_by_tracking_number(tracking_number):
    cursor.execute('''SELECT * FROM parcels WHERE tracking_number = ?''', (tracking_number,))
    return cursor.fetchone()

# Функция для поиска посылок по номеру телефона владельца
def find_parcels_by_phone_number(phone_number):
    cursor.execute('''SELECT * FROM parcels WHERE phone_number = ?''', (phone_number,))
    return cursor.fetchall()

# Добавляем пример данных в базу данных
add_parcel("123456789", "Иванов Иван", "+79101112233", "На складе")
add_parcel("987654321", "Петров Петр", "+79112223344", "В пути")
add_parcel("135792468", "Сидоров Сергей", "+79123344556", "Доставлено")
add_parcel("246813579", "Кузнецова Мария", "+79134455667", "На складе")
add_parcel("987654321", "Кузнецова Мария", "+79134455667", "В пути")
add_parcel("112233445", "Смирнов Алексей", "+79156677889", "Доставлено")
add_parcel("556677889", "Павлова Елена", "+79167788990", "На складе")
add_parcel("112233445", "Игнатова Ольга", "+79178899001", "В пути")
add_parcel("223344556", "Федоров Федор", "+79189900112", "На складе")
add_parcel("445566778", "Денисов Денис", "+79190011223", "В пути")



# Остальной код бота
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    welcome_message = f"Привет, {user_name}! Я бот для отслеживания посылок по трек-номерам и номеру телефона."
    # Создаем InlineKeyboard
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Проверить по трек-номеру", callback_data="check_track_number"),
    )
    keyboard.add(
        InlineKeyboardButton("Найти по номеру телефона", callback_data="find_phone_number"),
    )
    await message.answer(welcome_message, reply_markup=keyboard)

# Обработка команды /help
@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    help_message = "Этот бот предназначен для отслеживания посылок. Используйте /start, чтобы начать."
    await message.answer(help_message)

# Обработка кнопок Check by track number и Find by phone number
@dp.callback_query_handler(lambda c: c.data in ["check_track_number", "find_phone_number"])
async def process_callback(callback_query: types.CallbackQuery):
    action = callback_query.data
    if action == "check_track_number":
        await callback_query.message.answer("Введите трек-номер посылки:")
    elif action == "find_phone_number":
        await callback_query.message.answer("Введите номер телефона:")

# Обработка введенного текста (трек-номера посылки или номера телефона)
@dp.message_handler()
async def handle_text(message: types.Message):
    text = message.text.strip().lower()  # Приведение к нижнему регистру
    # Если текст - трек-номер, ищем посылку по этому номеру
    if text.isdigit():
        parcel = find_parcel_by_tracking_number(text)
        if parcel:
            response = f"Посылка найдена!\n\nТрек-номер: {parcel[1]}\nВладелец: {parcel[2]}\nНомер телефона: {parcel[3]}\nСтатус: {parcel[4]}"
        else:
            response = "Посылка с таким трек-номером не найдена."
    # Если текст - номер телефона, ищем посылки по этому номеру
    elif text.startswith('+') and text[1:].isdigit():
        parcels = find_parcels_by_phone_number(text)
        if parcels:
            response = "Найдены следующие посылки:\n\n"
            for parcel in parcels:
                response += f"Трек-номер: {parcel[1]}\nВладелец: {parcel[2]}\nСтатус: {parcel[4]}\n\n"
        else:
            response = "Посылок с таким номером телефона не найдено."
    else:
        response = "Не удалось распознать введенные данные."
    
    await message.answer(response)

# Запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
