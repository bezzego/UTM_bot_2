from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Tuple, Dict, Sequence


# --- Клавиатуры для генератора UTM ---

def build_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Источник (source)", callback_data="select_category:source")
    builder.button(text="📎 Тип трафика (medium)", callback_data="select_category:medium")
    builder.button(text="🚀 Кампания (campaign)", callback_data="select_category:campaign")
    # Эти кнопки пока не реализованы в хендлерах, но они есть в дизайне
    # builder.button(text="📝 Контент (content)", callback_data="select_category:content")
    # builder.button(text="🔑 Ключевое слово (term)", callback_data="select_category:term")
    builder.button(text="✅ Сгенерировать ссылку", callback_data="generate_link")
    builder.button(text="❌ Сбросить все", callback_data="reset_all")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def build_sources_keyboard(sources: Sequence[Tuple[str, str]]) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Отделяем Telegram от остальных
    telegram_source = None
    other_sources_list = []
    for name, value in sources:
        if value == "telegram":
            telegram_source = (name, value)
        else:
            other_sources_list.append((name, value))

    # Добавляем кнопку Telegram на отдельную строку
    if telegram_source:
        builder.button(text=telegram_source[0], callback_data=f"src:{telegram_source[1]}")
    
    # Добавляем остальные кнопки
    for name, value in other_sources_list:
        builder.button(text=name, callback_data=f"src:{value}")
    
    builder.button(text="Другое...", callback_data="srcgrp:other")

    # Собираем схему клавиатуры
    layout = []
    if telegram_source:
        layout.append(1) # Telegram в один ряд
    
    num_other_buttons = len(other_sources_list) + 1 # +1 для кнопки "Другое..."
    layout.extend([2] * (num_other_buttons // 2))
    if num_other_buttons % 2:
        layout.append(1)

    builder.adjust(*layout)
    return builder.as_markup()


def build_other_sources_keyboard(other_sources: Sequence[Tuple[str, str]]) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, value in other_sources:
        builder.button(text=name, callback_data=f"src:{value}")
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back:source"))
    return builder.as_markup()


def build_medium_keyboard(mediums: Sequence[Tuple[str, str]]) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, value in mediums:
        builder.button(text=name, callback_data=f"med:{value}")
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back:source"))
    return builder.as_markup()


def build_campaign_category_keyboard(categories: Dict[str, str]):
    builder = InlineKeyboardBuilder()
    for name, key in categories.items():
        builder.button(text=name, callback_data=f"select_campaign_category:{key}")
    builder.adjust(2)
    # Возврат на шаг выбора medium
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back:medium"))
    return builder.as_markup()


def build_campaign_keyboard(items: List[Tuple[str, str]], category_key: str, page: int = 1):
    builder = InlineKeyboardBuilder()
    
    display_items = []
    show_more_button = False

    if category_key == "regions":
        TOP_ITEMS_COUNT = 9
        if page == 1:
            display_items = items[:TOP_ITEMS_COUNT]
            if len(items) > TOP_ITEMS_COUNT:
                show_more_button = True
        else: # page == 2 or more
            display_items = items[TOP_ITEMS_COUNT:]
    else:
        display_items = items

    for full_name, value in display_items:
        short_name = full_name
        if category_key in ["regions", "foreign"]:
            if "Все позиции в " in full_name:
                short_name = full_name.replace("Все позиции в ", "Всё в ")
            if len(short_name) > 20:
                 short_name = short_name.replace("Всё в ", "")

        builder.button(text=short_name, callback_data=f"select_item:campaign:{value}")
    
    builder.adjust(2)

    if show_more_button:
        builder.row(types.InlineKeyboardButton(text="Показать еще 📜", callback_data=f"select_campaign_page:{category_key}:2"))

    if category_key == "regions" and page > 1:
        builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_campaign_page:{category_key}:1"))
    else:
        builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="select_category:campaign"))
        
    return builder.as_markup()


def build_date_choice_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Сегодня", callback_data="adddate:today")
    builder.button(text="Завтра", callback_data="adddate:tomorrow")
    builder.button(text="Послезавтра", callback_data="adddate:dayafter")
    builder.button(text="Ввести вручную", callback_data="adddate:manual")
    builder.button(text="Без даты", callback_data="adddate:none")
    builder.button(text="Вписать utm_content вручную", callback_data="adddate:manual_content")
    builder.adjust(3, 2, 1)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back:campaign"))
    return builder.as_markup()


def build_manual_content_confirm_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="content:confirm")
    builder.button(text="⬅️ Назад", callback_data="content:back")
    builder.adjust(1)
    return builder.as_markup()

# --- Клавиатуры для управления UTM ---

def build_categories_keyboard(categories: Dict[str, Tuple[str, str]]):
    builder = InlineKeyboardBuilder()
    for key, (name, _) in categories.items():
        builder.button(text=name, callback_data=f"manage_category:{key}")
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="Выйти", callback_data="exit_manage"))
    return builder.as_markup()

def build_category_management_keyboard(category_key: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="👁 Просмотреть метки", callback_data=f"view_items:{category_key}")
    builder.button(text="➕ Добавить метку", callback_data=f"add_item_prompt:{category_key}")
    builder.button(text="➖ Удалить метку", callback_data=f"delete_item_prompt:{category_key}")
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="back_to_categories"))
    return builder.as_markup()

def build_items_to_delete_keyboard(category_key: str, items: List[Tuple[str, str]]):
    builder = InlineKeyboardBuilder()
    for name, value in items:
        display_name = f"{name} ({value})"
        builder.button(text=f"❌ {display_name}", callback_data=f"delete_item:{category_key}:{value}")
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_manage:{category_key}"))
    return builder.as_markup()

def build_view_items_keyboard(category_key: str):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_manage:{category_key}"))
    return builder.as_markup()