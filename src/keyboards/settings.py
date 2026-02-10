from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="🔐 Поменять пароль",
            callback_data="settings:change_password",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🛠 Управление UTM",
            callback_data="settings:utm_manage",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="👥 Просмотреть пользователей",
            callback_data="settings:view_users",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🗑 Удалить пользователя",
            callback_data="settings:delete_user",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="⬅️ Выйти",
            callback_data="settings:exit",
        )
    )
    builder.adjust(1)
    return builder.as_markup()
