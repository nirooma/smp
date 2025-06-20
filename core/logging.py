import sys

from loguru import logger


def set_logging():
    logger.remove(0)
    logger.add(sys.stdout, colorize=True,
               format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>')
