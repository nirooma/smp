import os
from functools import lru_cache

from pydantic import BaseModel, MongoDsn, RedisDsn


class BaseConfig(BaseModel):
    MONGODB_URI: MongoDsn = "mongodb://admin:password@mongodb:27017"
    REDIS_URI: RedisDsn = "redis://redis:6379"


class DevelopmentConfig(BaseConfig):
    ENVIRONMENT: str = "dev"
    DEBUG: bool = True


class ProductionConfig(BaseConfig):
    ENVIRONMENT: str = "prod"
    DEBUG: bool = False


@lru_cache(1)
def load_settings():
    configs = {
        "production": ProductionConfig,
        "development": DevelopmentConfig,
    }
    return configs.get(os.getenv("ENVIRONMENT"), DevelopmentConfig)()


settings = load_settings()
