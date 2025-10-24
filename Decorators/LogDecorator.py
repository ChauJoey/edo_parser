import functools
import logging
import time

from quart import request

logger = logging.getLogger('quart.app')


def LogNormal(func):
    """
    装饰器函数，用于测量另一个函数的执行时间。
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Function {func.__name__} start!")
        requestJson = await request.json
        print('This is request json:' + str(requestJson)  )
        result = await func(*args, **kwargs)  # 异步函数需要使用await
        end_time = time.time()

        logger.info(f"Function {func.__name__} took {end_time - start_time} seconds to complete.")
        return result

    return wrapper
