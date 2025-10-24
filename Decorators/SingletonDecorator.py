""" 装饰器实现单例模式 。想要彻底弄懂需要学习一下闭包和什么是python的可调用对象，cls在这里就是一个可调用对象。"""


class Singleton(type):
    """
    自定义的元类用于创建单例。
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # 如果实例不存在，创建并存储实例
            cls._instances[cls] = super().__call__(*args, **kwargs)
        # 返回类的唯一实例
        return cls._instances[cls]
