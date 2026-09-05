"""
Telegram Bot Keyboards - reusable inline and reply keyboards.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard after /start."""
    keyboard = [
        [KeyboardButton(text="🖨 Новая печать")],
        [KeyboardButton(text="📋 Мои заказы")],
        [KeyboardButton(text="⚙️ Мои данные")],
        [KeyboardButton(text="❓ Помощь")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with cancel button."""
    keyboard = [
        [KeyboardButton(text="❌ Отменить")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_print_mode_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting print mode (B/W or Color)."""
    keyboard = [
        [InlineKeyboardButton(text="⚫ Ч/Б", callback_data="mode_bw")],
        [InlineKeyboardButton(text="🌈 Цвет", callback_data="mode_color")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_copies_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting number of copies."""
    keyboard = [
        [InlineKeyboardButton(text="1", callback_data="copies_1")],
        [InlineKeyboardButton(text="2", callback_data="copies_2")],
        [InlineKeyboardButton(text="3", callback_data="copies_3")],
        [InlineKeyboardButton(text="4", callback_data="copies_4")],
        [InlineKeyboardButton(text="5", callback_data="copies_5")],
        [InlineKeyboardButton(text="Другое количество", callback_data="copies_custom")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Keyboard for confirming order before payment."""
    keyboard = [
        [InlineKeyboardButton(text="💳 Оплатить", callback_data=f"pay_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{order_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_user_data_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for user data management."""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Изменить данные", callback_data="edit_address")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Admin panel main menu."""
    keyboard = [
        [KeyboardButton(text="🖨 Принтер")],
        [KeyboardButton(text="📋 Очередь")],
        [KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="🎁 Бесплатные")],
        [KeyboardButton(text="💰 Финансы")],
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="💵 Тарифы")],
        [KeyboardButton(text="🚨 Ошибки")],
        [KeyboardButton(text="⚙️ Настройки")],
        [KeyboardButton(text="🔙 Выход из админки")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def get_job_actions_keyboard(job_id: int) -> InlineKeyboardMarkup:
    """Keyboard for admin job actions."""
    keyboard = [
        [InlineKeyboardButton(text="⏸ Pause", callback_data=f"admin_pause_{job_id}")],
        [InlineKeyboardButton(text="▶️ Resume", callback_data=f"admin_resume_{job_id}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data=f"admin_cancel_{job_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_resume_from_page_keyboard(job_id: int) -> InlineKeyboardMarkup:
    """Keyboard for resuming job from specific page."""
    keyboard = [
        [InlineKeyboardButton(text="📄 Указать страницу", callback_data=f"admin_page_{job_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
