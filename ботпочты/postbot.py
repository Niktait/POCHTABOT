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
                   status TEXT,
                   payment_status TEXT)''')

# Функция для добавления посылки в базу данных
def add_parcel(tracking_number, owner_name, phone_number, status, payment_status):
    cursor.execute('''INSERT INTO parcels (tracking_number, owner_name, phone_number, status, payment_status) VALUES (?, ?, ?, ?, ?)''',
                   (tracking_number, owner_name, phone_number, status, payment_status))
    conn.commit()

# Добавляем пример данных в базу данных
add_parcel("123456789", "Иванов Иван", "+79101112233", "На складе", "Оплачено")
add_parcel("987654321", "Петров Петр", "+79112223344", "В пути", "Не оплачено")
add_parcel("135792468", "Сидоров Сергей", "+79123344556", "Доставлено", "Оплачено")
add_parcel("246813579", "Кузнецова Мария", "+79134455667", "На складе", "Не оплачено")
add_parcel("987654321", "Кузнецова Мария", "+79134455667", "В пути", "Оплачено")
add_parcel("112233445", "Смирнов Алексей", "+79156677889", "Доставлено", "Оплачено")
add_parcel("556677889", "Павлова Елена", "+79167788990", "На складе", "Не оплачено")
add_parcel("112233445", "Игнатова Ольга", "+79178899001", "В пути", "Оплачено")
add_parcel("223344556", "Федоров Федор", "+79189900112", "На складе", "Не оплачено")
add_parcel("445566778", "Денисов Денис", "+79190011223", "В пути", "Оплачено")




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
    keyboard.add(
        InlineKeyboardButton("Консультация", callback_data="consultation"),
    )
    keyboard.add(
        InlineKeyboardButton("Оплата", callback_data="payment"),
    )
    await message.answer(welcome_message, reply_markup=keyboard)


# Обработка кнопок в основном меню
@dp.callback_query_handler(lambda c: c.data in ["check_track_number", "find_phone_number", "consultation", "payment"])
async def process_main_menu(callback_query: types.CallbackQuery):
    action = callback_query.data
    if action == "check_track_number":
        await callback_query.message.answer("Введите трек-номер посылки:")
    elif action == "find_phone_number":
        await callback_query.message.answer("Введите номер телефона:")
    elif action == "consultation":
        # Обработка кнопок в меню консультации
        consultation_menu = InlineKeyboardMarkup()
        consultation_menu.add(
            InlineKeyboardButton("Города доставки", callback_data="delivery_cities"),
        )
        consultation_menu.add(
            InlineKeyboardButton("Расценки на доставку", callback_data="delivery_prices"),
        )
        consultation_menu.add(
            InlineKeyboardButton("Связь со специалистом", callback_data="contact_specialist"),
        )
        await callback_query.message.answer("Меню консультации", reply_markup=consultation_menu)
    elif action == "payment":
        # Отправить сообщение о способах оплаты и реквизитах
        payment_info = "Для оплаты свяжитесь с нашим менеджером. После чего вам будет выслана ссылка для оплаты.\n\n" \
                       "Реквизиты для оплаты:\n" \
                       "Банковский счет: 1234 5678 9012 3456\n" \
                       "БИК: 012345678\n" \
                       "ИНН: 1234567890\n" \
                       "КПП: 987654321\n"
        await callback_query.message.answer(payment_info)


# Обработка кнопок в меню консультации
@dp.callback_query_handler(lambda c: c.data in ["delivery_cities", "delivery_prices", "contact_specialist"])
async def process_consultation_menu(callback_query: types.CallbackQuery):
    action = callback_query.data
    if action == "delivery_cities":
        # Отправить список городов доставки
        delivery_cities = ["Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск", "Краснодар"]
        cities_message = "Города, в которых осуществляется доставка:\n" + "\n".join(delivery_cities)
        await callback_query.message.answer(cities_message)
    elif action == "delivery_prices":
        # Отправить информацию о расценках на доставку
        delivery_prices_message = "Расценки на доставку:\nЦена за километр: 10 рублей"
        await callback_query.message.answer(delivery_prices_message)
    elif action == "contact_specialist":
        # Отправить контактную информацию специалиста
        specialist_contact_info = "Связаться со специалистом для расчета стоимости доставки:\nТелефон: +7(XXX)XXX-XX-XX\nEmail: specialist@example.com"
        await callback_query.message.answer(specialist_contact_info)


# Обработка команды /help
@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    help_message = "Этот бот предназначен для отслеживания посылок. Используйте /start, чтобы начать."
    await message.answer(help_message)

# Функция для поиска посылки по трек-номеру
def find_parcel_by_tracking_number(tracking_number):
    cursor.execute('''SELECT * FROM parcels WHERE tracking_number = ?''', (tracking_number,))
    return cursor.fetchone()

# Функция для поиска посылок по номеру телефона владельца
def find_parcels_by_phone_number(phone_number):
    cursor.execute('''SELECT * FROM parcels WHERE phone_number = ?''', (phone_number,))
    return cursor.fetchall()

# Обработка введенного текста (трек-номера посылки или номера телефона)
@dp.message_handler()
async def handle_text(message: types.Message):
    text = message.text.strip().lower()  # Приведение к нижнему регистру
    # Если текст - трек-номер, ищем посылку по этому номеру
    if text.isdigit():
        parcel = find_parcel_by_tracking_number(text)
        if parcel:
            response = f"Посылка найдена!\n\nТрек-номер: {parcel[1]}\nВладелец: {parcel[2]}\nНомер телефона: {parcel[3]}\nСтатус: {parcel[4]}\nСтатус оплаты: {parcel[5]}"
        else:
            response = "Посылка с таким трек-номером не найдена."
    # Если текст - номер телефона, ищем посылки по этому номеру
    elif text.startswith('+') and text[1:].isdigit():
        parcels = find_parcels_by_phone_number(text)
        if parcels:
            response = "Найдены следующие посылки:\n\n"
            for parcel in parcels:
                response += f"Трек-номер: {parcel[1]}\nВладелец: {parcel[2]}\nСтатус: {parcel[4]}\nСтатус оплаты: {parcel[5]}\n\n"
        else:
            response = "Посылок с таким номером телефона не найдено."
    else:
        response = "Не удалось распознать введенные данные."
    
    await message.answer(response)


# Запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
