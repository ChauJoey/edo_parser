from abc import ABC, abstractmethod
from typing import Dict, List

class BaseStrategy(ABC):
    """所有船司解析策略的抽象基类"""

    name: str = "base"
    keywords: List[str] = []  # 策略关键字/别名

    @abstractmethod
    def match(self, text: str) -> bool:
        """判断该策略是否能处理当前文档"""
        raise NotImplementedError

    @abstractmethod
    def extract(self, text: str) -> List[Dict[str, str]]:
        """
        执行提取逻辑
        返回的每条记录应包含:
        {
            "柜号": str,
            "PIN": str,
            "还柜场": str
        }
        """
        raise NotImplementedError