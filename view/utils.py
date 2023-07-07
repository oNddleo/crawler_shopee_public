import time
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


def timer(function):
    def wrapper(*args, **kws):
        t_start = time.time()
        result = function(*args, **kws)
        t_end = time.time()
        t_count = t_end - t_start
        logger.info(
            f"<function {function.__qualname__}> - Time Coast: "
            f"{t_count:.2f}s \n"
        )
        return result

    return wrapper


def buildQueryString(d: dict):
    return urlencode(d)
