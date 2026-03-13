import asyncio
import csv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest  # <--- ЭТО ОБЯЗАТЕЛЬНО ДОБАВИТЬ
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


# --- КОНФИГУРАЦИЯ ---
import os
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6807542444  # Твой ID для получения заявок

bot = Bot(token=TOKEN)
dp = Dispatcher()

def save_to_csv(user_id, name, phone):
    file_path = 'users.csv'
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['User ID', 'Имя', 'Телефон'])
        writer.writerow([user_id, name, phone])


# --- СОСТОЯНИЯ КВИЗА (9 ШАГОВ) ---
class Quiz(StatesGroup):
    goal = State()
    symptoms = State()
    gnathology = State()
    aesthetic = State()
    diagnostics = State()
    history = State()
    priority = State()
    budget = State()
    contact = State()

# --- ИНФОРМАЦИОННЫЕ БЛОКИ ---

TEAM_INFO = (
    "<b>👨‍⚕️ КОМАНДА ELEMENTS DENTAL CENTER</b>\n\n"
    "• <b>Новодран Вадим Николаевич</b>\n<i>Главный врач, челюстно-лицевой хирург, имплантолог.</i>\n\n"
    "• <b>Жданов Виктор Егорович</b>\n<i>Хирург-имплантолог.</i>\n\n"
    "• <b>Руденок Татьяна Леонидовна</b>\n<i>Гнатолог, ортопед-стоматолог, терапевт.</i>\n\n"
    "• <b>Кононенко Андрей Алексеевич</b>\n<i>Терапевт, ортопед-стоматолог.</i>\n\n"
    "• <b>Лебеденко Евгений Владимирович</b>\n<i>Терапевт, ортопед-стоматолог.</i>\n\n"
    "• <b>Кучеев Никита Витальевич</b>\n<i>Врач-ортодонт.</i>\n\n"
    "• <b>Степаненко Елена Сергеевна</b> — <i>Старшая медсестра.</i>\n"
    "• <b>Смирнов Дмитрий Алексеевич</b> — <i>Зубной техник.</i>"
)

TECH_DETAILED = (
    "<b>🔬 ТЕХНОЛОГИИ ПРЕМИУМ-КЛАССА</b>\n\n"
    "✅ <b>Микроскоп Carl Zeiss:</b> Лечение каналов, извлечение инструментов и диагностика трещин с 40-кратным увеличением.\n\n"
    "✅ <b>Аппарат VECTOR:</b> Безоперационное лечение десен. Ультразвук удаляет налет и бактерии без боли и отеков.\n\n"
    "✅ <b>Orthophos S Sirona:</b> КЛКТ последнего поколения для сверхточной 3D-диагностики.\n\n"
    "✅ <b>Beyond Polus:</b> Самое бережное отбеливание холодным светом (результат до 12 тонов)."
)

# --- КЛАВИАТУРЫ ---

def main_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Подобрать план лечения (Квиз)", callback_data="quiz_start")
    kb.button(text="💰 Услуги и прайс", callback_data="menu_price")
    kb.button(text="👨‍⚕️ Наши специалисты", callback_data="menu_team")
    kb.button(text="🏥 Технологии и оборудование", callback_data="menu_tech")
    kb.button(text="📍 Контакты", callback_data="menu_contacts")
    kb.adjust(1)
    return kb.as_markup()

def price_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📐 Ортодонтия", callback_data="pr:ortho_dent")
    kb.button(text="💎 Ортопедия / Протез", callback_data="pr:ortho_ped")
    kb.button(text="🦷 Терапия / Лечение", callback_data="pr:therapy")
    kb.button(text="🦾 Хирургия / Импланты", callback_data="pr:surgery")
    kb.button(text="🧼 Чистка / Рентген", callback_data="pr:hygiene_rentgen")
    kb.button(text="⬅️ Назад", callback_data="to_main")
    kb.adjust(1) # Все кнопки в один ряд для удобства клика
    return kb.as_markup()



# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    # Создаем кнопку запроса контакта
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Пройти верификацию", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "<b>Добро пожаловать в Elements Dental Center! ✨</b>\n\n"
        "Для доступа к прайс-листу и записи, пожалуйста, подтвердите ваш номер телефона, нажав кнопку ниже.",
        reply_markup=kb,
        parse_mode="HTML"
    )

@dp.message(F.contact)
async def get_contact(message: types.Message):
    contact = message.contact
    
    # 1. Сохраняем в таблицу
    save_to_csv(contact.user_id, contact.first_name, contact.phone_number)
    
    # 2. Уведомляем тебя (админа)
    await bot.send_message(
        6807542444, 
        f"👤 <b>Новый клиент в базе!</b>\nИмя: {contact.first_name}\nТел: {contact.phone_number}\nID: <code>{contact.user_id}</code>",
        parse_mode="HTML"
    )
    
    # 3. Убираем кнопку верификации и показываем меню
    await message.answer(
        "Верификация пройдена! ✅ Теперь вам доступны все разделы.",
        reply_markup=ReplyKeyboardRemove() 
    )
    await message.answer(
        "<b>Выберите раздел:</b>",
        reply_markup=main_kb(), # Твоя функция главного меню
        parse_mode="HTML"
    )




@dp.callback_query(F.data == "to_main")
async def back_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Выберите раздел:", reply_markup=main_kb())

@dp.callback_query(F.data == "menu_team")
async def show_team(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="to_main")
    await callback.message.edit_text(TEAM_INFO, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_tech")
async def show_tech(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="to_main")
    await callback.message.edit_text(TECH_DETAILED, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_price")
async def show_price(callback: types.CallbackQuery):
    await callback.message.edit_text("<b>💰 КАТЕГОРИИ УСЛУГ</b>", reply_markup=price_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_contacts")
async def show_contacts(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Написать администратору", url="https://t.me/elements_dental") 
    kb.button(text="⬅️ Назад", callback_data="to_main")
    kb.adjust(1)
    
    text = (
        "<b>📍 КОНТАКТЫ ELEMENTS</b>\n\n"
        "г. Донецк, пр-т Ильича, 17в\n"
        "🕒 <b>Режим работы:</b> Пн-Сб 9:00 - 19:00\n"
        "📞 <b>Телефон:</b> +7 (949) 307-15-85\n\n"
        "Вы можете записаться через квиз или написать нам напрямую."
    )
    
    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except TelegramBadRequest:
        pass
    await callback.answer()


@dp.callback_query(F.data.startswith("pr:"))
async def price_detail(callback: types.CallbackQuery):
    cat = callback.data.split(":")[1]
    res = ""
    
    if cat == "ortho_dent":
        res = (
            "<b>📐 ОРТОДОНТИЯ</b>\n\n"
            "<b>Установка брекет-систем:</b>\n"
            "• Металлические — 35 000 ₽\n"
            "• Керамические — 37 000 ₽\n"
            "• Сапфировые — 40 000 ₽\n"
            "• Самолигирующие — 60 000 ₽\n\n"
            "<b>Диагностика:</b>\n"
            "• Консультация гнатолога — 3 000 ₽\n"
            "• Полная диагностика (план, 3D модель) — 8 000 ₽\n\n"
            "<b>Обслуживание:</b>\n"
            "• Коррекция (1 челюсть) — 4 000 ₽\n"
            "• Коррекция (2 челюсти) — 5 500 ₽\n"
            "• Подклейка брекета — 1 000 ₽\n"
            "• Мини-винт — 15 000 ₽\n\n"
            "<b>Завершение лечения:</b>\n"
            "• Пластинка — 10 500 ₽\n"
            "• Каппа ретенционная — 6 500 ₽\n"
            "• Ретейнер (1 ед. / 6 ед.) — 3 000 / 5 000 ₽\n"
            "• Снятие системы — 4 500 ₽"
        )
    elif cat == "ortho_ped":
        res = (
            "<b>💎 ОРТОПЕДИЯ И ПРОТЕЗИРОВАНИЕ</b>\n\n"
            "<b>Виниры и коронки:</b>\n"
            "• Винир керамический — 33 000 ₽\n"
            "• Коронка E-MAX / Циркон — 33 000 - 35 000 ₽\n"
            "• Металлокерамика — 20 000 ₽\n"
            "• Коронка на импланте — от 22 000 ₽\n"
            "• Вкладка E-MAX — 10 000 - 15 000 ₽\n\n"
            "<b>Абатменты:</b>\n"
            "• OSSTEM / БИО — 7 000 ₽\n"
            "• JDental / Индивидуальный — 10 000 ₽\n"
            "• Мультиюнит (JDental) — 12 000 - 15 000 ₽\n\n"
            "<b>Протезы:</b>\n"
            "• Акриловый — 30 000 ₽\n"
            "• Нейлоновый — 45 000 ₽\n\n"
            "<b>Дополнительно:</b>\n"
            "• Сканирование 3D — 5 000 ₽\n"
            "• Временная коронка — 2 000 - 3 000 ₽"
        )
    elif cat == "therapy":
        res = (
            "<b>🦷 ТЕРАПИЯ И ЛЕЧЕНИЕ</b>\n\n"
            "<b>Кариес:</b>\n"
            "• Поверхностный — 5 000 ₽\n"
            "• Средний — 6 000 ₽\n"
            "• Глубокий — 7 000 ₽\n"
            "• Реставрация (до 1/3) — 5 000 ₽\n"
            "• Реставрация (более 1/3) — 8 000 ₽\n\n"
            "<b>Эндодонтия (Микроскоп):</b>\n"
            "• Работа под микроскопом — 4 000 ₽\n"
            "• Пломбирование канала — 3 000 ₽\n"
            "• Распломбировка — 3 000 ₽\n"
            "• Удаление инструмента — от 2 000 ₽\n\n"
            "<b>Подготовка:</b>\n"
            "• Анестезия — 1 000 ₽\n"
            "• Консультация с планом — 3 000 ₽"
        )
    elif cat == "surgery":
        res = (
            "<b>🦾 ХИРУРГИЯ И ИМПЛАНТАЦИЯ</b>\n\n"
            "<b>Имплантация:</b>\n"
            "• Имплант OSSTEM — 35 000 ₽\n"
            "• Имплант JDental — 50 000 ₽\n"
            "• Шаблон хирургический — от 4 000 ₽\n"
            "• Синус-лифт — 50 000 ₽\n\n"
            "<b>Удаление зубов:</b>\n"
            "• Однокорневой — 4 000 ₽\n"
            "• Многокорневой — 4 500 ₽\n"
            "• Ретинированный (мудрости) — 8 000 ₽\n\n"
            "<b>Костная пластика:</b>\n"
            "• Пластика (общая) — 45 000 ₽\n"
            "• Материал Bio-Oss — 15 000 - 20 000 ₽"
        )
    elif cat == "hygiene_rentgen":
        res = (
            "<b>🧼 ГИГИЕНА И РЕНТГЕН</b>\n\n"
            "<b>Пародонтология:</b>\n"
            "• Аппарат Vector (2 челюсти) — 16 000 ₽\n"
            "• Чистка простая — 4 000 ₽\n"
            "• Чистка сложная — 6 000 ₽\n"
            "• Отбеливание Beyond Polus (2 чел.) — 16 000 ₽\n\n"
            "<b>Рентгенография:</b>\n"
            "• 3D снимок (КТ) — 4 000 ₽\n"
            "• Панорамный снимок — 2 000 ₽\n"
            "• Прицельный снимок — 500 ₽"
        )

        # Это заменяет твои текущие строки 225-227
    res += (
        "\n\n🌐 <b>С полным прайс-листом и услугами можно ознакомиться на нашем сайте.</b>"
        "\n\n<i>*Окончательная цена зависит от клинического случая.</i>"
    )
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Перейти на сайт", url="https://elements-dent.ru/")
    kb.button(text="⬅️ К категориям", callback_data="menu_price")
    kb.adjust(1)

    try:
        await callback.message.edit_text(res, reply_markup=kb.as_markup(), parse_mode="HTML")
    except TelegramBadRequest:
        pass
    await callback.answer()


# --- КВИЗ (9 ШАГОВ) ---

@dp.callback_query(F.data == "quiz_start")
async def quiz_1(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Quiz.goal)
    kb = InlineKeyboardBuilder()
    kb.button(text="🦷 Лечение боли", callback_data="g:Лечение")
    kb.button(text="✨ Виниры/Эстетика", callback_data="g:Эстетика")
    kb.button(text="🦾 Имплантация", callback_data="g:Имплантация")
    kb.button(text="📐 Прикус", callback_data="g:Прикус")
    kb.adjust(1)
    await callback.message.edit_text("<b>Шаг 1/9:</b> Какая задача сейчас самая важная?", reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(Quiz.goal)
async def quiz_2(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(goal=callback.data.split(":")[1])
    await state.set_state(Quiz.symptoms)
    kb = InlineKeyboardBuilder().button(text="Да", callback_data="s:Да").button(text="Нет", callback_data="s:Нет")
    await callback.message.edit_text("<b>Шаг 2/9:</b> Беспокоят ли вас боли в зубах или деснах?", reply_markup=kb.as_markup())

@dp.callback_query(Quiz.symptoms)
async def quiz_3(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(pain=callback.data.split(":")[1])
    await state.set_state(Quiz.gnathology)
    kb = InlineKeyboardBuilder()
    kb.button(text="Щелчки в челюсти", callback_data="gn:Щелчки")
    kb.button(text="Головные боли", callback_data="gn:Боли")
    kb.button(text="Все в норме", callback_data="gn:Норма")
    kb.adjust(1)
    await callback.message.edit_text("<b>Шаг 3/9:</b> Замечали ли вы щелчки при открывании рта или скрежет зубами?", reply_markup=kb.as_markup())

@dp.callback_query(Quiz.gnathology)
async def quiz_4(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(gnath=callback.data.split(":")[1])
    await state.set_state(Quiz.aesthetic)
    kb = InlineKeyboardBuilder().button(text="Цвет", callback_data="a:Цвет").button(text="Форма зубов", callback_data="a:Форма").button(text="Отсутствие зуба", callback_data="a:Пробел")
    await callback.message.edit_text("<b>Шаг 4/9:</b> Что бы вы хотели изменить визуально?", reply_markup=kb.as_markup())

@dp.callback_query(Quiz.aesthetic)
async def quiz_5(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(look=callback.data.split(":")[1])
    await state.set_state(Quiz.diagnostics)
    kb = InlineKeyboardBuilder().button(text="Есть КТ/Снимок", callback_data="d:Да").button(text="Нужна диагностика", callback_data="d:Нет")
    await callback.message.edit_text("<b>Шаг 5/9:</b> Делали ли вы КЛКТ (3D снимок) в последние полгода?", reply_markup=kb.as_markup())

@dp.callback_query(Quiz.diagnostics)
async def quiz_6(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(diag=callback.data.split(":")[1])
    await state.set_state(Quiz.history)
    kb = InlineKeyboardBuilder().button(text="До 6 месяцев", callback_data="h:Полгода").button(text="Давно", callback_data="h:Давно")
    await callback.message.edit_text("<b>Шаг 6/9:</b> Как давно вы были на профессиональной гигиене?", reply_markup=kb.as_markup())

@dp.callback_query(Quiz.history)
async def quiz_7(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(hist=callback.data.split(":")[1])
    await state.set_state(Quiz.priority)
    kb = InlineKeyboardBuilder().button(text="Максимальная эстетика", callback_data="p:Эстетика").button(text="Функциональность", callback_data="p:Функция")
    await callback.message.edit_text("<b>Шаг 7/9:</b> Что для вас важнее в результате лечения?", reply_markup=kb.as_markup())

@dp.callback_query(Quiz.priority)
async def quiz_8(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(prio=callback.data.split(":")[1])
    await state.set_state(Quiz.budget)
    kb = InlineKeyboardBuilder().button(text="Премиум (E-max)", callback_data="b:Премиум").button(text="Стандарт", callback_data="b:Стандарт")
    await callback.message.edit_text("<b>Шаг 8/9:</b> Какие материалы рассматриваете?", reply_markup=kb.as_markup())

@dp.callback_query(Quiz.budget)
async def quiz_9(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(bud=callback.data.split(":")[1])
    await state.set_state(Quiz.contact)
    await callback.message.edit_text("<b>Шаг 9/9:</b> Введите ваш номер телефона, и мы свяжемся для записи:")

@dp.message(Quiz.contact)
async def quiz_final(message: types.Message, state: FSMContext):
    phone = message.text
    data = await state.get_data()
    
    report = (
        f"<b>🚨 НОВАЯ ЗАЯВКА - ELEMENTS</b>\n"
        f"👤 Пациент: {message.from_user.full_name}\n"
        f"📞 Тел: {phone}\n"
        f"📋 Цель: {data['goal']}\n"
        f"🦷 Боль: {data['pain']}\n"
        f"🧠 Гнато: {data['gnath']}\n"
        f"🔍 Снимок: {data['diag']}"
    )
    
    try:
        await bot.send_message(ADMIN_ID, report, parse_mode="HTML")
    except:
        pass

    await state.clear()
    await message.answer("✅ Данные получены! Куратор клиники свяжется с вами.", reply_markup=main_kb())

# КЛИЕНТ -> АДМИН (Пересылка сообщений тебе)
@dp.message(F.chat.type == "private", ~F.from_user.id == 6807542444)
async def forward_to_admin(message: types.Message):
    await message.answer("Ваше сообщение отправлено администратору. Ожидайте ответа! ✨")
    
    # Пересылаем сообщение админу с данными клиента
    await bot.send_message(
        6807542444,
        f"📩 <b>Сообщение от клиента!</b>\n"
        f"Имя: {message.from_user.full_name}\n"
        f"ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )
    await message.forward(chat_id=6807542444)

# АДМИН -> КЛИЕНТ (Ответ на сообщение через Reply)
@dp.message(F.from_user.id == 6807542444, F.reply_to_message)
async def reply_to_user(message: types.Message):
    # Пытаемся достать ID из пересланного сообщения
    if message.reply_to_message.forward_from:
        user_id = message.reply_to_message.forward_from.id
        try:
            await bot.send_message(user_id, f"<b>Ответ администратора:</b>\n\n{message.text}", parse_mode="HTML")
            await message.answer("✅ Ответ отправлен.")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    else:
        await message.answer("❌ Не могу определить ID. Отвечайте только на пересланные ботом сообщения!")


# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
