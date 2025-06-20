from beanie import init_beanie
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from core.settings import settings
from db.address import Address
from db.transaction import Transaction


async def initialize_mongodb():
    logger.info(f"Start mongodb connection - {settings.MONGODB_URI!r}")
    client = AsyncIOMotorClient(settings.MONGODB_URI)

    await init_beanie(database=client.db_name, document_models=[Transaction, Address])
    logger.info(f"Connection with mongodb successfully established")
