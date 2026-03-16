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

def is_user_registered(user_id):
    file_path = 'users.csv'
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Проверяем каждую строку, есть ли там ID (он в первом столбце)
            for row in reader:
                if row and str(row[0]) == str(user_id):
                    return True
    except:
        return False
    return False



class EasyQuiz(StatesGroup):
    goal = State()      # Чего хочет клиент
    last_visit = State() # Как давно был у врача
    comfort = State()    # Насколько боится
    contact = State()    # Номер телефона


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
    kb.button(text="📍 Контакты", callback_data="menu_contacts") # Проверь эту строку!
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



@dp.callback_query(F.data.startswith("menu_contacts")) # Изменили на startswith для надежности
async def show_contacts(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer() # Убирает состояние нажатия (часики)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Записаться через квиз", callback_data="quiz_start")
    kb.button(text="💬 Написать администратору", url="https://t.me/elements_dental") 
    kb.button(text="📞 Позвонить сейчас", url="tel:+79493071585")
    kb.button(text="⬅️ Назад", callback_data="to_main")
    kb.adjust(1)
    
    text = (
        "<b>📍 КОНТАКТЫ ELEMENTS</b>\n\n"
        "г. Донецк, пр-т Ильича, 17в\n"
        "🕒 <b>Режим работы:</b> Пн-Сб 9:00 - 19:00\n\n"
        "📞 <b>Телефон:</b> <a href='tel:+79493071585'>+7 (949) 307-15-85</a>\n\n"
        "<b>Как записаться к нам на приём?</b>\n"
        "• <b>Быстро:</b> Нажмите кнопку «Записаться через квиз» ниже.\n"
        "• <b>Лично:</b> Позвоните нам или напишите администратору."
    )
    
    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception as e:
        # Если не получается отредактировать, просто шлем новым сообщением
        await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")






# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear() # Сбрасываем квиз, если человек решил начать заново
    
    if is_user_registered(message.from_user.id):
        # Если клиент уже знаком, просто даем меню
        await message.answer(
            f"<b>С возвращением, {message.from_user.first_name}! ✨</b>\nЧем можем помочь сегодня?",
            reply_markup=main_kb(),
            parse_mode="HTML"
        )
    else:
        # Если новый — просим номер
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Пройти верификацию", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "<b>Добро пожаловать в Elements! ✨</b>\n\n"
            "Для доступа к прайсу и записи, пожалуйста, подтвердите ваш номер телефона.",
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


# --- УПРОЩЕННЫЙ КВИЗ ---

@dp.callback_query(F.data == "quiz_start")
async def easy_quiz_1(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(EasyQuiz.goal)
    kb = InlineKeyboardBuilder()
    kb.button(text="🦷 Вылечить зубы", callback_data="eq:Лечение")
    kb.button(text="✨ Сделать улыбку красивее", callback_data="eq:Эстетика")
    kb.button(text="🦷 Восстановить зубы", callback_data="eq:Восстановление")
    kb.adjust(1)
    kb.row(types.InlineKeyboardButton(text="🏠 В главное меню", callback_data="to_main"))
    
    await callback.message.edit_text(
        "<b>Шаг 1/4:</b> Какая задача для вас сейчас наиболее важна?",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(EasyQuiz.goal)
async def easy_quiz_2(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(goal=callback.data.split(":")[1])
    await state.set_state(EasyQuiz.last_visit)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="Менее 6 месяцев назад", callback_data="ev:Недавно")
    kb.button(text="Более года назад", callback_data="ev:Давно")
    kb.button(text="Очень давно", callback_data="ev:Затрудняюсь")
    kb.adjust(1)
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="quiz_start"))
    
    await callback.message.edit_text(
        "<b>Шаг 2/4:</b> Как давно вы были на профилактическом осмотре?",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(EasyQuiz.last_visit)
async def easy_quiz_3(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(last_visit=callback.data.split(":")[1])
    await state.set_state(EasyQuiz.comfort)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="Спокойно, доверяю врачам", callback_data="ec:Спокойно")
    kb.button(text="Немного волнуюсь", callback_data="ec:Волнуюсь")
    kb.button(text="Очень боюсь", callback_data="ec:Боюсь")
    kb.adjust(1)
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="quiz_start")) # Можно усложнить и вернуть на шаг 2, но для легкости ведем в начало
    
    await callback.message.edit_text(
        "<b>Шаг 3/4:</b> Как вы относитесь к посещению стоматолога?\n<i>(Мы подберем максимально комфортный подход)</i>",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(EasyQuiz.comfort)
async def easy_quiz_4(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(comfort=callback.data.split(":")[1])
    await state.set_state(EasyQuiz.contact)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 В меню", callback_data="to_main")
    
    await callback.message.edit_text(
        "<b>Шаг 4/4:</b> Почти готово! Оставьте ваш номер телефона, и наш куратор подберет удобное время для консультации.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@dp.message(EasyQuiz.contact)
async def easy_quiz_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    phone = message.text
    
    # Формируем отчет для админа
    report = (
        f"<b>💎 НОВАЯ КОНСУЛЬТАЦИЯ</b>\n"
        f"👤 Клиент: {message.from_user.full_name}\n"
        f"📞 Тел: {phone}\n"
        f"🎯 Цель: {data.get('goal')}\n"
        f"📅 Последний визит: {data.get('last_visit')}\n"
        f"🧘 Состояние: {data.get('comfort')}\n"
        f"ID: <code>{message.from_user.id}</code>"
    )
    
    await bot.send_message(ADMIN_ID, report, parse_mode="HTML")
    await state.clear()
    
    await message.answer(
        "✅ <b>Спасибо за доверие!</b>\n\nМы получили ваши данные. Куратор клиники Elements свяжется с вами в ближайшее время, чтобы ответить на вопросы.",
        reply_markup=main_kb(),
        parse_mode="HTML"
    )


# --- ЕДИНЫЙ ОБРАБОТЧИК (КЛИЕНТ <-> АДМИН) ---

@dp.message()
async def handle_messages(message: types.Message, state: FSMContext):
    # 1. ОТВЕТ АДМИНА КЛИЕНТУ
    if message.from_user.id == ADMIN_ID and message.reply_to_message:
        target_id = None
        
        # Пытаемся получить ID клиента из пересланного сообщения или текста
        if message.reply_to_message.forward_from:
            target_id = message.reply_to_message.forward_from.id
        elif message.reply_to_message.caption and "ID:" in message.reply_to_message.caption:
            target_id = int(message.reply_to_message.caption.split("ID:")[1].strip().split()[0])
        elif message.reply_to_message.text and "ID:" in message.reply_to_message.text:
            target_id = int(message.reply_to_message.text.split("ID:")[1].strip().split()[0])

        if target_id:
            try:
                await bot.copy_message(chat_id=target_id, from_chat_id=message.chat.id, message_id=message.message_id)
                await message.answer("✅ Отправлено клиенту!")
            except Exception as e:
                await message.answer(f"❌ Ошибка отправки: {e}")
        else:
            await message.answer("⚠️ Не могу найти ID клиента. Отвечайте на сообщение, где есть пометка 'ID:'")
        return 

    # 2. ПЕРЕСЫЛКА КЛИЕНТА АДМИНУ
    current_state = await state.get_state()
    if current_state is None and message.from_user.id != ADMIN_ID:
        # Уведомление админу
        user_info = f"📩 <b>Новое сообщение</b>\nОт: {message.from_user.full_name}\nID: <code>{message.from_user.id}</code>"
        await bot.send_message(ADMIN_ID, user_info, parse_mode="HTML")
        
        # Пересылка контента (текст, фото, видео)
        await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
        
        # Если это текст, добавляем кнопку возврата
        if message.text and not message.text.startswith('/'):
            kb = InlineKeyboardBuilder()
            kb.button(text="🏠 В главное меню", callback_data="to_main")
            await message.answer("Сообщение доставлено администратору Elements!", reply_markup=kb.as_markup())





# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
