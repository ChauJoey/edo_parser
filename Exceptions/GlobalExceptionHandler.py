import traceback

from Response import Response
from quart import request
import logging

logger = logging.getLogger('quart.app')


async def globalExceptionHandler(e):
    # 自定义全局错误响应
    stack_trace = traceback.format_exc()  # 获取完整的调用堆栈信息
    logger.error(f"Exception occurred: {e}\nStack trace:\n{stack_trace}")
    return Response.error(message={"exception": str(e)})
