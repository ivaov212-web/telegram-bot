import asyncio
import csv
import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
)

# ═══════════════════════════════════════════════
#              КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ Переменная BOT_TOKEN не задана! Установите её в Railway Variables.")

ADMIN_ID = int(os.getenv("ADMIN_ID", "6807542444"))
CSV_PATH = "users.csv"

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# ═══════════════════════════════════════════════
#              БАЗА ДАННЫХ (CSV)
# ═══════════════════════════════════════════════

def save_to_csv(user_id: int, name: str, phone: str) -> None:
    """Сохраняет нового пользователя в CSV-файл."""
    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["User ID", "Имя", "Телефон", "Дата регистрации"])
        writer.writerow([user_id, name, phone, datetime.now().strftime("%d.%m.%Y %H:%M")])
    logger.info(f"Пользователь сохранён: id={user_id}, name={name}, phone={phone}")


def is_user_registered(user_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь (есть ли его ID в CSV)."""
    if not os.path.isfile(CSV_PATH):
        return False
    try:
        with open(CSV_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Пропускаем заголовок
            for row in reader:
                if row and str(row[0]) == str(user_id):
                    return True
    except Exception as e:
        logger.error(f"Ошибка чтения CSV: {e}")
    return False


# ═══════════════════════════════════════════════
#              СОСТОЯНИЯ FSM (КВИЗ)
# ═══════════════════════════════════════════════

class Quiz(StatesGroup):
    goal = State()          # Шаг 1: Цель визита
    urgency = State()       # Шаг 2: Срочность
    last_visit = State()    # Шаг 3: Последний визит к врачу
    comfort = State()       # Шаг 4: Отношение к стоматологу
    phone = State()         # Шаг 5: Номер телефона


# ═══════════════════════════════════════════════
#              ТЕКСТЫ (КОНТЕНТ)
# ═══════════════════════════════════════════════

WELCOME_NEW = (
    "🦷 <b>Добро пожаловать в Elements Dental Center!</b>\n\n"
    "Мы — стоматологическая клиника премиум-класса в Донецке.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⭐️ <b>Почему нас выбирают тысячи пациентов:</b>\n"
    "• Безболезненное лечение под анестезией\n"
    "• Немецкое и швейцарское оборудование\n"
    "• Гарантия на все работы до 5 лет\n"
    "• Принимаем по записи — без очередей\n"
    "• Работаем с детьми от 3 лет\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "📱 <b>Для доступа к меню клиники — подтвердите ваш номер телефона.</b>\n"
    "<i>Это займёт 5 секунд и ваши данные в безопасности.</i>"
)

WELCOME_BACK = (
    "✨ <b>С возвращением, {name}!</b>\n\n"
    "Рады снова видеть вас в нашем боте.\n"
    "Выберите нужный раздел 👇"
)

MAIN_MENU_TEXT = (
    "🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n"
    "<i>Elements Dental Center — ваша улыбка, наша забота</i>\n\n"
    "Выберите интересующий раздел:"
)

CONTACTS_TEXT = (
    "📍 <b>КОНТАКТЫ ELEMENTS DENTAL CENTER</b>\n\n"
    "🏢 <b>Адрес:</b>\n"
    "г. Донецк, пр-т Ильича, 17в\n\n"
    "🕒 <b>Режим работы:</b>\n"
    "Понедельник — Суббота: 9:00 – 17:00\n"
    "Воскресенье: выходной\n\n"
    "📞 <b>Телефон:</b>\n"
    "<a href='tel:+79493071585'>+7 (949) 307-15-85</a>\n\n"
    "💬 <b>Мессенджеры:</b>\n"
    "Telegram: @elements_dental\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "<b>Как записаться?</b>\n"
    "📝 Пройдите квиз — куратор позвонит сам\n"
    "💬 Напишите администратору напрямую\n"
    "📞 Позвоните и мы запишем вас немедленно"
)

TEAM_TEXT = (
    "👨‍⚕️ <b>КОМАНДА ELEMENTS DENTAL CENTER</b>\n\n"
    "Наши специалисты — это врачи с опытом от 10 лет, "
    "прошедшие подготовку в ведущих клиниках России и Европы.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "🏆 <b>Новодран Вадим Николаевич</b>\n"
    "<i>Главный врач · Челюстно-лицевой хирург · Имплантолог</i>\n"
    "Опыт работы — более 15 лет. Специализация: сложные случаи имплантации.\n\n"
    "🦷 <b>Жданов Виктор Егорович</b>\n"
    "<i>Хирург-имплантолог</i>\n"
    "Эксперт по атрофии кости и синус-лифтингу.\n\n"
    "💎 <b>Руденок Татьяна Леонидовна</b>\n"
    "<i>Гнатолог · Ортопед · Терапевт-стоматолог</i>\n"
    "Единственный гнатолог в клинике. Лечит бруксизм и ВНЧС.\n\n"
    "🔬 <b>Кононенко Андрей Алексеевич</b>\n"
    "<i>Терапевт · Ортопед-стоматолог</i>\n"
    "Мастер реставрации и работы под микроскопом.\n\n"
    "✨ <b>Лебеденко Евгений Владимирович</b>\n"
    "<i>Терапевт · Ортопед-стоматолог</i>\n"
    "Специализация: эстетическая стоматология и виниры.\n\n"
    "📐 <b>Кучеев Никита Витальевич</b>\n"
    "<i>Врач-ортодонт</i>\n"
    "Исправление прикуса и выравнивание зубов для детей и взрослых.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "👩‍⚕️ <b>Степаненко Елена Сергеевна</b> — Старшая медсестра\n"
    "🔧 <b>Смирнов Дмитрий Алексеевич</b> — Зубной техник (собственная лаборатория)"
)

TECH_TEXT = (
    "🔬 <b>ТЕХНОЛОГИИ PREMIUM-КЛАССА</b>\n\n"
    "Мы инвестируем в лучшее оборудование, "
    "чтобы ваше лечение было точным, быстрым и безболезненным.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "🔭 <b>Микроскоп Carl Zeiss (Германия)</b>\n"
    "40-кратное увеличение. Применяется при лечении каналов, "
    "диагностике трещин и извлечении сломанных инструментов. "
    "<i>Результат — сохранение зубов, которые другие врачи предлагают удалить.</i>\n\n"
    "🌊 <b>Аппарат VECTOR</b>\n"
    "Безоперационное лечение пародонтита. Ультразвуковые волны "
    "уничтожают бактерии и снимают воспаление без разрезов и боли.\n\n"
    "🖥 <b>Orthophos S Sirona (КЛКТ)</b>\n"
    "3D-томограф последнего поколения. Даёт полную картину "
    "состояния зубов, корней и кости за один снимок.\n\n"
    "💡 <b>Beyond Polus — Отбеливание холодным светом</b>\n"
    "Самая бережная система отбеливания. Результат до 12 тонов за один сеанс. "
    "Без ожогов десен и чувствительности.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🏭 <b>Собственная зуботехническая лаборатория</b>\n"
    "Коронки, виниры и протезы изготавливаем прямо в клинике — "
    "это ускоряет работу и гарантирует качество."
)

PRICE_MENU_TEXT = (
    "💰 <b>УСЛУГИ И ПРАЙС-ЛИСТ</b>\n\n"
    "Выберите категорию, чтобы узнать стоимость:\n\n"
    "📌 <i>Цены указаны за единицу. Окончательная стоимость "
    "рассчитывается врачом на бесплатной консультации.</i>"
)

PRICE_ORTHO_DENT = (
    "📐 <b>ОРТОДОНТИЯ — Исправление прикуса</b>\n\n"
    "<b>🔩 Установка брекет-системы (одна челюсть):</b>\n"
    "• Металлические брекеты          — 35 000 ₽\n"
    "• Керамические брекеты           — 37 000 ₽\n"
    "• Сапфировые (прозрачные)        — 40 000 ₽\n"
    "• Самолигирующие (Damon)         — 60 000 ₽\n\n"
    "<b>🔎 Диагностика и планирование:</b>\n"
    "• Консультация гнатолога         — 3 000 ₽\n"
    "• Полная диагностика (3D + план) — 8 000 ₽\n\n"
    "<b>🔄 Регулярное обслуживание:</b>\n"
    "• Коррекция (1 челюсть)          — 4 000 ₽\n"
    "• Коррекция (2 челюсти)          — 5 500 ₽\n"
    "• Подклейка брекета              — 1 000 ₽\n"
    "• Мини-винт (скелетная опора)    — 15 000 ₽\n\n"
    "<b>✅ Завершение лечения:</b>\n"
    "• Съёмная ретенционная пластина  — 10 500 ₽\n"
    "• Каппа ретенционная             — 6 500 ₽\n"
    "• Ретейнер несъёмный (1 ед.)     — 3 000 ₽\n"
    "• Ретейнер несъёмный (6 зубов)   — 5 000 ₽\n"
    "• Снятие брекет-системы          — 4 500 ₽\n\n"
)

PRICE_ORTHO_PED = (
    "💎 <b>ОРТОПЕДИЯ И ПРОТЕЗИРОВАНИЕ</b>\n\n"
    "<b>🦷 Виниры и коронки:</b>\n"
    "• Винир керамический (E-MAX)     — 33 000 ₽\n"
    "• Коронка E-MAX                  — 33 000 ₽\n"
    "• Коронка циркониевая            — 35 000 ₽\n"
    "• Металлокерамическая коронка    — 20 000 ₽\n"
    "• Коронка на импланте            — от 22 000 ₽\n"
    "• Вкладка E-MAX (культевая)      — 10 000 – 15 000 ₽\n\n"
    "<b>🔩 Абатменты для имплантов:</b>\n"
    "• Стандартный OSSTEM / БИО       — 7 000 ₽\n"
    "• JDental / Индивидуальный       — 10 000 ₽\n"
    "• Мультиюнит JDental             — 12 000 – 15 000 ₽\n\n"
    "<b>🦷 Съёмные протезы:</b>\n"
    "• Акриловый протез               — 30 000 ₽\n"
    "• Нейлоновый протез              — 45 000 ₽\n\n"
    "<b>📐 Дополнительные услуги:</b>\n"
    "• 3D-сканирование челюсти        — 5 000 ₽\n"
    "• Временная коронка              — 2 000 – 3 000 ₽\n\n"
)

PRICE_THERAPY = (
    "🦷 <b>ТЕРАПИЯ И ЛЕЧЕНИЕ ЗУБОВ</b>\n\n"
    "<b>🦠 Лечение кариеса:</b>\n"
    "• Поверхностный кариес           — 5 000 ₽\n"
    "• Средний кариес                 — 6 000 ₽\n"
    "• Глубокий кариес                — 7 000 ₽\n"
    "• Реставрация (до 1/3 коронки)   — 5 000 ₽\n"
    "• Реставрация (более 1/3)        — 8 000 ₽\n\n"
    "<b>🔬 Эндодонтия (лечение каналов под микроскопом):</b>\n"
    "• Работа под микроскопом         — 4 000 ₽\n"
    "• Инструментальная обработка     — 3 000 – 4 500 ₽\n"
    "• Пломбирование 1 канала         — 3 000 ₽\n"
    "• Распломбировка канала          — 3 000 ₽\n"
    "• Извлечение сломанного инструм. — от 2 000 ₽\n\n"
    "<b>💉 Подготовка к лечению:</b>\n"
    "• Анестезия (местная)            — 1 000 ₽\n"
    "• Консультация с планом лечения  — 3 000 ₽\n\n"
)

PRICE_SURGERY = (
    "🦾 <b>ХИРУРГИЯ И ИМПЛАНТАЦИЯ</b>\n\n"
    "<b>🔩 Имплантация зубов:</b>\n"
    "• Имплант OSSTEM (Корея)         — 35 000 ₽\n"
    "• Имплант JDental (Израиль)      — 50 000 ₽\n"
    "• Хирургический шаблон           — от 4 000 ₽\n"
    "• Синус-лифт (поднятие дна)      — 50 000 ₽\n\n"
    "<b>🔪 Удаление зубов:</b>\n"
    "• Однокорневой зуб               — 4 000 ₽\n"
    "• Многокорневой зуб              — 4 500 ₽\n"
    "• Ретинированный (зуб мудрости)  — 8 000 ₽\n\n"
    "<b>🦴 Костная пластика:</b>\n"
    "• Пластика костной ткани         — 45 000 ₽\n"
    "• Материал Bio-Oss               — 15 000 – 20 000 ₽\n\n"
)

PRICE_HYGIENE = (
    "🧼 <b>ГИГИЕНА И РЕНТГЕНОДИАГНОСТИКА</b>\n\n"
    "<b>🌊 Пародонтология и чистка:</b>\n"
    "• Аппарат VECTOR (2 челюсти)     — 16 000 ₽\n"
    "• Профессиональная чистка (простая) — 4 000 ₽\n"
    "• Профессиональная чистка (сложная) — 6 000 ₽\n"
    "• Отбеливание Beyond Polus (2 чел.) — 16 000 ₽\n\n"
    "<b>📷 Рентгенография:</b>\n"
    "• КЛКТ 3D-снимок (полная КТ)     — 4 000 ₽\n"
    "• Ортопантомограмма (панорама)   — 2 000 ₽\n"
    "• Прицельный снимок              — 500 ₽\n\n"
)

PRICE_FOOTER = (
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🌐 <b>Полный прайс — на нашем сайте.</b>\n"
    "<i>Цена уточняется врачом после первичного осмотра.\n"
    "Первичная консультация + осмотр — <b>БЕСПЛАТНО</b>.</i>"
)

QUIZ_FINISH_ADMIN = (
    "💎 <b>НОВАЯ ЗАЯВКА НА КОНСУЛЬТАЦИЮ</b>\n\n"
    "👤 Клиент: {full_name}\n"
    "📞 Телефон: {phone}\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🎯 Цель визита: {goal}\n"
    "⚡️ Срочность: {urgency}\n"
    "📅 Последний визит к врачу: {last_visit}\n"
    "🧘 Отношение к стоматологу: {comfort}\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🔖 Telegram ID: <code>{user_id}</code>\n"
    "📩 Username: @{username}\n"
    "🕒 Время: {timestamp}"
)

QUIZ_FINISH_USER = (
    "🎉 <b>Отлично, {name}! Ваша заявка принята!</b>\n\n"
    "📋 Что происходит дальше:\n\n"
    "1️⃣ Куратор клиники получил ваши данные\n"
    "2️⃣ В течение рабочего дня с вами свяжутся\n"
    "3️⃣ Вам предложат удобное время для визита\n"
    "4️⃣ На первой встрече врач составит план лечения бесплатно\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⏱ <b>Время ответа:</b> до 2 часов в рабочее время\n"
    "📞 <b>Или позвоните сами:</b> +7 (949) 307-15-85\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<i>Спасибо, что выбрали Elements Dental Center! ❤️</i>"
)


# ═══════════════════════════════════════════════
#              КЛАВИАТУРЫ
# ═══════════════════════════════════════════════

def kb_main() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📝  Подобрать план лечения  ←  СТАРТ", callback_data="quiz_start"))
    kb.row(InlineKeyboardButton(text="💰  Услуги и прайс-лист", callback_data="menu_price"))
    kb.row(InlineKeyboardButton(text="👨‍⚕️  Наши специалисты", callback_data="menu_team"))
    kb.row(InlineKeyboardButton(text="🔬  Технологии и оборудование", callback_data="menu_tech"))
    kb.row(InlineKeyboardButton(text="📍  Контакты и запись", callback_data="menu_contacts"))
    return kb.as_markup()


def kb_back_main() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📝 Записаться на консультацию", callback_data="quiz_start"))
    kb.row(InlineKeyboardButton(text="⬅️  Главное меню", callback_data="to_main"))
    return kb.as_markup()


def kb_contacts() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📝  Записаться через квиз", callback_data="quiz_start"))
    kb.row(InlineKeyboardButton(text="💬  Написать администратору", url="https://t.me/elements_dental"))
    kb.row(InlineKeyboardButton(text="📞  Позвонить: +7 (949) 307-15-85", callback_data="show_phone"))
    kb.row(InlineKeyboardButton(text="🌐  Открыть сайт клиники", url="https://elements-dent.ru/"))
    kb.row(InlineKeyboardButton(text="⬅️  Главное меню", callback_data="to_main"))
    return kb.as_markup()


def kb_price_categories() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📐  Ортодонтия (брекеты, капы)", callback_data="pr:ortho_dent"))
    kb.row(InlineKeyboardButton(text="💎  Ортопедия (виниры, коронки, протезы)", callback_data="pr:ortho_ped"))
    kb.row(InlineKeyboardButton(text="🦷  Терапия (лечение кариеса, каналы)", callback_data="pr:therapy"))
    kb.row(InlineKeyboardButton(text="🦾  Хирургия (импланты, удаление)", callback_data="pr:surgery"))
    kb.row(InlineKeyboardButton(text="🧼  Гигиена, отбеливание, рентген", callback_data="pr:hygiene"))
    kb.row(InlineKeyboardButton(text="⬅️  Главное меню", callback_data="to_main"))
    return kb.as_markup()


def kb_after_price() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📝  Записаться на консультацию (бесплатно)", callback_data="quiz_start"))
    kb.row(InlineKeyboardButton(text="🌐  Полный прайс на сайте", url="https://elements-dent.ru/"))
    kb.row(InlineKeyboardButton(text="⬅️  К категориям услуг", callback_data="menu_price"))
    return kb.as_markup()


def kb_quiz_goal() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🦷  Вылечить больной зуб", callback_data="q_goal:Лечение зуба"))
    kb.row(InlineKeyboardButton(text="✨  Сделать улыбку красивее (виниры/отбеливание)", callback_data="q_goal:Эстетика"))
    kb.row(InlineKeyboardButton(text="🔩  Восстановить утраченные зубы (импланты/протез)", callback_data="q_goal:Восстановление зубов"))
    kb.row(InlineKeyboardButton(text="📐  Исправить прикус (брекеты/капы)", callback_data="q_goal:Исправление прикуса"))
    kb.row(InlineKeyboardButton(text="🧼  Профессиональная чистка / осмотр", callback_data="q_goal:Гигиена и осмотр"))
    kb.row(InlineKeyboardButton(text="🏠  Главное меню", callback_data="to_main"))
    return kb.as_markup()


def kb_quiz_urgency() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🚨  Срочно — болит прямо сейчас", callback_data="q_urgency:Срочно (боль)"))
    kb.row(InlineKeyboardButton(text="📅  В ближайшие 1–2 недели", callback_data="q_urgency:В ближайшие 2 недели"))
    kb.row(InlineKeyboardButton(text="🗓  В течение месяца", callback_data="q_urgency:В течение месяца"))
    kb.row(InlineKeyboardButton(text="🤔  Пока только интересуюсь / выбираю клинику", callback_data="q_urgency:Изучаю варианты"))
    kb.row(InlineKeyboardButton(text="⬅️  Назад", callback_data="quiz_start"))
    return kb.as_markup()


def kb_quiz_last_visit() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✅  Менее 6 месяцев назад", callback_data="q_lv:Недавно (менее 6 месяцев)"))
    kb.row(InlineKeyboardButton(text="📆  От 6 месяцев до года", callback_data="q_lv:6–12 месяцев назад"))
    kb.row(InlineKeyboardButton(text="⏳  Более года назад", callback_data="q_lv:Более года назад"))
    kb.row(InlineKeyboardButton(text="❓  Затрудняюсь вспомнить", callback_data="q_lv:Очень давно / не помню"))
    kb.row(InlineKeyboardButton(text="⬅️  Назад", callback_data="quiz_step2"))
    return kb.as_markup()


def kb_quiz_comfort() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="😊  Спокойно — доверяю врачам", callback_data="q_comfort:Спокойно"))
    kb.row(InlineKeyboardButton(text="😬  Немного волнуюсь, но приду", callback_data="q_comfort:Немного волнуюсь"))
    kb.row(InlineKeyboardButton(text="😰  Сильно боюсь — нужна седация или особый подход", callback_data="q_comfort:Боюсь (нужна помощь)"))
    kb.row(InlineKeyboardButton(text="⬅️  Назад", callback_data="quiz_step3"))
    return kb.as_markup()


def kb_quiz_phone_skip() -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🏠  Главное меню", callback_data="to_main"))
    return kb.as_markup()


# ═══════════════════════════════════════════════
#              ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════

async def safe_edit(message: types.Message, text: str, reply_markup=None) -> None:
    """Редактирует сообщение или шлёт новое при ошибке."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except TelegramBadRequest:
        await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


# ═══════════════════════════════════════════════
#              ОБРАБОТЧИКИ /start
# ═══════════════════════════════════════════════

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    if is_user_registered(message.from_user.id):
        await message.answer(
            WELCOME_BACK.format(name=message.from_user.first_name),
            reply_markup=kb_main(),
        )
    else:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Подтвердить номер телефона", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(WELCOME_NEW, reply_markup=kb)


@dp.message(F.contact)
async def handle_contact(message: types.Message):
    contact = message.contact

    # Защита: нельзя поделиться чужим контактом
    if contact.user_id != message.from_user.id:
        await message.answer("⚠️ Пожалуйста, отправьте <b>ваш собственный</b> номер телефона.", parse_mode="HTML")
        return

    save_to_csv(contact.user_id, contact.first_name or "Не указано", contact.phone_number)

    # Уведомление администратору
    admin_text = (
        f"👤 <b>Новый пользователь верифицирован!</b>\n\n"
        f"Имя: {contact.first_name}\n"
        f"Телефон: {contact.phone_number}\n"
        f"ID: <code>{contact.user_id}</code>\n"
        f"Username: @{message.from_user.username or '—'}\n"
        f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logger.error(f"Не удалось уведомить администратора: {e}")

    await message.answer(
        "✅ <b>Номер подтверждён!</b> Добро пожаловать в Elements.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(MAIN_MENU_TEXT, reply_markup=kb_main())


# ═══════════════════════════════════════════════
#              НАВИГАЦИЯ — ГЛАВНОЕ МЕНЮ
# ═══════════════════════════════════════════════

@dp.callback_query(F.data == "to_main")
async def cb_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await safe_edit(callback.message, MAIN_MENU_TEXT, reply_markup=kb_main())


@dp.callback_query(F.data == "menu_team")
async def cb_team(callback: types.CallbackQuery):
    await callback.answer()
    await safe_edit(callback.message, TEAM_TEXT, reply_markup=kb_back_main())


@dp.callback_query(F.data == "menu_tech")
async def cb_tech(callback: types.CallbackQuery):
    await callback.answer()
    await safe_edit(callback.message, TECH_TEXT, reply_markup=kb_back_main())

@dp.callback_query(F.data == "show_phone")
async def cb_show_phone(callback: types.CallbackQuery):
    await callback.answer("📞 +7 (949) 307-15-85", show_alert=True)


@dp.callback_query(F.data == "menu_contacts")
async def cb_contacts(callback: types.CallbackQuery):
    await callback.answer()
    await safe_edit(callback.message, CONTACTS_TEXT, reply_markup=kb_contacts())


@dp.callback_query(F.data == "menu_price")
async def cb_price(callback: types.CallbackQuery):
    await callback.answer()
    await safe_edit(callback.message, PRICE_MENU_TEXT, reply_markup=kb_price_categories())


# ═══════════════════════════════════════════════
#              ПРАЙС — КАТЕГОРИИ
# ═══════════════════════════════════════════════

PRICE_MAP = {
    "ortho_dent": PRICE_ORTHO_DENT,
    "ortho_ped":  PRICE_ORTHO_PED,
    "therapy":    PRICE_THERAPY,
    "surgery":    PRICE_SURGERY,
    "hygiene":    PRICE_HYGIENE,
}


@dp.callback_query(F.data.startswith("pr:"))
async def cb_price_detail(callback: types.CallbackQuery):
    await callback.answer()
    cat = callback.data.split(":")[1]
    text = PRICE_MAP.get(cat)
    if not text:
        await callback.answer("⚠️ Раздел не найден.", show_alert=True)
        return
    await safe_edit(callback.message, text + PRICE_FOOTER, reply_markup=kb_after_price())


# ═══════════════════════════════════════════════
#              КВИЗ — ШАГ 1
# ═══════════════════════════════════════════════

@dp.callback_query(F.data == "quiz_start")
async def cb_quiz_1(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Quiz.goal)
    await callback.answer()
    await safe_edit(
        callback.message,
        "🦷 <b>Квиз — Шаг 1 из 5</b>\n\n"
        "<b>Какая задача для вас сейчас наиболее важна?</b>\n\n"
        "<i>Выберите один вариант, наиболее подходящий вашей ситуации:</i>",
        reply_markup=kb_quiz_goal(),
    )


# ═══════════════════════════════════════════════
#              КВИЗ — ШАГ 2
# ═══════════════════════════════════════════════

@dp.callback_query(Quiz.goal, F.data.startswith("q_goal:"))
async def cb_quiz_2(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(goal=callback.data.split(":", 1)[1])
    await state.set_state(Quiz.urgency)
    await callback.answer()
    await safe_edit(
        callback.message,
        "⚡️ <b>Квиз — Шаг 2 из 5</b>\n\n"
        "<b>Насколько срочно нужна помощь?</b>\n\n"
        "<i>Это поможет нам предложить вам ближайшее доступное время:</i>",
        reply_markup=kb_quiz_urgency(),
    )


# Кнопка «Назад» на шаг 1
@dp.callback_query(F.data == "quiz_step2")
async def cb_quiz_back_to_1(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Quiz.goal)
    await callback.answer()
    await safe_edit(
        callback.message,
        "🦷 <b>Квиз — Шаг 1 из 5</b>\n\n"
        "<b>Какая задача для вас сейчас наиболее важна?</b>",
        reply_markup=kb_quiz_goal(),
    )


# ═══════════════════════════════════════════════
#              КВИЗ — ШАГ 3
# ═══════════════════════════════════════════════

@dp.callback_query(Quiz.urgency, F.data.startswith("q_urgency:"))
async def cb_quiz_3(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(urgency=callback.data.split(":", 1)[1])
    await state.set_state(Quiz.last_visit)
    await callback.answer()
    await safe_edit(
        callback.message,
        "📅 <b>Квиз — Шаг 3 из 5</b>\n\n"
        "<b>Как давно вы последний раз посещали стоматолога?</b>\n\n"
        "<i>Это помогает врачу заранее подготовиться к вашему визиту:</i>",
        reply_markup=kb_quiz_last_visit(),
    )


# Кнопка «Назад» на шаг 2
@dp.callback_query(F.data == "quiz_step3")
async def cb_quiz_back_to_2(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Quiz.urgency)
    await callback.answer()
    await safe_edit(
        callback.message,
        "⚡️ <b>Квиз — Шаг 2 из 5</b>\n\n"
        "<b>Насколько срочно нужна помощь?</b>",
        reply_markup=kb_quiz_urgency(),
    )


# ═══════════════════════════════════════════════
#              КВИЗ — ШАГ 4
# ═══════════════════════════════════════════════

@dp.callback_query(Quiz.last_visit, F.data.startswith("q_lv:"))
async def cb_quiz_4(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(last_visit=callback.data.split(":", 1)[1])
    await state.set_state(Quiz.comfort)
    await callback.answer()
    await safe_edit(
        callback.message,
        "🧘 <b>Квиз — Шаг 4 из 5</b>\n\n"
        "<b>Как вы обычно относитесь к походу к стоматологу?</b>\n\n"
        "<i>Мы подберём максимально комфортный подход именно для вас:\n"
        "успокоительные препараты, пауза при необходимости или седация.</i>",
        reply_markup=kb_quiz_comfort(),
    )


# ═══════════════════════════════════════════════
#              КВИЗ — ШАГ 5
# ═══════════════════════════════════════════════

@dp.callback_query(Quiz.comfort, F.data.startswith("q_comfort:"))
async def cb_quiz_5(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(comfort=callback.data.split(":", 1)[1])
    await state.set_state(Quiz.phone)
    await callback.answer()
    await safe_edit(
        callback.message,
        "📞 <b>Квиз — Шаг 5 из 5 — Финальный!</b>\n\n"
        "<b>Оставьте номер телефона</b>, и наш куратор свяжется с вами в течение рабочего дня.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Первичная консультация — <b>БЕСПЛАТНО</b>\n"
        "✅ Врач составит индивидуальный план лечения\n"
        "✅ Мы предложим 3 удобных времени для записи\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📱 <b>Напишите ваш номер в формате:</b>\n"
        "<code>+7 (949) 123-45-67</code>",
        reply_markup=kb_quiz_phone_skip(),
    )


# ═══════════════════════════════════════════════
#              КВИЗ — ФИНАЛ (получение телефона)
# ═══════════════════════════════════════════════

@dp.message(Quiz.phone)
async def quiz_final(message: types.Message, state: FSMContext):
    phone = message.text.strip() if message.text else "Не указан"
    data = await state.get_data()
    await state.clear()

    username = message.from_user.username or "—"
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Отправка заявки администратору
    report = QUIZ_FINISH_ADMIN.format(
        full_name=message.from_user.full_name,
        phone=phone,
        goal=data.get("goal", "—"),
        urgency=data.get("urgency", "—"),
        last_visit=data.get("last_visit", "—"),
        comfort=data.get("comfort", "—"),
        user_id=message.from_user.id,
        username=username,
        timestamp=timestamp,
    )
    try:
        await bot.send_message(ADMIN_ID, report)
    except Exception as e:
        logger.error(f"Ошибка уведомления администратора: {e}")

    # Ответ пользователю
    await message.answer(
        QUIZ_FINISH_USER.format(name=message.from_user.first_name),
        reply_markup=kb_main(),
    )


# ═══════════════════════════════════════════════
#    ЕДИНЫЙ ОБРАБОТЧИК СООБЩЕНИЙ (ADMIN <-> USER)
# ═══════════════════════════════════════════════

@dp.message()
async def handle_free_message(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    # 1. Администратор отвечает клиенту через reply
    if message.from_user.id == ADMIN_ID and message.reply_to_message:
        target_id = None
        ref = message.reply_to_message

        if ref.forward_from:
            target_id = ref.forward_from.id
        elif ref.text and "ID:" in ref.text:
            try:
                raw = ref.text.split("ID:")[1].strip().split()[0]
                target_id = int(raw.strip("<code>").strip("</code>"))
            except (ValueError, IndexError):
                pass
        elif ref.caption and "ID:" in ref.caption:
            try:
                raw = ref.caption.split("ID:")[1].strip().split()[0]
                target_id = int(raw.strip("<code>").strip("</code>"))
            except (ValueError, IndexError):
                pass

        if target_id:
            try:
                await bot.copy_message(
                    chat_id=target_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                )
                await message.answer("✅ Сообщение доставлено клиенту!")
            except Exception as e:
                await message.answer(f"❌ Ошибка отправки клиенту: {e}")
        else:
            await message.answer(
                "⚠️ Не удалось определить ID клиента.\n"
                "Отвечайте на сообщение, где есть строка «ID:»."
            )
        return

    # 2. Клиент пишет произвольное сообщение — пересылаем администратору
    if current_state is None and message.from_user.id != ADMIN_ID:
        info = (
            f"📩 <b>Сообщение от клиента</b>\n\n"
            f"Имя: {message.from_user.full_name}\n"
            f"Username: @{message.from_user.username or '—'}\n"
            f"ID: <code>{message.from_user.id}</code>\n"
            f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        try:
            await bot.send_message(ADMIN_ID, info)
            await bot.copy_message(
                chat_id=ADMIN_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
        except Exception as e:
            logger.error(f"Ошибка пересылки сообщения администратору: {e}")

        if message.text and not message.text.startswith("/"):
            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text="🏠  Главное меню", callback_data="to_main"))
            await message.answer(
                "✅ Ваше сообщение передано администратору клиники Elements!\n"
                "Мы ответим вам в ближайшее время.",
                reply_markup=kb.as_markup(),
            )


# ═══════════════════════════════════════════════
#              ЗАПУСК БОТА
# ═══════════════════════════════════════════════

async def main():
    logger.info("🚀 Бот Elements Dental Center запущен!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
