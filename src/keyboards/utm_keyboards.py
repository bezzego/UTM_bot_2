from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Tuple, Dict

# --- Клавиатуры для генератора UTM ---
def build_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Источник (source)", callback_data="select_category:source")
    builder.button(text="📎 Тип трафика (medium)", callback_data="select_category:medium")
    builder.button(text="🚀 Кампания (campaign)", callback_a="select_category:campaign")
    builder.button(text="📝 Контент (content)", callback_data="select_category:content")
    builder.button(text="🔑 Ключевое слово (term)", callback_data="select_category:term")
    builder.button(text="✅ Сгенерировать ссылку", callback_data="generate_link")
    builder.button(text="❌ Сбросить все", callback_data="reset_all")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def build_selection_keyboard(items: List[Tuple[str, str]], category: str):
    builder = InlineKeyboardBuilder()
    for name, value in items:
        builder.button(text=name, callback_data=f"select_item:{category}:{value}")
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def build_campaign_category_keyboard(categories: Dict[str, str]):
    builder = InlineKeyboardBuilder()
    for name, key in categories.items():
        builder.button(text=name, callback_data=f"select_campaign_category:{key}")
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))
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

    # Сокращаем текст на кнопках
    for full_name, value in display_items:
        short_name = full_name
        if category_key in ["regions", "foreign"]:
            if "Все позиции в " in full_name:
                short_name = full_name.replace("Все позиции в ", "Всё в ")
            if len(short_name) > 20: # Эмпирическое ограничение для избежания переноса
                 short_name = short_name.replace("Всё в ", "")

        builder.button(text=short_name, callback_data=f"select_item:campaign:{value}")
    
    builder.adjust(2)

    if show_more_button:
        builder.row(types.InlineKeyboardButton(text="Показать еще 📜", callback_data=f"select_campaign_page:{category_key}:2"))

    # Кнопка "Назад"
    if category_key == "regions" and page > 1:
        # Для второй страницы регионов, "Назад" возвращает на первую страницу
        builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_campaign_page:{category_key}:1"))
    else:
        # Для всех остальных случаев, "Назад" возвращает к выбору категории кампании
        builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="select_category:campaign"))
        
    return builder.as_markup()

# --- Клавиатуры для управления UTM ---
from aiogram import types

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
