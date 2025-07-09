from config import LOGS
from loguru import logger


logger.add(
    sink=LOGS,
    enqueue=True,
    rotation='1 MB',
    compression='zip',
    format='{time} {level} {message}',
    level='DEBUG',
    catch=True
)