import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- КОНФИГУРАЦИЯ ---
TOKEN = "мой токен"
ADMIN_ID = 6807542444  # Твой ID для получения заявок

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
    kb.button(text="🦾 Имплантация / Хирургия", callback_data="pr:implants")
    kb.button(text="💎 Виниры / Коронки", callback_data="pr:ortho")
    kb.button(text="📐 Брекеты / Ортодонтия", callback_data="pr:braces")
    kb.button(text="🧼 Гигиена / Vector", callback_data="pr:hygiene")
    kb.button(text="⬅️ Назад", callback_data="to_main")
    kb.adjust(2)
    return kb.as_markup()

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "<b>ELEMENTS DENTAL CENTER</b> ⚪\n\n"
        "Цифровая стоматология экспертного уровня. Мы объединили опыт "
        "ведущих хирургов и технологии Carl Zeiss для вашего здоровья.\n\n"
        "Выберите раздел:",
        reply_markup=main_kb(), parse_mode="HTML"
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
    res = "Данные обновляются..."
    
    if cat == "implants":
        res = ("<b>🦾 ИМПЛАНТОЛОГИЯ</b>\n\n"
               "• <b>All-on-4 / All-on-6:</b> Технология 'Все на 4' или 'Все на 6' имплантатах. Позволяет восстановить весь зубной ряд даже при полной потере зубов.\n"
               "• <b>Одномоментная имплантация:</b> Установка имплантата сразу в лунку удаленного зуба.\n"
               "• Абатмент JDental — 10 000 ₽\n• Абатмент Osstem — 7 000 ₽")
    elif cat == "hygiene":
        res = ("<b>🧼 ГИГИЕНА И ПАРОДОНТОЛОГИЯ</b>\n\n"
               "• <b>Аппарат VECTOR:</b> Лечение десен без боли. Удаляет биопленку и зубной камень ультразвуком.\n"
               "• Профессиональная гигиена — от 5 500 ₽\n"
               "• Отбеливание Beyond Polus — от 25 000 ₽")
    elif cat == "braces":
        res = ("<b>📐 ОРТОДОНТИЯ</b>\n\n"
               "• Брекеты Incognito (невидимые) — от 150 000 ₽\n"
               "• Сапфировые брекеты — от 60 000 ₽\n"
               "• Керамические брекеты — от 55 000 ₽")
    
    kb = InlineKeyboardBuilder().button(text="⬅️ К услугам", callback_data="menu_price")
    await callback.message.edit_text(res, reply_markup=kb.as_markup(), parse_mode="HTML")

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

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
