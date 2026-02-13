from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_settings_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🔐 Изменить пароль бота", callback_data="settings:change_password")],
        [InlineKeyboardButton(text="👥 Посмотреть пользователей", callback_data="settings:view_users")],
        [InlineKeyboardButton(text="🗑 Удалить пользователя", callback_data="settings:delete_user")],
        [InlineKeyboardButton(text="⚙️ Управление UTM", callback_data="settings:utm_manage")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="settings:exit")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
