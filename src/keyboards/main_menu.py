from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard_layout = [
        [KeyboardButton(text="Отправить ссылку")],
        [
            KeyboardButton(text="Добавить UTM"),
            KeyboardButton(text="Посмотреть историю"),
        ],
        [KeyboardButton(text="Настройки")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard_layout,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
