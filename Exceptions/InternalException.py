from Decorators.LogDecorator import logger


class InternalException(Exception):
    """
        封装异常。为了能够在异常的时候提供更多的信息。所以尽量不要使用ROW EXCEPTION了。
    """
    position: str = None
    originalException = None

    def __init__(self, message, position: str, orginalException=None):
        super().__init__(message)
        self.position = position
        self.originalException = orginalException

    def __str__(self):
        name = self.__class__.__name__
        message = self.args[0]
        position = "position: " + str(self.position)
        originalException = "," + "originalException: " + str(self.originalException) if self.originalException else ""
        result = f"{name}: {message},{position}" + originalException
        logger.info("Exception:" + result)
        return result
