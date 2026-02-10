from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.services.database import database


class AccessControlMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None)
        if from_user is None:
            return await handler(event, data)

        user_id = from_user.id

        if database.is_user_banned(user_id):
            await self._notify_banned(event)
            return None

        handler_object = data.get("handler")
        flags = getattr(handler_object, "flags", {}) if handler_object else {}

        if not flags.get("auth_required", True):
            return await handler(event, data)

        if not database.is_user_authorized(user_id):
            await self._prompt_for_password(event)
            return None

        return await handler(event, data)

    async def _notify_banned(self, event: TelegramObject) -> None:
        text = "⛔️ Доступ к боту запрещён."
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
            if event.message:
                await event.message.answer(text)
        elif isinstance(event, Message):
            await event.answer(text)

    async def _prompt_for_password(self, event: TelegramObject) -> None:
        text = "🔐 Введите пароль командой /start, чтобы получить доступ к боту."
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
            if event.message:
                await event.message.answer(text)
        elif isinstance(event, Message):
            await event.answer(text)
