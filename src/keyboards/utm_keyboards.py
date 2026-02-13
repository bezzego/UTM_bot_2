from typing import Iterable, Sequence, Tuple

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_categories_keyboard(categories: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, (name, _) in categories.items():
        builder.add(InlineKeyboardButton(text=name, callback_data=f"manage_category:{key}"))
    builder.add(InlineKeyboardButton(text="❌ Выйти", callback_data="exit_manage"))
    builder.adjust(1)
    return builder.as_markup()


def build_category_management_keyboard(category_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="👁 Просмотреть метки",
            callback_data=f"view_items:{category_key}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="➕ Добавить метку",
            callback_data=f"add_item_prompt:{category_key}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🗑 Удалить метку",
            callback_data=f"delete_item_prompt:{category_key}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="⬅️ Назад к категориям",
            callback_data="back_to_categories"
        )
    )
    builder.adjust(1)
    return builder.as_markup()

def build_view_items_keyboard(category_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_manage:{category_key}"))
    return builder.as_markup()

def build_items_to_delete_keyboard(category_key: str, items: Sequence[Tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, value in items:
        builder.add(
            InlineKeyboardButton(
                text=f"❌ {name}",
                callback_data=f"delete_item:{category_key}:{value}"
            )
        )
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_manage:{category_key}"))
    builder.adjust(1)
    return builder.as_markup()


def build_sources_keyboard(sources: Iterable[Tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    telegram_button = None
    other_buttons: list[InlineKeyboardButton] = []

    for name, value in sources:
        button = InlineKeyboardButton(text=name, callback_data=f"src:{value}")
        if value == "telegram":
            telegram_button = button
        else:
            other_buttons.append(button)

    if telegram_button:
        builder.row(telegram_button)

    for idx in range(0, len(other_buttons), 2):
        builder.row(*other_buttons[idx:idx + 2])

    builder.row(InlineKeyboardButton(text="Другое", callback_data="srcgrp:other"))
    return builder.as_markup()


def build_other_sources_keyboard(items: Iterable[Tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [InlineKeyboardButton(text=name, callback_data=f"src:{value}") for name, value in items]
    for idx in range(0, len(buttons), 2):
        builder.row(*buttons[idx:idx + 2])
    builder.row(InlineKeyboardButton(text="⬅ Назад", callback_data="back:source"))
    return builder.as_markup()


def build_medium_keyboard(items: Iterable[Tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [InlineKeyboardButton(text=name, callback_data=f"med:{value}") for name, value in items]
    for idx in range(0, len(buttons), 2):
        builder.row(*buttons[idx:idx + 2])
    builder.row(InlineKeyboardButton(text="⬅ Назад", callback_data="back:source"))
    return builder.as_markup()


def build_campaign_groups_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📍 Санкт-Петербург", callback_data="campgrp:spb")
    builder.button(text="🏙 Москва", callback_data="campgrp:msk")
    builder.button(text="🌍 Регионы России", callback_data="campgrp:regions")
    builder.button(text="🌐 Зарубежные направления", callback_data="campgrp:foreign")
    builder.adjust(2)
    return builder.as_markup()


def build_campaign_keyboard(items: Iterable[Tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [InlineKeyboardButton(text=name, callback_data=f"camp:{value}") for name, value in items]
    for idx in range(0, len(buttons), 2):
        builder.row(*buttons[idx:idx + 2])
    builder.row(InlineKeyboardButton(text="⬅ Назад", callback_data="back:campaign"))
    return builder.as_markup()


def build_date_choice_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Сегодня", callback_data="adddate:today")
    builder.button(text="📆 Завтра", callback_data="adddate:tomorrow")
    builder.button(text="📆 Послезавтра", callback_data="adddate:dayafter")
    builder.button(text="✏️ Ввести дату", callback_data="adddate:manual")
    builder.button(text="📝 Вписать вручную", callback_data="adddate:manual_content")
    builder.button(text="❌ Не добавлять дату", callback_data="adddate:none")
    builder.adjust(2)
    return builder.as_markup()


def build_manual_content_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="content:confirm")
    builder.button(text="⬅ Назад", callback_data="content:back")
    builder.adjust(2)
    return builder.as_markup()
