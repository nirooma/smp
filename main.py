from fastapi import FastAPI
from loguru import logger

from controllers.v1 import simpliance
from core.logging import set_logging
from core.settings import settings
from db.mongodb import initialize_mongodb
from db.redis import initialize_redis


async def on_startup():
    await initialize_mongodb()
    await initialize_redis()

    logger.info("Application is ready to accept new connections")


def create_application() -> FastAPI:
    application = FastAPI(
        debug=settings.DEBUG,
        on_startup=[on_startup]
    )

    set_logging()

    application.include_router(simpliance.router)

    return application


app = create_application()
