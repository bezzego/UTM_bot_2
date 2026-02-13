import re

from aiogram import F, Router, types
from aiogram.filters import Command

from src.keyboards.utm_keyboards import (
    build_categories_keyboard,
    build_category_management_keyboard,
    build_items_to_delete_keyboard,
    build_view_items_keyboard, 
)
from src.services.utm_manager import utm_manager
from src.state.user_state import utm_editing_data


router = Router()


def _reset_add_state(user_id: int) -> None:
    utm_editing_data.pop(user_id, None)


def _is_add_active(user_id: int) -> bool:
    return user_id in utm_editing_data


async def _exit_add_mode(
    user_id: int,
    message: types.Message | None = None,
    callback: types.CallbackQuery | None = None,
) -> None:
    had_state = _is_add_active(user_id)
    _reset_add_state(user_id)

    if callback:
        await callback.answer()

    if not had_state:
        if message:
            await message.answer("Режим управления UTM-метками не активен.")
        elif callback:
            await callback.message.answer("Режим управления UTM-метками не активен.")
        return

    text = "Вы вышли из режима управления UTM-метками."
    if message:
        await message.answer(text)
    elif callback:
        await callback.message.answer(text)


async def start_utm_management(
    user_id: int,
    message: types.Message | None = None,
    callback: types.CallbackQuery | None = None,
) -> None:
    utm_editing_data[user_id] = {"step": None, "category": None}
    categories = utm_manager.get_all_categories()
    text = (
        "🛠 Панель управления UTM-метками\n\n"
        "Выберите категорию для редактирования.\n"
        "Чтобы выйти, отправьте /cancel, напишите «Отмена» или нажмите кнопку «❌ Выйти»."
    )

    if callback:
        await callback.answer()
        if callback.message:
            await callback.message.edit_text(text, reply_markup=build_categories_keyboard(categories))
        return

    if message:
        await message.answer(text, reply_markup=build_categories_keyboard(categories))


@router.message(Command("manage_utm"))
async def cmd_manage_utm(message: types.Message) -> None:
    await start_utm_management(message.from_user.id, message=message)


@router.message(Command("cancel"))
async def cancel_add_command(message: types.Message) -> None:
    await _exit_add_mode(message.from_user.id, message=message)


@router.message(lambda msg: msg.text and msg.text.lower() in {"отмена", "cancel", "выход", "stop"})
async def cancel_add_text(message: types.Message) -> None:
    await _exit_add_mode(message.from_user.id, message=message)


@router.callback_query(F.data.startswith("manage_category:"))
async def select_manage_category(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    category_key = callback.data.split(":", 1)[1]

    utm_editing_data.setdefault(user_id, {})
    utm_editing_data[user_id].update({"category": category_key, "step": "choosing_action"})

    categories = utm_manager.get_all_categories()
    category_name = categories[category_key][0]

    await callback.message.edit_text(
        f"Выбрана категория: {category_name}\n\n"
        "Выберите действие:",
        reply_markup=build_category_management_keyboard(category_key),
    )

@router.callback_query(F.data.startswith("add_item_prompt:"))
async def prompt_add_item(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    category_key = callback.data.split(":", 1)[1]

    utm_editing_data.setdefault(user_id, {})
    utm_editing_data[user_id].update({"category": category_key, "step": "waiting_name"})

    await callback.message.edit_text(
        "Введите название новой метки (например: 'Новый источник'):"
    )

@router.callback_query(F.data.startswith("delete_item_prompt:"))
async def prompt_delete_item(callback: types.CallbackQuery) -> None:
    category_key = callback.data.split(":", 1)[1]
    items = utm_manager.get_category_data(category_key)
    if not items:
        await callback.answer("В этой категории нет меток для удаления.", show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите метку для удаления:",
        reply_markup=build_items_to_delete_keyboard(category_key, items)
    )

@router.callback_query(F.data.startswith("view_items:"))
async def view_items(callback: types.CallbackQuery) -> None:
    category_key = callback.data.split(":", 1)[1]
    items = utm_manager.get_category_data(category_key)
    
    categories = utm_manager.get_all_categories()
    category_name = categories[category_key][0]
    
    if not items:
        await callback.answer(f"В категории '{category_name}' пока нет меток.", show_alert=True)
        return

    text = f"Просмотр меток в категории: {category_name}\n\n"
    text += "\n".join([f"- {name} ({value})" for name, value in items])

    await callback.message.edit_text(
        text,
        reply_markup=build_view_items_keyboard(category_key)
    )


@router.message(lambda msg: utm_editing_data.get(msg.from_user.id, {}).get("step") == "waiting_name")
async def handle_utm_name(message: types.Message) -> None:
    user_id = message.from_user.id
    name = message.text.strip()

    if not name:
        await message.answer("Название не может быть пустым. Попробуйте еще раз:")
        return

    utm_editing_data[user_id]["name"] = name
    utm_editing_data[user_id]["step"] = "waiting_value"

    await message.answer(
        f"Отлично! Название: '{name}'\n\n"
        "Теперь введите значение для UTM-метки (только латинские буквы, цифры и нижние подчеркивания):\n"
        "Пример: new_source_2024"
    )


@router.message(lambda msg: utm_editing_data.get(msg.from_user.id, {}).get("step") == "waiting_value")
async def handle_utm_value(message: types.Message) -> None:
    user_id = message.from_user.id
    value = message.text.strip()

    if not re.match(r"^[A-Za-z0-9._-]+$", value):
        await message.answer(
            "Неверный формат! Используйте только:\n"
            "• латинские буквы (любые)\n"
            "• цифры\n"
            "• нижние подчеркивания, точки и дефисы\n\n"
            "Пример: yandex.promopages\n"
            "Попробуйте еще раз:"
        )
        return

    user_state = utm_editing_data[user_id]
    category_key = user_state["category"]
    name = user_state["name"]

    success = utm_manager.add_item(category_key, name, value)

    if success:
        await message.answer(
            "✅ Успешно добавлено!\n"
            f"Название: {name}\n"
            f"Значение: {value}",
        )
    else:
        await message.answer(
            "❌ Ошибка! Возможно, метка с таким значением уже существует."
        )
    
    _reset_add_state(user_id)
    await start_utm_management(user_id, message=message)



@router.callback_query(F.data.startswith("delete_item:"))
async def delete_utm_item(callback: types.CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("❌ Ошибка!")
        return

    _, category_key, value = parts

    success = utm_manager.delete_item(category_key, value)
    if not success:
        await callback.answer("❌ Ошибка при удалении!")
        return

    await callback.answer("✅ Метка удалена!")

    items = utm_manager.get_category_data(category_key)
    if not items:
        await callback.message.edit_text("Все метки в этой категории были удалены.")
        await start_utm_management(callback.from_user.id, callback=callback)
        return

    await callback.message.edit_text(
        "Выберите метку для удаления:",
        reply_markup=build_items_to_delete_keyboard(category_key, items),
    )


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery) -> None:
    await start_utm_management(callback.from_user.id, callback=callback)


@router.callback_query(F.data.startswith("back_to_manage:"))
async def back_to_manage_category(callback: types.CallbackQuery) -> None:
    category_key = callback.data.split(":", 1)[1]
    categories = utm_manager.get_all_categories()
    category_name = categories[category_key][0]
    await callback.message.edit_text(
        f"Выбрана категория: {category_name}\n\nВыберите действие:",
        reply_markup=build_category_management_keyboard(category_key),
    )

@router.callback_query(F.data == "exit_manage")
async def exit_add_callback(callback: types.CallbackQuery) -> None:
    await _exit_add_mode(callback.from_user.id, callback=callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
