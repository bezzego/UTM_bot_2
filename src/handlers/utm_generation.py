import datetime
import logging
from typing import Optional, Sequence, Tuple, Dict

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from src.keyboards.utm_keyboards import (
    build_campaign_category_keyboard,
    build_campaign_keyboard,
    build_date_choice_keyboard,
    build_manual_content_confirm_keyboard,
    build_medium_keyboard,
    build_other_sources_keyboard,
    build_sources_keyboard,
)
from src.services.utm_builder import build_utm_url
from src.services.utm_manager import utm_manager
from src.services.database import database
from src.utils.utm import build_utm_content_with_date, extract_action_slug

logger = logging.getLogger(__name__)
router = Router()


class UTMGenerationStates(StatesGroup):
    base_url = State()
    utm_source = State()
    utm_medium = State()
    utm_campaign = State()
    utm_content = State()
    date_for_utm = State()
    awaiting_date = State()
    awaiting_content = State()


# --- Получение данных из UTM Manager ---

def get_utm_sources() -> Sequence[Tuple[str, str]]:
    return utm_manager.get_category_data("source")

def get_utm_other_sources() -> Sequence[Tuple[str, str]]:
    return utm_manager.get_category_data("source_other")

def get_utm_mediums() -> Sequence[Tuple[str, str]]:
    return utm_manager.get_category_data("medium")

CAMPAIGN_CATEGORIES: Dict[str, str] = {
    "📍 СПБ кампании": "spb",
    "🏙 МСК кампании": "msk",
    "🌍 Регионы кампании": "regions",
    "🌐 Зарубежье кампании": "foreign",
}

CAMPAIGN_GROUPS_MAP = {
    "spb": "campaign_spb",
    "msk": "campaign_msk",
    "regions": "campaign_regions",
    "foreign": "campaign_foreign",
}

def get_utm_campaigns(group: str) -> Sequence[Tuple[str, str]]:
    category_key = CAMPAIGN_GROUPS_MAP.get(group)
    if not category_key:
        return []
    return utm_manager.get_category_data(category_key)

# --- Обработчики процесса генерации UTM ---

@router.message(F.text.regexp(r"^https?://"))
async def handle_base_url(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(base_url=message.text.strip())
    logger.info("Received base URL: %s", message.text.strip())

    sources = get_utm_sources()
    if not sources:
        await message.answer("❌ Список utm_source пуст. Добавьте данные через /manage.")
        return

    await message.answer(
        "1️⃣ Выберите источник трафика (utm_source):",
        reply_markup=build_sources_keyboard(sources),
    )


@router.callback_query(F.data == "srcgrp:other")
async def open_other_sources(callback: types.CallbackQuery) -> None:
    other_sources = get_utm_other_sources()
    if not other_sources:
        await callback.answer("В разделе «Другое» пока нет меток.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        "1️⃣ Выберите источник из раздела «Другое»:",
        reply_markup=build_other_sources_keyboard(other_sources),
    )


@router.callback_query(F.data.startswith("src:"))
async def select_source(callback: types.CallbackQuery, state: FSMContext) -> None:
    source_val = callback.data.split(":", 1)[1]
    await state.update_data(utm_source=source_val)
    logger.info("Selected utm_source: %s", source_val)

    await callback.answer()
    
    mediums = get_utm_mediums()
    if not mediums:
        await callback.message.edit_text("❌ Список utm_medium пуст. Добавьте данные через /manage.")
        return

    await callback.message.edit_text(
        f"Источник: {source_val}\n\n2️⃣ Выберите тип трафика (utm_medium):",
        reply_markup=build_medium_keyboard(mediums),
    )


@router.callback_query(F.data.startswith("med:"))
async def select_medium(callback: types.CallbackQuery, state: FSMContext) -> None:
    medium_val = callback.data.split(":", 1)[1]
    await state.update_data(utm_medium=medium_val)
    logger.info("Selected utm_medium: %s", medium_val)

    await callback.answer()
    data = await state.get_data()
    await callback.message.edit_text(
        f"Источник: {data.get('utm_source')}\nТип: {medium_val}\n\n3️⃣ Выберите категорию кампании (utm_campaign):",
        reply_markup=build_campaign_category_keyboard(CAMPAIGN_CATEGORIES),
    )

@router.callback_query(F.data == "select_category:campaign")
async def select_campaign_main_category(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(
        f"Источник: {data.get('utm_source')}\nТип: {data.get('utm_medium')}\n\n3️⃣ Выберите категорию кампании (utm_campaign):",
        reply_markup=build_campaign_category_keyboard(CAMPAIGN_CATEGORIES),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_campaign_category:"))
async def select_campaign_category(callback: types.CallbackQuery, state: FSMContext) -> None:
    category_key = callback.data.split(":", 1)[1]
    campaigns = get_utm_campaigns(category_key)
    if not campaigns:
        await callback.answer("В этой группе пока нет меток.", show_alert=True)
        return

    await callback.answer()
    data = await state.get_data()
    await callback.message.edit_text(
        f"Источник: {data.get('utm_source')}\nТип: {data.get('utm_medium')}\n\n4️⃣ Выберите кампанию:",
        reply_markup=build_campaign_keyboard(campaigns, category_key, page=1),
    )

@router.callback_query(F.data.startswith("select_campaign_page:"))
async def select_campaign_page(callback: types.CallbackQuery, state: FSMContext):
    _, category_key, page_str = callback.data.split(":", 2)
    page = int(page_str)
    campaigns = get_utm_campaigns(category_key)
    if not campaigns:
        await callback.answer("В этой группе пока нет меток.", show_alert=True)
        return

    await callback.answer()
    data = await state.get_data()
    await callback.message.edit_text(
        f"Источник: {data.get('utm_source')}\nТип: {data.get('utm_medium')}\n\n4️⃣ Выберите кампанию:",
        reply_markup=build_campaign_keyboard(campaigns, category_key, page=page),
    )


@router.callback_query(F.data.startswith("select_item:campaign:"))
async def select_campaign(callback: types.CallbackQuery, state: FSMContext) -> None:
    campaign_val = callback.data.split(":", 2)[2]
    await state.update_data(utm_campaign=campaign_val)
    logger.info("Selected utm_campaign: %s", campaign_val)

    await callback.answer()
    data = await state.get_data()
    await callback.message.edit_text(
        f"Источник: {data.get('utm_source')}\nТип: {data.get('utm_medium')}\nКампания: {campaign_val}\n\n5️⃣ Добавить дату в utm_content?",
        reply_markup=build_date_choice_keyboard(),
    )


@router.callback_query(F.data.startswith("adddate:"))
async def add_date_choice(callback: types.CallbackQuery, state: FSMContext) -> None:
    choice = callback.data.split(":", 1)[1]
    await state.update_data(awaiting_date=False, awaiting_content=False)

    if choice == "today":
        today = datetime.date.today().isoformat()
        await state.update_data(date_for_utm=today)
        await generate_short_link(state, callback=callback)

    elif choice == "tomorrow":
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        await state.update_data(date_for_utm=tomorrow)
        await generate_short_link(state, callback=callback)

    elif choice == "dayafter":
        day_after = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
        await state.update_data(date_for_utm=day_after)
        await generate_short_link(state, callback=callback)

    elif choice == "none":
        await state.update_data(date_for_utm=None)
        await generate_short_link(state, callback=callback)

    elif choice == "manual_content":
        await state.set_state(UTMGenerationStates.awaiting_content)
        await state.update_data(awaiting_content=True)
        await callback.message.answer(
            "Введите utm_content вручную. После ввода нажмите «Подтвердить».",
            reply_markup=build_manual_content_confirm_keyboard(),
        )
    elif choice == "manual":
        await state.set_state(UTMGenerationStates.awaiting_date)
        await state.update_data(awaiting_date=True)
        await callback.message.answer("Введите дату в формате YYYY-MM-DD (например: 2025-10-10)")
    
    await callback.answer()


@router.message(UTMGenerationStates.awaiting_date)
async def handle_manual_date(message: types.Message, state: FSMContext) -> None:
    date_str = message.text.strip()
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await message.answer("Неверный формат даты. Введите в формате YYYY-MM-DD.")
        return

    await state.update_data(date_for_utm=date_str, awaiting_date=False)
    await generate_short_link(state, message=message)


@router.message(UTMGenerationStates.awaiting_content)
async def handle_manual_content(message: types.Message, state: FSMContext) -> None:
    content_text = (message.text or "").strip()
    if not content_text:
        await message.answer("utm_content не может быть пустым. Попробуйте ещё раз.")
        return

    await state.update_data(utm_content=content_text)
    await message.answer(
        f"Сохранено utm_content: {content_text}\nНажмите «Подтвердить», чтобы сформировать ссылку.",
        reply_markup=build_manual_content_confirm_keyboard(),
    )


@router.callback_query(F.data == "content:confirm")
async def confirm_manual_content(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("utm_content"):
        await callback.answer("Сначала введите utm_content.", show_alert=True)
        return
    await state.update_data(awaiting_content=False, date_for_utm=None)
    await callback.answer()
    await generate_short_link(state, callback=callback)


@router.callback_query(F.data == "content:back")
async def back_from_manual_content(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(None)
    await state.update_data(awaiting_content=False, utm_content=None)
    data = await state.get_data()
    await callback.answer()
    await callback.message.edit_text(
        f"Источник: {data.get('utm_source')}\nТип: {data.get('utm_medium')}\nКампания: {data.get('utm_campaign')}\n\n5️⃣ Добавить дату в utm_content?",
        reply_markup=build_date_choice_keyboard(),
    )

# --- Генерация ссылки и навигация ---

async def generate_short_link(
    state: FSMContext,
    message: Optional[types.Message] = None,
    callback: Optional[types.CallbackQuery] = None,
) -> None:
    user_id = callback.from_user.id if callback else message.from_user.id
    data = await state.get_data()
    
    base_url = data.get("base_url", "")
    utm_source = data.get("utm_source")
    utm_medium = data.get("utm_medium")
    utm_campaign = data.get("utm_campaign")
    utm_content_manual = data.get("utm_content")
    date_for_utm = data.get("date_for_utm")

    if utm_content_manual:
        utm_content = utm_content_manual
    else:
        base_slug = extract_action_slug(base_url)
        utm_content = build_utm_content_with_date(base_slug, date_for_utm)

    full_url = build_utm_url(base_url, utm_source, utm_medium, utm_campaign, utm_content)
    logger.info("Full UTM URL for user %s: %s", user_id, full_url)

    database.add_history(user_id, base_url, full_url, full_url)

    result_text = (
        f"✅ Результаты генерации ссылок:\n\n"
        f"🔗 Исходная:\n{base_url}\n\n"
        f"🧩 С UTM:\n{full_url}"
    )
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть API Гориболета", web_app=WebAppInfo(url="https://api.gorbilet.com/v2/admin/"))]
    ])

    await _reply(message, callback, result_text, reply_markup=admin_keyboard)
    await state.clear()


async def _reply(
    message: Optional[types.Message],
    callback: Optional[types.CallbackQuery],
    text: str,
    reply_markup: Optional[types.InlineKeyboardMarkup] = None,
) -> None:
    kwargs = {"disable_web_page_preview": True}
    if reply_markup:
        kwargs["reply_markup"] = reply_markup
    if callback:
        await callback.message.answer(text, **kwargs)
    elif message:
        await message.answer(text, **kwargs)


@router.callback_query(F.data.startswith("back:"))
async def go_back(callback: types.CallbackQuery, state: FSMContext) -> None:
    target = callback.data.split(":", 1)[1]
    await callback.answer()

    if target == "source":
        sources = get_utm_sources()
        await callback.message.edit_text(
            "1️⃣ Выберите источник трафика (utm_source):",
            reply_markup=build_sources_keyboard(sources),
        )
    elif target == "medium":
        mediums = get_utm_mediums()
        data = await state.get_data()
        await callback.message.edit_text(
            f"Источник: {data.get('utm_source')}\n\n2️⃣ Выберите тип трафика (utm_medium):",
            reply_markup=build_medium_keyboard(mediums),
        )
    elif target == "campaign":
        data = await state.get_data()
        await callback.message.edit_text(
            f"Источник: {data.get('utm_source')}\nТип: {data.get('utm_medium')}\n\n3️⃣ Выберите категорию кампании (utm_campaign):",
            reply_markup=build_campaign_category_keyboard(CAMPAIGN_CATEGORIES),
        )
