import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
import config
from aiogram.dispatcher.filters import Text
import os
import shutil
import sys
import subprocess
import tempfile
import random
import string
from tokens import TokenManager
from dotenv import load_dotenv
import aiohttp
from aiohttp import web
import logging

# Данные для работы магазина
CITIES = ["Москва", "Санкт-Петербург", "Казань"]
DISTRICTS = {
    "Москва": ["Центральный", "Южный", "Северный"],
    "Санкт-Петербург": ["Центральный", "Васильевский", "Петроградский"],
    "Казань": ["Вахитовский", "Советский", "Приволжский"]
}
PICKUP_POINTS = {
    "Москва": {
        "Центральный": ["ул. Тверская, 1", "Пушкинская площадь, 2", "ул. Арбат, 15"],
        "Южный": ["Варшавское шоссе, 26", "Каширское шоссе, 10", "ул. Чертановская, 5"],
        "Северный": ["Ленинградский пр., 20", "ул. Дубнинская, 7", "Дмитровское шоссе, 12"]
    },
    "Санкт-Петербург": {
        "Центральный": ["Невский пр., 1", "ул. Садовая, 5", "Литейный пр., 10"],
        "Васильевский": ["6-я линия В.О., 3", "Большой пр. В.О., 8", "Малый пр. В.О., 15"],
        "Петроградский": ["Большой пр. П.С., 18", "Каменноостровский пр., 25", "ул. Куйбышева, 30"]
    },
    "Казань": {
        "Вахитовский": ["ул. Баумана, 12", "ул. Кремлевская, 5", "ул. Пушкина, 8"],
        "Советский": ["ул. Гвардейская, 20", "пр. Победы, 15", "ул. Космонавтов, 10"],
        "Приволжский": ["ул. Авангардная, 7", "пр. Ямашева, 30", "ул. Фучика, 15"]
    }
}
PAYMENT_METHODS = ["VISA/MasterCard", "МИР"]

# Инициализация
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database('shop.db')

# Создаем экземпляр TokenManager
token_manager = TokenManager()

# Состояния FSM
class OrderStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_product = State()
    waiting_for_district = State()
    waiting_for_pickup = State()
    waiting_for_payment = State()

class AdminStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_city = State()
    waiting_for_district = State()
    waiting_for_pickup = State()

# Добавим новое состояние для создания бота
class CreateBotState(StatesGroup):
    waiting_for_token = State()

# Клавиатуры
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🛍 Изменить город", callback_data="change_city")
    )
    return keyboard

# Обработчики команд
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.username)
    
    # Создаем клавиатуру с городами и дополнительными кнопками
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Сначала добавляем города
    for city in CITIES:
        keyboard.add(InlineKeyboardButton(city, callback_data=f"city_{city}"))
    
    # Добавляем дополнительные кнопки в одну строку
    keyboard.row(
        InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        InlineKeyboardButton("🛒 Мои заказы", callback_data="orders"),
        InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
    )
    # Добавляем кнопку "Поделиться ботом"
    keyboard.row(InlineKeyboardButton("🤖 Создать своего бота", callback_data="share_bot"))
    
    await message.answer(
        f"👋 Добро пожаловать в наш магазин, {message.from_user.first_name}!\n\n"
        "🌆 Выберите ваш город:",
        reply_markup=keyboard
    )

@dp.callback_query_handler(text="catalog")
async def show_catalog(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for city in CITIES:
        keyboard.add(InlineKeyboardButton(city, callback_data=f"city_{city}"))
    await callback.message.answer("🌆 Выберите город:", reply_markup=keyboard)

@dp.callback_query_handler(text_startswith="city_")
async def choose_city(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split('_')[1]
    await state.update_data(city=city)
    
    products = db.get_all_products(city)
    if not products:
        await callback.message.answer(
            f"😕 В каталоге нет товаров для города {city}",
            reply_markup=get_main_keyboard()
        )
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    for product in products:
        keyboard.add(InlineKeyboardButton(f"{product[1]} - {product[3]}₽", 
                                        callback_data=f"product_{product[0]}"))
    
    # Показываем только товары с кнопкой изменения города
    await callback.message.answer(
        "🛍 Доступные товары:", 
        reply_markup=keyboard
    )
    
    await OrderStates.waiting_for_product.set()

@dp.callback_query_handler(text_startswith="product_", state=OrderStates.waiting_for_product)
async def choose_product(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[1])
    product = db.get_product(product_id)
    await state.update_data(product_id=product_id, product_name=product[1], price=product[3])
    
    data = await state.get_data()
    city = data['city']
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    for district in DISTRICTS[city]:
        keyboard.add(InlineKeyboardButton(district, callback_data=f"district_{district}"))
    
    await callback.message.answer("🏘 Выберите район:", reply_markup=keyboard)
    await OrderStates.waiting_for_district.set()

@dp.callback_query_handler(text_startswith="district_", state=OrderStates.waiting_for_district)
async def choose_district(callback: types.CallbackQuery, state: FSMContext):
    district = callback.data.split('_')[1]
    await state.update_data(district=district)
    
    data = await state.get_data()
    city = data['city']
    
    # Создаем клавиатуру с пунктами выдачи
    keyboard = InlineKeyboardMarkup(row_width=1)
    for pickup in PICKUP_POINTS[city][district]:
        keyboard.add(InlineKeyboardButton(pickup, callback_data=f"pickup_{pickup}"))
    
    await callback.message.answer("📍 Выберите пункт выдачи:", reply_markup=keyboard)
    await OrderStates.waiting_for_pickup.set()

# Функция для генерации уникального ID заказа
def generate_order_id():
    letters = string.ascii_uppercase
    numbers = string.digits
    return ''.join(random.choice(letters) for _ in range(2)) + ''.join(random.choice(numbers) for _ in range(4))

# Изменим обработчик выбора пункта выдачи
@dp.callback_query_handler(text_startswith="pickup_", state=OrderStates.waiting_for_pickup)
async def choose_pickup(callback: types.CallbackQuery, state: FSMContext):
    pickup = callback.data.split('_')[1]
    await state.update_data(pickup_point=pickup)
    
    data = await state.get_data()
    
    # Генерируем уникальный ID заказа
    order_id = generate_order_id()
    await state.update_data(order_id=order_id)
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💳 Оплатить", callback_data="pay"),
        InlineKeyboardButton("❌ Отменить", callback_data="cancel")
    )
    
    await callback.message.answer(
        f"📋 Подтвердите заказ:\n\n"
        f"🌆 ID заказа: #{order_id}\n"
        f"🌆 Город: {data['city']}\n"
        f"🏘 Район: {data['district']}\n"
        f"📍 Пункт выдачи: {pickup}\n"
        f"🛍 Товар: {data['product_name']}\n"
        f"💰 Цена: {data['price']}₽",
        reply_markup=keyboard
    )
    await OrderStates.waiting_for_payment.set()

@dp.callback_query_handler(text="cancel", state="*")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    
    # Создаем клавиатуру как в команде /start
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Добавляем города
    for city in CITIES:
        keyboard.add(InlineKeyboardButton(city, callback_data=f"city_{city}"))
    
    # Добавляем дополнительные кнопки
    keyboard.row(
        InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        InlineKeyboardButton("🛒 Мои заказы", callback_data="orders"),
        InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
    )
    # Добавляем кнопку создания бота
    keyboard.row(InlineKeyboardButton("🤖 Создать своего бота", callback_data="share_bot"))
    
    await callback.message.answer(
        f"❌ Заказ отменен\n\n"
        f"👋 Добро пожаловать в наш магазин, {callback.from_user.first_name}!\n\n"
        "🌆 Выберите ваш город:",
        reply_markup=keyboard
    )

@dp.callback_query_handler(text="pay", state=OrderStates.waiting_for_payment)
async def choose_payment(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for method in PAYMENT_METHODS:
        keyboard.add(InlineKeyboardButton(method, callback_data=f"payment_{method}"))
    
    await callback.message.answer("💳 Выберите способ оплаты:", reply_markup=keyboard)
    await OrderStates.waiting_for_payment.set()

@dp.callback_query_handler(text_startswith="payment_", state=OrderStates.waiting_for_payment)
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    payment_method = callback.data.split('_')[1]
    data = await state.get_data()
    
    # Сохраняем заказ в базе данных
    db.add_order(data['order_id'], callback.from_user.id, data['product_id'])
    
    await callback.message.answer(
        f"💰 К оплате: {data['price']}₽\n\n"
        f"🆔 ID заказа: #{data['order_id']}\n"
        f"🆔 Способ оплаты: {payment_method}\n"
        f"⚠️ Это демо-версия бота, оплата не производится"
    )
    
    await state.finish()

@dp.callback_query_handler(text="balance")
async def show_balance(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💳 Пополнить", callback_data="add_money"))
    
    await callback.message.answer(
        f"💰 Ваш баланс: {user[2]}₽",
        reply_markup=keyboard
    )

@dp.callback_query_handler(text="help")
async def show_help(callback: types.CallbackQuery):
    await callback.message.answer(
        "ℹ️ Помощь по использованию бота:\n\n"
        "1. Для просмотра товаров нажмите «Каталог»\n"
        "2. Для просмотра баланса нажмите «Баланс»\n"
        "3. Для просмотра заказов нажмите «Мои заказы»\n\n"
        "По всем вопросам обращайтесь к администратору: @admin"
    )

@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("❌ У вас нет доступа к панели администратора!")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить товар", callback_data="add_product"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("🗑 Удалить товар", callback_data="delete_product"),
        InlineKeyboardButton("📢 Рассылка", callback_data="broadcast")
    )
    await message.answer("👨‍💼 Панель администратора:", reply_markup=keyboard)

@dp.callback_query_handler(text="add_product")
async def add_product_start(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.message.answer("❌ У вас нет доступа к этой функции!")
        return
    
    await AdminStates.waiting_for_name.set()
    await callback.message.answer("📝 Введите название товара:")

@dp.message_handler(state=AdminStates.waiting_for_name)
async def add_product_name(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await state.finish()
        return
    
    await state.update_data(name=message.text)
    await AdminStates.waiting_for_description.set()
    await message.answer("📝 Введите описание товара:")

@dp.message_handler(state=AdminStates.waiting_for_description)
async def add_product_description(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await state.finish()
        return
    
    await state.update_data(description=message.text)
    await AdminStates.waiting_for_price.set()
    await message.answer("💰 Введите цену товара (только число):")

@dp.message_handler(state=AdminStates.waiting_for_price)
async def add_product_price(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await state.finish()
        return
    
    try:
        price = float(message.text)
        await state.update_data(price=price)
        
        # Создаем клавиатуру с городами
        keyboard = InlineKeyboardMarkup(row_width=2)
        for city in CITIES:
            keyboard.add(InlineKeyboardButton(city, callback_data=f"addcity_{city}"))
        
        await AdminStates.waiting_for_city.set()
        await message.answer("🌆 Выберите город для товара:", reply_markup=keyboard)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену (только число)!")

# Добавляем новый обработчик для выбора города
@dp.callback_query_handler(text_startswith="addcity_", state=AdminStates.waiting_for_city)
async def add_product_city(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await state.finish()
        return
    
    city = callback.data.split('_')[1]
    await state.update_data(city=city)
    
    # Создаем клавиатуру с районами
    keyboard = InlineKeyboardMarkup(row_width=2)
    for district in DISTRICTS[city]:
        keyboard.add(InlineKeyboardButton(district, callback_data=f"adddistrict_{district}"))
    
    await AdminStates.waiting_for_district.set()
    await callback.message.answer("🏘 Выберите район:", reply_markup=keyboard)

# Добавим новый обработчик для выбора района
@dp.callback_query_handler(text_startswith="adddistrict_", state=AdminStates.waiting_for_district)
async def add_product_district(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await state.finish()
        return
    
    district = callback.data.split('_')[1]
    await state.update_data(district=district)
    
    # Получаем город и состояния
    data = await state.get_data()
    city = data['city']
    
    # Создаем клавиатуру с пунктами выдачи для выбранного города и района
    keyboard = InlineKeyboardMarkup(row_width=1)
    for pickup in PICKUP_POINTS[city][district]:
        keyboard.add(InlineKeyboardButton(pickup, callback_data=f"addpickup_{pickup}"))
    
    await AdminStates.waiting_for_pickup.set()
    await callback.message.answer("📍 Выберите пункт выдачи:", reply_markup=keyboard)

# Добавим обработчик для пункта выдачи
@dp.callback_query_handler(text_startswith="addpickup_", state=AdminStates.waiting_for_pickup)
async def add_product_pickup(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await state.finish()
        return
    
    pickup = callback.data.split('_')[1]
    data = await state.get_data()
    
    # Добавляем товар в базу данных
    db.add_product(data['name'], data['description'], data['price'], 
                  data['city'], data['district'], pickup)
    await state.finish()
    
    await callback.message.answer(
        "✅ Товар успешно добавлен в каталог!\n\n"
        f"📦 Товар: {data['name']}\n"
        f"💰 Цена: {data['price']}₽\n"
        f"🌆 Город: {data['city']}\n"
        f"🏘 Район: {data['district']}\n"
        f"📍 Пункт выдачи: {pickup}"
    )

# Добавим обработчик для кнопки "Изменить город"
@dp.callback_query_handler(text="change_city")
async def change_city(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Сначала добавляем города
    for city in CITIES:
        keyboard.add(InlineKeyboardButton(city, callback_data=f"city_{city}"))
    
    # Добавляем дополнительные кнопки в одну строку
    keyboard.row(
        InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        InlineKeyboardButton("🛒 Мои заказы", callback_data="orders"),
        InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
    )
    
    await callback.message.answer("🌆 Выберите город:", reply_markup=keyboard)

# Добавим обработчик статистики
@dp.callback_query_handler(text="admin_stats")
async def show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        return
    
    stats = db.get_stats()
    
    city_info = "\n".join([f"- {city}: {count} товаров" for city, count in stats['city_stats']])
    creators_info = "\n".join([
        f"- @{username}: {count} ботов" for username, count in stats['top_creators']
    ]) or "Пока нет данных"
    
    await callback.message.answer(
        "📊 Статистика магазина:\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"📦 Всего товаров: {stats['total_products']}\n"
        f"🛒 Всего заказов: {stats['total_orders']}\n"
        f"💰 Общая сумма заказов: {stats['total_sum']}₽\n\n"
        f"🌆 Создано ботов: {stats['total_bots']}\n"
        f"🏆 Топ создателей ботов:\n{creators_info}\n\n"
        f"🌆 Товары по городам:\n{city_info}"
    )

# Добавим обработчик удаления товаров
@dp.callback_query_handler(text="delete_product")
async def show_products_for_deletion(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        return
    
    products = db.get_all_products()
    if not products:
        await callback.message.answer("❌ В каталоге нет товаров")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for product in products:
        keyboard.add(InlineKeyboardButton(
            f"{product[1]} ({product[4]})", 
            callback_data=f"del_product_{product[0]}"
        ))
    
    await callback.message.answer("🗑 Выберите товар для удаления:", reply_markup=keyboard)

@dp.callback_query_handler(text_startswith="del_product_")
async def delete_product(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        return
    
    product_id = int(callback.data.split('_')[2])
    db.delete_product(product_id)
    await callback.message.answer("✅ Товар успешно удален")

# Добавим рассылку всем пользователям
class BroadcastState(StatesGroup):
    waiting_for_message = State()

@dp.callback_query_handler(text="broadcast")
async def broadcast_start(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        return
    
    await BroadcastState.waiting_for_message.set()
    await callback.message.answer("📝 Введите текст рассылки:")

@dp.message_handler(state=BroadcastState.waiting_for_message)
async def broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await state.finish()
        return
    
    users = db.cursor.execute('SELECT user_id FROM users').fetchall()
    sent = 0
    
    await message.answer("📤 Начинаю рассылку...")
    
    for user in users:
        try:
            await bot.send_message(user[0], message.text)
            sent += 1
            await asyncio.sleep(0.1)  # Задержка между отправками
        except Exception:
            continue
    
    await message.answer(f"✅ Рассылка завершена\nСообщение получили {sent} пользователей")
    await state.finish()

# Добавим просмотр заказов для пользователей
@dp.callback_query_handler(text="orders")
async def show_user_orders(callback: types.CallbackQuery):
    orders = db.get_user_orders(callback.from_user.id)
    
    if not orders:
        await callback.message.answer("😕 У вас пока нет заказов")
        return
    
    text = "🛒 Ваши заказы:\n\n"
    for order in orders:
        text += (f"🆔 Заказ #{order[0]}\n"
                f"📦 Товар: {order[1]}\n"
                f"💰 Сумма: {order[2]}₽\n"
                f"📅 Дата: {order[3]}\n"
                f"📋 Статус: {order[4]}\n\n")
    
    await callback.message.answer(text)

# Добавим обработчик кнопки "Поделиться ботом"
@dp.callback_query_handler(text="share_bot")
async def share_bot(callback: types.CallbackQuery):
    await callback.message.answer(
        "🤖 Как создать своего бота:\n\n"
        "1. Перейдите к @BotFather\n"
        "2. Отправьте команду /newbot\n"
        "3. Следуйте инструкциям для создания бота\n"
        "4. Получите токен бота\n"
        "5. Отправьте токен в этот чат\n\n"
        "⚠️ Внимание: токен должен начинаться с цифр и содержать ':'",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Отмена", callback_data="cancel_create")
        )
    )
    await CreateBotState.waiting_for_token.set()

# Добавим обработчик отмены создания бота
@dp.callback_query_handler(text="cancel_create", state=CreateBotState.waiting_for_token)
async def cancel_create_bot(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.answer("❌ Создание бота отменено")

# Словарь для хранения запущенных ботов
running_bots = {}

# Добавим словарь для хранения веб-приложений ботов
bot_apps = {}
WEBHOOK_HOST = 'your_domain.com'  # Замените на ваш домен
WEBHOOK_PORT = 8443  # Порт для webhook

# Добавим функцию для регистрации всех обработчиков
def register_all_handlers(dp, bot):
    # Регистрируем все обработчики команд
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_callback_query_handler(show_catalog, text="catalog")
    dp.register_callback_query_handler(choose_city, text_startswith="city_")
    dp.register_callback_query_handler(choose_product, text_startswith="product_", state=OrderStates.waiting_for_product)
    dp.register_callback_query_handler(choose_district, text_startswith="district_", state=OrderStates.waiting_for_district)
    dp.register_callback_query_handler(choose_pickup, text_startswith="pickup_", state=OrderStates.waiting_for_pickup)
    dp.register_callback_query_handler(cancel_order, text="cancel", state="*")
    dp.register_callback_query_handler(choose_payment, text="pay", state=OrderStates.waiting_for_payment)
    dp.register_callback_query_handler(process_payment, text_startswith="payment_", state=OrderStates.waiting_for_payment)
    dp.register_callback_query_handler(show_balance, text="balance")
    dp.register_callback_query_handler(show_help, text="help")
    dp.register_callback_query_handler(change_city, text="change_city")
    dp.register_callback_query_handler(show_user_orders, text="orders")
    dp.register_message_handler(admin_panel, commands=['admin'])
    dp.register_callback_query_handler(add_product_start, text="add_product")
    dp.register_callback_query_handler(show_stats, text="admin_stats")
    dp.register_callback_query_handler(show_products_for_deletion, text="delete_product")
    dp.register_callback_query_handler(delete_product, text_startswith="del_product_")
    dp.register_callback_query_handler(broadcast_start, text="broadcast")
    dp.register_callback_query_handler(share_bot, text="share_bot")
    
    # Регистрируем обработчики состояний
    dp.register_message_handler(add_product_name, state=AdminStates.waiting_for_name)
    dp.register_message_handler(add_product_description, state=AdminStates.waiting_for_description)
    dp.register_message_handler(add_product_price, state=AdminStates.waiting_for_price)
    dp.register_callback_query_handler(add_product_city, text_startswith="addcity_", state=AdminStates.waiting_for_city)
    dp.register_callback_query_handler(add_product_district, text_startswith="adddistrict_", state=AdminStates.waiting_for_district)
    dp.register_callback_query_handler(add_product_pickup, text_startswith="addpickup_", state=AdminStates.waiting_for_pickup)
    dp.register_message_handler(broadcast_send, state=BroadcastState.waiting_for_message)
    dp.register_callback_query_handler(cancel_create_bot, text="cancel_create", state=CreateBotState.waiting_for_token)
    dp.register_message_handler(process_token, state=CreateBotState.waiting_for_token)

# Изменим обработчик получения токена
@dp.message_handler(state=CreateBotState.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    token = message.text.strip()
    
    if ':' not in token or not token.split(':')[0].isdigit():
        await message.answer(
            "❌ Неверный формат токена. Токен должен начинаться с цифр и содержать ':'\n"
            "Попробуйте еще раз или нажмите 'Отмена'"
        )
        return
    
    try:
        # Проверяем валидность токена
        new_bot = Bot(token=token)
        bot_info = await new_bot.get_me()
        session = await new_bot.get_session()
        await session.close()
        
        # Сохраняем информацию о созданном боте
        db.add_created_bot(message.from_user.id, bot_info.username, token)
        
        # Сохраняем токен в файл
        token_manager.add_token(
            token,
            bot_info.username,
            message.from_user.id,
            message.from_user.username or "Unknown"
        )
        
        # Создаем новый файл конфигурации для бота
        bot_folder = f"bots/{bot_info.username}"
        os.makedirs(bot_folder, exist_ok=True)
        
        # Копируем все необходимые файлы
        files_to_copy = ['main.py', 'database.py', 'tokens.py', 'config.py']
        for file in files_to_copy:
            shutil.copy2(file, bot_folder)
        
        # Создаем config.py для нового бота
        config_content = f"""BOT_TOKEN = "{token}"
ADMIN_ID = {config.ADMIN_ID}"""
        
        with open(os.path.join(bot_folder, 'config.py'), 'w') as f:
            f.write(config_content)
        
        # Запускаем бота в отдельном процессе
        subprocess.Popen(
            ['python3', 'main.py'] if os.name != 'nt' else ['python', 'main.py'],
            cwd=bot_folder,
            env={**os.environ, 'PYTHONPATH': bot_folder}
        )
        
        await message.answer(
            f"✅ Бот @{bot_info.username} успешно запущен!\n\n"
            "🚀 Перейдите к боту и нажмите /start"
        )
        
    except Exception as e:
        await message.answer(
            "❌ Ошибка при создании бота. Проверьте токен и попробуйте снова.\n"
            f"Ошибка: {str(e)}"
        )
    finally:
        await state.finish()

# Добавим команду для просмотра токенов (только для админа)
@dp.message_handler(commands=['tokens'])
async def show_tokens(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой функции!")
        return
    
    tokens = token_manager.get_all_tokens()
    if not tokens:
        await message.answer("🤖 Пока нет созданных ботов")
        return
    
    text = "📋 Список всех созданных ботов:\n\n"
    for token_info in tokens:
        text += token_manager.format_token_info(token_info) + "\n\n"
    
    await message.answer(text)

# Добавим команду для просмотра своих ботов
@dp.message_handler(commands=['mybots'])
async def show_my_bots(message: types.Message):
    tokens = token_manager.get_user_tokens(message.from_user.id)
    if not tokens:
        await message.answer("🤖 У вас пока нет созданных ботов")
        return
    
    text = "🤖 Ваши боты:\n\n"
    for token_info in tokens:
        text += f"@{token_info['bot_username']}\n"
        text += f"📅 Создан: {token_info['created_at']}\n\n"
    
    await message.answer(text)

# Изменим функцию main
async def main():
    # Настраиваем логирование
    logging.basicConfig(level=logging.INFO)
    
    # Создаем папку для ботов, если её нет
    os.makedirs('bots', exist_ok=True)
    
    # Запускаем основного бота
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
