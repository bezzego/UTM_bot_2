import re
from aiogram import F, Router, types
from aiogram.filters import Command

# Теперь мы импортируем сам класс, а не глобальный объект
from src.services.utm_manager import UTMManager 
from src.keyboards.utm_keyboards import (
    build_categories_keyboard,
    build_category_management_keyboard,
    build_items_to_delete_keyboard,
    build_view_items_keyboard,
)
from src.state.user_state import utm_editing_data

router = Router()

# --- Вспомогательные функции для управления состоянием ---
def _reset_user_state(user_id: int):
    utm_editing_data.pop(user_id, None)

# --- Функции для управления режимом редактирования ---
async def _exit_utm_mode(user_id: int, message: types.Message, callback: types.CallbackQuery | None = None):
    _reset_user_state(user_id)
    await message.answer("Вы вышли из режима управления UTM-метками.")
    if callback:
        await callback.answer()

async def start_utm_management(user_id: int, message: types.Message | None = None, callback: types.CallbackQuery | None = None):
    # Создаем НОВЫЙ экземпляр UTMManager КАЖДЫЙ РАЗ при входе в управление
    utm_manager = UTMManager()
    
    categories = utm_manager.get_all_categories()
    text = (
        "🛠 Панель управления UTM-метками\n\n"
        "Выберите категорию для редактирования.\n"
        "Чтобы выйти, отправьте /cancel или напишите «Отмена»."
    )
    
    keyboard = build_categories_keyboard(categories)

    if callback:
        await callback.answer()
        await callback.message.edit_text(text, reply_markup=keyboard)
    elif message:
        await message.answer(text, reply_markup=keyboard)

# --- Обработчики команд ---
@router.message(Command("manage_utm"))
async def cmd_manage_utm(message: types.Message):
    await start_utm_management(message.from_user.id, message=message)

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    await _exit_utm_mode(message.from_user.id, message)

@router.message(F.text.lower().in_(["отмена", "cancel", "стоп"]))
async def text_cancel(message: types.Message):
    if message.from_user.id in utm_editing_data:
        await _exit_utm_mode(message.from_user.id, message)

# --- Обработчики колбеков (кнопок) ---
@router.callback_query(F.data.startswith("manage_category:"))
async def cb_manage_category(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    category_key = callback.data.split(":", 1)[1]
    
    # Создаем новый экземпляр, чтобы быть уверенными в свежести данных
    utm_manager = UTMManager()
    categories = utm_manager.get_all_categories()
    category_name = categories[category_key][0]

    utm_editing_data[user_id] = {"category": category_key, "step": "choosing_action"}

    await callback.message.edit_text(
        f"Выбрана категория: {category_name}\n\nВыберите действие:",
        reply_markup=build_category_management_keyboard(category_key)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("view_items:"))
async def cb_view_items(callback: types.CallbackQuery):
    utm_manager = UTMManager()
    long_category_key = callback.data.split(":", 1)[1]
    categories = utm_manager.get_all_categories()
    
    category_name, short_category_key = categories[long_category_key]
    items = utm_manager.get_category_data(short_category_key)

    if not items:
        await callback.answer(f"В категории '{category_name}' пока нет меток.", show_alert=True)
        return

    text = f"Просмотр меток в категории: {category_name}\n\n"
    text += "\n".join([f"- {name} ({value})" for name, value in items])

    await callback.message.edit_text(text, reply_markup=build_view_items_keyboard(long_category_key))
    await callback.answer()

@router.callback_query(F.data.startswith("add_item_prompt:"))
async def cb_add_item_prompt(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    long_category_key = callback.data.split(":", 1)[1]
    
    utm_manager = UTMManager()
    categories = utm_manager.get_all_categories()
    _, short_category_key = categories[long_category_key]

    utm_editing_data[user_id] = {"category": short_category_key, "step": "waiting_name"}

    await callback.message.edit_text("Введите название новой метки (например: 'Новый источник'):")
    await callback.answer()


@router.callback_query(F.data.startswith("delete_item_prompt:"))
async def cb_delete_item_prompt(callback: types.CallbackQuery):
    utm_manager = UTMManager()
    long_category_key = callback.data.split(":", 1)[1]
    categories = utm_manager.get_all_categories()
    _, short_category_key = categories[long_category_key]

    items = utm_manager.get_category_data(short_category_key)
    if not items:
        await callback.answer("В этой категории нет меток для удаления.", show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите метку для удаления:",
        reply_markup=build_items_to_delete_keyboard(long_category_key, items)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_item:"))
async def cb_delete_item(callback: types.CallbackQuery):
    utm_manager = UTMManager()
    _, long_category_key, value = callback.data.split(":", 2)
    categories = utm_manager.get_all_categories()
    _, short_category_key = categories[long_category_key]

    if utm_manager.delete_item(short_category_key, value):
        await callback.answer("✅ Метка удалена!", show_alert=True)
        # Обновляем список для удаления
        items = utm_manager.get_category_data(short_category_key)
        if not items:
            await callback.message.edit_text("Все метки в этой категории были удалены.")
            await start_utm_management(callback.from_user.id, callback.message)
        else:
            await callback.message.edit_text(
                "Выберите метку для удаления:",
                reply_markup=build_items_to_delete_keyboard(long_category_key, items)
            )
    else:
        await callback.answer("❌ Ошибка при удалении!", show_alert=True)


# --- Обработчики текстовых сообщений в режиме редактирования ---
@router.message(lambda msg: utm_editing_data.get(msg.from_user.id, {}).get("step") == "waiting_name")
async def process_utm_name(message: types.Message):
    user_id = message.from_user.id
    if not message.text or not message.text.strip():
        await message.answer("Название не может быть пустым. Попробуйте снова.")
        return
    
    utm_editing_data[user_id]["name"] = message.text.strip()
    utm_editing_data[user_id]["step"] = "waiting_value"
    await message.answer(
        f"Отлично! Название: '{utm_editing_data[user_id]['name']}'\n\n"
        f"Теперь введите значение (латиница, цифры, _, -):"
    )

@router.message(lambda msg: utm_editing_data.get(msg.from_user.id, {}).get("step") == "waiting_value")
async def process_utm_value(message: types.Message):
    user_id = message.from_user.id
    value = message.text.strip() if message.text else ""
    
    if not re.match(r"^[A-Za-z0-9._-]+$", value):
        await message.answer("Неверный формат! Только латиница, цифры и символы '._-'. Попробуйте снова.")
        return

    state = utm_editing_data[user_id]
    utm_manager = UTMManager()
    
    if utm_manager.add_item(state["category"], state["name"], value):
        await message.answer(f"✅ Успешно добавлено!\nНазвание: {state['name']}\nЗначение: {value}")
    else:
        await message.answer("❌ Ошибка! Возможно, метка с таким значением уже существует.")

    _reset_user_state(user_id)
    await start_utm_management(user_id, message)

# --- Навигационные колбеки ---
@router.callback_query(F.data == "back_to_categories")
async def cb_back_to_categories(callback: types.CallbackQuery):
    await start_utm_management(callback.from_user.id, callback=callback)

@router.callback_query(F.data.startswith("back_to_manage:"))
async def cb_back_to_manage_category(callback: types.CallbackQuery):
    await cb_manage_category(callback) # Просто вызываем обработчик управления категорией

@router.callback_query(F.data == "exit_manage")
async def cb_exit_manage(callback: types.CallbackQuery):
    await _exit_utm_mode(callback.from_user.id, callback.message, callback)
