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

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Данные для работы магазина
CITIES = [
    "🏢Ноябрьск", "🏢Нижневартовск", "🏢Ханты-Мансийск", "🏢Когалым", "🏢Губкинский", "🏢Лабытнанги",
    "🏢Салехард", "🏢Советский", "🏢Югорск", "🏢Новый Уренгой", "🏢Муравленко", "🏢Излучинск",
    "🏢Коротчаево", "🏢Стрежевой", "🏢Тарко-Сале", "🏢Мегион", "🏢Урай", "🏢Вынгапуровский",
    "🏢Пангоды", "🏢Надым", "🏢Нягань", "🏢Радужный", "🏢Старый Уренгой", "🏢Междуреченский",
    "🏢Пурпе", "🏢Пуровск", "🏢Покачи", "🏢Белоярский", "🏢Лангепас", "🏢Талинка"
]
DISTRICTS = {
    "🏢Ноябрьск": ["🌆Город🌆"],
    "🏢Нижневартовск": ["🌆Город🌆"],
    "🏢Ханты-Мансийск": ["🌆Город🌆"],
    "🏢Когалым": ["🌆Город🌆"],
    "🏢Губкинский": ["🌆Город🌆"],
    "🏢Лабытнанги": ["🌆Город🌆"],
    "🏢Салехард": ["🌆Город🌆"],
    "🏢Советский": ["🌆Город🌆"],
    "🏢Югорск": ["🌆Город🌆"],
    "🏢Новый Уренгой": ["🌆Город🌆"],
    "🏢Муравленко": ["🌆Город🌆"],
    "🏢Излучинск": ["🌆Город🌆"],
    "🏢Коротчаево": ["🌆Город🌆"],
    "🏢Стрежевой": ["🌆Город🌆"],
    "🏢Тарко-Сале": ["🌆Город🌆"],
    "🏢Мегион": ["🌆Город🌆"],
    "🏢Урай": ["🌆Город🌆"],
    "🏢Вынгапуровский": ["🌆Город🌆"],
    "🏢Пангоды": ["🌆Город🌆"],
    "🏢Надым": ["🌆Город🌆"],
    "🏢Нягань": ["🌆Город🌆"],
    "🏢Радужный": ["🌆Город🌆"],
    "🏢Старый Уренгой": ["🌆Город🌆"],
    "🏢Междуреченский": ["🌆Город🌆"],
    "🏢Пурпе": ["🌆Город🌆"],
    "🏢Пуровск": ["🌆Город🌆"],
    "🏢Покачи": ["🌆Город🌆"],
    "🏢Белоярский": ["🌆Город🌆"],
    "🏢Лангепас": ["🌆Город🌆"],
    "🏢Талинка": ["🌆Город🌆"]
}
PICKUP_POINTS = {
    "🏢Ноябрьск": {"🌆Город🌆": ["тайник"]},
    "🏢Нижневартовск": {"🌆Город🌆": ["тайник"]},
    "🏢Ханты-Мансийск": {"🌆Город🌆": ["тайник"]},
    "🏢Когалым": {"🌆Город🌆": ["тайник"]},
    "🏢Губкинский": {"🌆Город🌆": ["тайник"]},
    "🏢Лабытнанги": {"🌆Город🌆": ["тайник"]},
    "🏢Салехард": {"🌆Город🌆": ["тайник"]},
    "🏢Советский": {"🌆Город🌆": ["тайник"]},
    "🏢Югорск": {"🌆Город🌆": ["тайник"]},
    "🏢Новый Уренгой": {"🌆Город🌆": ["тайник"]},
    "🏢Муравленко": {"🌆Город🌆": ["тайник"]},
    "🏢Излучинск": {"🌆Город🌆": ["тайник"]},
    "🏢Коротчаево": {"🌆Город🌆": ["тайник"]},
    "🏢Стрежевой": {"🌆Город🌆": ["тайник"]},
    "🏢Тарко-Сале": {"🌆Город🌆": ["тайник"]},
    "🏢Мегион": {"🌆Город🌆": ["тайник"]},
    "🏢Урай": {"🌆Город🌆": ["тайник"]},
    "🏢Вынгапуровский": {"🌆Город🌆": ["тайник"]},
    "🏢Пангоды": {"🌆Город🌆": ["тайник"]},
    "🏢Надым": {"🌆Город🌆": ["тайник"]},
    "🏢Нягань": {"🌆Город🌆": ["тайник"]},
    "🏢Радужный": {"🌆Город🌆": ["тайник"]},
    "🏢Старый Уренгой": {"🌆Город🌆": ["тайник"]},
    "🏢Междуреченский": {"🌆Город🌆": ["тайник"]},
    "🏢Пурпе": {"🌆Город🌆": ["тайник"]},
    "🏢Пуровск": {"🌆Город🌆": ["тайник"]},
    "🏢Покачи": {"🌆Город🌆": ["тайник"]},
    "🏢Белоярский": {"🌆Город🌆": ["тайник"]},
    "🏢Лангепас": {"🌆Город🌆": ["тайник"]},
    "🏢Талинка": {"🌆Город🌆": ["тайник"]}
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
    waiting_for_price = State()
    waiting_for_city = State()
    waiting_for_district = State()
    waiting_for_pickup = State()
    # Новые состояния для редактирования
    edit_product = State()
    edit_name = State()
    edit_price = State()
    edit_city = State()
    edit_district = State()
    edit_pickup = State()

# Добавим новое состояние для создания бота
class CreateBotState(StatesGroup):
    waiting_for_token = State()

# Функция для создания клавиатуры с городами
def get_city_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)  # Города по два в строке
    buttons = [InlineKeyboardButton(city, callback_data=f"city_{city}") for city in CITIES]
    keyboard.add(*buttons)
    return keyboard

# Функция для создания клавиатуры с городами при добавлении товара
def get_add_city_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)  # Города по два в строке
    buttons = [InlineKeyboardButton(city, callback_data=f"addcity_{city}") for city in CITIES]
    keyboard.add(*buttons)
    return keyboard

# Обработчики команд
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()  # Завершаем текущее состояние, если оно есть
    db.add_user(message.from_user.id, message.from_user.username)
    
    # Создаем клавиатуру с городами
    keyboard = get_city_keyboard()
    
    # Добавляем дополнительные кнопки по одной в строке
    keyboard.add(InlineKeyboardButton("Баланс (0 руб.)", callback_data="balance"))
    keyboard.add(InlineKeyboardButton("Последний заказ", callback_data="orders"))
    keyboard.add(InlineKeyboardButton("😎Оператор продаж😎", callback_data="help"))
    keyboard.add(InlineKeyboardButton("💭Курилка💭", callback_data="help"))
    keyboard.add(InlineKeyboardButton("🧔🏻‍♂️Саппорт🧔🏻‍♂️", callback_data="help"))
    keyboard.add(InlineKeyboardButton("✏️Отзывы📝", callback_data="help"))
    keyboard.add(InlineKeyboardButton("💰Работа💰", callback_data="help"))
    keyboard.add(InlineKeyboardButton("📝Жалобы и редложения📝", callback_data="help"))
    
    # Добавляем кнопку "Поделиться ботом"
    keyboard.add(InlineKeyboardButton("🤖 Создать своего бота", callback_data="share_bot"))
    
    welcome_message = (
        "😎😎МАГАЗИН😎😎\n"
        "🥷АЛИБАБА И 40 КЛАДОВ 🥷\n"
        "Оператор авто-продаж🤖 Приветствует тебя.\n"
        "🛑АКЦИЯ  3+1🛑\n"
        "ТЕПЕРЬ НЕ ТОЛЬКО ЧЕРЕЗ ОПЕРАТОРА, НО И В БОТЕ\n"
        "Совершите 3 покупки через ОПЕРАТОРА или в БОТЕ за 12 часов и получите в ПОДАРОК 4 адрес "
        "(☝️Бонус выдается наименьшая позиция ваших покупок ☝️)"
    )
    
    await message.answer(welcome_message)
    await message.answer("🌆 Выберите ваш город:", reply_markup=keyboard)

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
    
    # Добавим отладочное сообщение
    logging.info(f"Пользователь выбрал город: {city}")
    
    products = db.get_all_products(city)
    
    # Добавим отладочное сообщение для проверки полученных товаров
    logging.info(f"Товары для города {city}: {products}")
    
    if not products:
        await callback.message.answer(
            f"😕 В каталоге нет товаров для города {city}",
            reply_markup=get_city_keyboard()
        )
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    for product in products:
        keyboard.add(InlineKeyboardButton(f"{product[1]} - {product[3]}₽", 
                                          callback_data=f"product_{product[0]}"))
    
    await callback.message.answer(
        "💊Какой продукт хотели бы приобрести?💎", 
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
    
    await callback.message.answer("🏙Выберите район🏙", reply_markup=keyboard)
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
    
    await callback.message.answer("Выберите тип", reply_markup=keyboard)
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
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Оплатить", callback_data="pay"),
        InlineKeyboardButton("Отменить", callback_data="cancel")
    )
    
    await callback.message.answer(
        f"Идентификатор вашей покупки: № {order_id}\n"
        f"Сумма к оплате: {data['price']}руб.\n"
        f"Местоположение: {data['city']}\n"
        f"Локация/Ближайшая станция: {data['district']}\n\n"
        "Пожалуйста, перейдите к оплате, нажав кнопку ОПЛАТИТЬ.\n"
        "Обратите внимание: после начала процесса оплаты у вас будет 30 минут для её завершения.",
        reply_markup=keyboard
    )
    await OrderStates.waiting_for_payment.set()

@dp.callback_query_handler(text="cancel", state="*")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    
    # Создаем клавиатуру как в команде /start
    keyboard = get_city_keyboard()
    
    # Добавляем дополнительные кнопки
    keyboard.add(InlineKeyboardButton("Баланс (0 руб.)", callback_data="balance"))
    keyboard.add(InlineKeyboardButton("Последний заказ", callback_data="orders"))
    keyboard.add(InlineKeyboardButton("😎Оператор продаж😎", callback_data="help"))
    keyboard.add(InlineKeyboardButton("💭Курилка💭", callback_data="help"))
    keyboard.add(InlineKeyboardButton("🧔🏻‍♂️Саппорт🧔🏻‍♂️", callback_data="help"))
    keyboard.add(InlineKeyboardButton("✏️Отзывы📝", callback_data="help"))
    keyboard.add(InlineKeyboardButton("💰Работа💰", callback_data="help"))
    keyboard.add(InlineKeyboardButton("📝Жалобы и редложения📝", callback_data="help"))
    
    # Добавляем кнопку создания бота
    keyboard.add(InlineKeyboardButton("🤖 Создать своего бота", callback_data="share_bot"))
    
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
    
    await callback.message.answer(f"💳 Выберите способ оплаты:", reply_markup=keyboard)
    await OrderStates.waiting_for_payment.set()

@dp.callback_query_handler(text_startswith="payment_", state=OrderStates.waiting_for_payment)
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    payment_method = callback.data.split('_')[1]
    data = await state.get_data()
    
    # Сохраняем заказ в базе данных
    db.add_order(data['order_id'], callback.from_user.id, data['product_id'])
    
    await callback.message.answer(
        f"✅ ВЫДАННЫЕ РЕКВИЗИТЫ ДЕЙСТВУЮТ 30 МИНУТ\n"
        f"✅ ВЫ ПОТеряете деньги, если оплатите позже\n"
        f"✅ Переводите точную сумму. Неверная сумма не будет зачислена.\n"
        f"✅ Оплата должна проходить одним платежом.\n"
        f"✅ Проблемы с оплатой? Перейдите по ссылке: [doctor](https://example.com)\n"
        f"Предоставьте чек об оплате и ID: {data['order_id']}\n"
        f"✅ С проблемной заявкой обращайтесь не позднее 24 часов с момента оплаты.\n\n",
        parse_mode='Markdown'
    )

    # Добавляем новое сообщение с деталями оплаты
    await callback.message.answer(
        f"Номер оплаты № {data['order_id']}. Заплатите {data['price']} рублей.\n"
        "Важно пополнить ровную сумму.\n"
        "на карту 2200154595790709\n"
        "‼️ у вас есть 30 мин на оплату, после чего платёж не будет принят\n"
        "‼️ ПЕРЕВЁЛ НЕТОЧНУЮ СУММУ - ОПЛАТИЛ ЧУЖОЙ ЗАКАЗ!"
    )

    # Добавляем сообщение о действиях при задержке выдачи средств
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Проблема с оплатой", callback_data="payment_issue"))
    await callback.message.answer(
        "Если в течении часа средства не выдались автоматически, то нажмите на кнопку - 'Проблема с оплатой'.",
        reply_markup=keyboard
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

@dp.message_handler(commands=['admin'], state='*')
async def admin_panel(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("❌ У вас нет доступа к панели администратора!")
        return
    
    await state.finish()  # Завершаем текущее состояние, если оно есть
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить товар", callback_data="add_product"),
        InlineKeyboardButton("✏️ Редактировать товар", callback_data="edit_product"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("🗑 Удалить товар", callback_data="delete_product"),
        InlineKeyboardButton("📢 Рассылка", callback_data="broadcast"),
        InlineKeyboardButton("📦 Все товары", callback_data="show_all_products")
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
        keyboard = get_add_city_keyboard()
        
        await AdminStates.waiting_for_city.set()
        await message.answer("🌆 Выберите город для товара:", reply_markup=keyboard)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену (только число)!")

# Обработчик для выбора города при добавлении товара
@dp.callback_query_handler(text_startswith="addcity_", state=AdminStates.waiting_for_city)
async def add_product_city(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.split('_')[1]
    await state.update_data(city=city)
    
    # Создаем клавиатуру с районами
    keyboard = InlineKeyboardMarkup(row_width=2)
    for district in DISTRICTS[city]:
        keyboard.add(InlineKeyboardButton(district, callback_data=f"adddistrict_{district}"))
    
    await callback.message.answer("🏙Выберите район🏙", reply_markup=keyboard)
    await AdminStates.waiting_for_district.set()

# Добавим новый обработчик для выбора района
@dp.callback_query_handler(text_startswith="adddistrict_", state=AdminStates.waiting_for_district)
async def add_product_district(callback: types.CallbackQuery, state: FSMContext):
    district = callback.data.split('_')[1]
    await state.update_data(district=district)
    
    data = await state.get_data()
    city = data['city']
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for pickup in PICKUP_POINTS[city][district]:
        keyboard.add(InlineKeyboardButton(pickup, callback_data=f"addpickup_{pickup}"))
    
    await callback.message.answer("Выберите тип", reply_markup=keyboard)
    await AdminStates.waiting_for_pickup.set()

# Добавим обработчик для пункта выдачи
@dp.callback_query_handler(text_startswith="addpickup_", state=AdminStates.waiting_for_pickup)
async def add_product_pickup(callback: types.CallbackQuery, state: FSMContext):
    pickup = callback.data.split('_')[1]
    await state.update_data(pickup=pickup)
    
    data = await state.get_data()
    # Добавляем описание товара, которое ранее отсутствовало
    description = "Описание не указано"  # Здесь можно добавить логику для получения описания, если оно есть
    db.add_product(data['name'], description, data['price'], data['city'], data['district'], data['pickup'])
    await callback.message.answer(
        f"✅ Товар успешно добавлен:\n"
        f"📦 Название: {data['name']}\n"
        f"💰 Цена: {data['price']}₽\n"
        f"🌆 Город: {data['city']}\n"
        f"🏘 Район: {data['district']}\n"
        f"📍 Пункт выдачи: {pickup}"
    )
    await state.finish()

# Добавим обработчик для кнопки "Изменить город"
@dp.callback_query_handler(text="change_city")
async def change_city(callback: types.CallbackQuery):
    keyboard = get_city_keyboard()
    
    # Добавляем дополнительные кнопки по одной в строке
    keyboard.add(InlineKeyboardButton("Баланс (0 руб.)", callback_data="balance"))
    keyboard.add(InlineKeyboardButton("Последний заказ", callback_data="orders"))
    keyboard.add(InlineKeyboardButton("😎Оператор продаж😎", callback_data="help"))
    keyboard.add(InlineKeyboardButton("💭Курилка💭", callback_data="help"))
    keyboard.add(InlineKeyboardButton("🧔🏻‍♂️Саппорт🧔🏻‍♂️", callback_data="help"))
    keyboard.add(InlineKeyboardButton("✏️Отзывы📝", callback_data="help"))
    keyboard.add(InlineKeyboardButton("💰Работа💰", callback_data="help"))
    keyboard.add(InlineKeyboardButton("📝Жалобы и редложения📝", callback_data="help"))
    
    # Добавляем кнопку "Поделиться ботом"
    keyboard.add(InlineKeyboardButton("🤖 Создать своего бота", callback_data="share_bot"))
    
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
    dp.register_message_handler(cmd_start, commands=['start'], state='*')
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
    dp.register_message_handler(admin_panel, commands=['admin'], state='*')
    dp.register_callback_query_handler(add_product_start, text="add_product")
    dp.register_callback_query_handler(show_stats, text="admin_stats")
    dp.register_callback_query_handler(show_products_for_deletion, text="delete_product")
    dp.register_callback_query_handler(delete_product, text_startswith="del_product_")
    dp.register_callback_query_handler(broadcast_start, text="broadcast")
    dp.register_callback_query_handler(share_bot, text="share_bot")
    
    # Регистрируем обработчики состояний
    dp.register_message_handler(add_product_name, state=AdminStates.waiting_for_name)
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

# Обработчик для отображения всех товаров
@dp.callback_query_handler(text="show_all_products")
async def show_all_products(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        return
    
    products = db.get_all_products()
    if not products:
        await callback.message.answer("❌ В каталоге нет товаров")
        return
    
    text = "📦 Все товары:\n\n"
    for product in products:
        text += (f"🆔 ID: {product[0]}\n"
                 f"📦 Название: {product[1]}\n"
                 f"💰 Цена: {product[3]}₽\n"
                 f"🌆 Город: {product[4]}\n"
                 f"🏘 Район: {product[5]}\n"
                 f"📍 Пункт выдачи: {product[6]}\n\n")
    
    await callback.message.answer(text)

# Изменим функцию main
async def main():
    # Настраиваем логирование
    logging.basicConfig(level=logging.INFO)
    
    # Создаем папку для ботов, если её нет
    os.makedirs('bots', exist_ok=True)
    
    # Запускаем основного бота
    await dp.start_polling()

@dp.callback_query_handler(text="edit_product")
async def start_edit_product(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.message.answer("❌ У вас нет доступа к этой функции!")
        return
    
    products = db.get_all_products()
    if not products:
        await callback.message.answer("❌ В каталоге нет товаров")
        return
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for product in products:
        keyboard.add(InlineKeyboardButton(
            f"{product[1]} ({product[4]})", 
            callback_data=f"select_product_{product[0]}"
        ))
    
    await callback.message.answer("📝 Выберите товар для редактирования:", reply_markup=keyboard)

@dp.callback_query_handler(text_startswith="select_product_")
async def select_product(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[2])
    product = db.get_product(product_id)
    await state.update_data(product_id=product_id)
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Изменить название", callback_data="edit_name"),
        InlineKeyboardButton("Изменить цену", callback_data="edit_price"),
        InlineKeyboardButton("Изменить город", callback_data="edit_city"),
        InlineKeyboardButton("Изменить район", callback_data="edit_district"),
        InlineKeyboardButton("Изменить пункт выдачи", callback_data="edit_pickup"),
        InlineKeyboardButton("Отмена", callback_data="cancel_edit")
    )
    
    await callback.message.answer(
        f"📝 Редактирование товара: {product[1]}\n"
        f"💬 Цена: {product[3]}₽\n"
        f"🌆 Город: {product[4]}\n"
        f"🏘 Район: {product[5]}\n"
        f"📍 Пункт выдачи: {product[6]}",
        reply_markup=keyboard
    )

if __name__ == '__main__':
    asyncio.run(main())
