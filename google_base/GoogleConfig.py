import os
from Decorators.SingletonDecorator import Singleton


class GoogleConfig(metaclass=Singleton):
    """
    GoogleConfig 用于集中管理与 Google 相关的配置，包括：
      - Service Account JSON 凭证路径
      - 授权作用域 Scope
      - Google Sheet 工作簿 URL
      - 三个 EDO 文件夹 URL（Input / Output / Fail）

    本类采用单例模式（Singleton），确保全局只存在一个实例。
    """

    _jsonConfigFilePath: str = None
    _scope: list = None
    _remark: str = None
    _workBookUrl: str = None

    # 这是一种编程风格。属性前面加上_下划线来标识这个属性是一个私有的属性。最好不要随意修改。如果需要修改，请使用特定的方法。
    def __init__(self):
        """
        初始化配置项。
        若后续有需要，可以继承此类并覆盖这些默认配置。
        """
        # 凭证文件路径
        self._jsonConfigFilePath = GoogleConfig._getGlobalJsonConfigFilePath()

        # Google API 授权范围
        self._scope = GoogleConfig._getScope()

        # 标识信息
        self._remark = "全局的唯一实例"

        # Google Sheet 工作簿 URL
        self._workBookUrl = ('https://docs.google.com/spreadsheets/d/1nZ8_RLmKoAQNhreIVq7WRHMlVPua-ty6zpZP5mTYbNM/edit#gid=1676080520')

        # ✅ 仅存放【文件夹ID】（不再保存 URL）
        self._edoInputId = "1z5R4Xi_APdDedu1UleSCf_Ml_bqniaF1"
        self._edoOutputId = "1timca5IO47csu_49pwJY3j0ECTBLatUB"
        self._edoFailId = "1-0qpp79kb4OeckZOymBKf9Yeo2z0_Y7d"


    """
    以下是get方法，符合面向对象的编程风格。对象->方法。最好不要直接访问这些配置，并且尽量少修改。已经加了_下划线强调的属性是最好不要修改的属性。
    这里有一个set方法。
    。因为其他属性在初始化时候就已经set了。这个除外，所以就单独设置了set方法。
    为什么不用实例.属性的方式给实例的属性赋值是因为编程风格统一一下比较好。
    """

    def getJsonConfigFilePath(self):
        """返回 Service Account JSON 凭证路径"""
        return self._jsonConfigFilePath

    def setJsonConfigFilePath(self, path):
        """动态修改 JSON 凭证路径"""
        self._jsonConfigFilePath = path

    def getScope(self):
        """返回授权作用域"""
        return self._scope

    def getRemark(self):
        """返回备注信息"""
        return self._remark

    def getWorkBookUrl(self):
        """返回 Google Sheet 工作簿 URL"""
        return self._workBookUrl

    def getEdoInputId(self):
        return self._edoInputId

    def getEdoOutputId(self):
        return self._edoOutputId

    def getEdoFailId(self):
        return self._edoFailId

    def __str__(self):
        """打印当前配置摘要"""
        return 'JsonConfigFilePath:' + self.getJsonConfigFilePath() + '\n' + "Scope:" + "\t".join(
            self.getScope()) + "\nRemark:" + self.getRemark()

    # ---------- 工厂与内部方法 ----------

    @classmethod
    def getGlobalGoogleConfig(cls):
        """返回全局唯一实例"""
        return cls()

    # 这两个方法双下划线不能被其他模块引用。这是一种约定。
    @staticmethod
    def _getGlobalJsonConfigFilePath():
        """
                计算 JSON 凭证文件的绝对路径。
                通过当前脚本路径 + 相对路径的方式定位。
                """
        current_script_path = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.join('..', 'Jsons', 'vic-depot-95801651e707.json')
        json_file_path = os.path.abspath(os.path.join(current_script_path, relative_path))
        return json_file_path

    @staticmethod
    def _getScope() -> list:
        """
                返回默认的 Google API 授权作用域。
                如需最小化权限，可视需求精简。
                """
        return ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

# ---------- 测试区域 ----------
if __name__ == '__main__':
    cfg = GoogleConfig.getGlobalGoogleConfig()
    print("EDO Input  ID:", cfg.getEdoInputId())
    print("EDO Output ID:", cfg.getEdoOutputId())
    print("EDO Fail   ID:", cfg.getEdoFailId())
