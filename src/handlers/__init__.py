from aiogram import Dispatcher

from .commands import router as commands_router
from .utm_generation import router as utm_generation_router
from .utm_management import router as utm_management_router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(commands_router)
    dp.include_router(utm_management_router)
    dp.include_router(utm_generation_router)
