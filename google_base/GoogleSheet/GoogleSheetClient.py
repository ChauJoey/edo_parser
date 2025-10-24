import gspread
from gspread import Spreadsheet, Client, Worksheet
from oauth2client.service_account import ServiceAccountCredentials
from Decorators.SingletonDecorator import Singleton
from google_base.GoogleConfig import GoogleConfig
from Exceptions.InternalException import InternalException



class GoogleSheetClient(metaclass=Singleton):
    """
    应该作为全局唯一的与google sheets的接入点。
    """
    _singletonCreated: bool = False  # 不要自行修改这个属性。

    def __init__(self):
        if not self._singletonCreated:
            self._config: GoogleConfig = GoogleConfig.getGlobalGoogleConfig()  # 决定了如何连接。这个配置应该是从静态文件中解析的。
            self._client: Spreadsheet = None
            self._authorization: Client = None
            self._singletonCreated = True

    def _createCredentials(self):
        # 这个方法已经完成了通信建立。根据自身凭证和GOOGLE连接。
        try:
            print("谷歌开始认证。")
            credential = ServiceAccountCredentials.from_json_keyfile_name(self._config.getJsonConfigFilePath(),
                                                                          self._config.getScope())
            self._authorization = gspread.authorize(credential)
            self._client: Spreadsheet = self._authorization.open_by_url(self._config.getWorkBookUrl())
        except Exception as e:
            raise InternalException("连接谷歌错误。", "GoogleSheetClient:_createCredentials", e)

    def getClient(self) -> Spreadsheet:
        return self._client

    def getAuthorization(self):
        return self._authorization

    @classmethod
    def getGlobalGoogleSheetClient(cls):
        GlobalGoogleSheetClient = cls()
        if GlobalGoogleSheetClient.getAuthorization() is None:
            GlobalGoogleSheetClient._createCredentials()
        return GlobalGoogleSheetClient

    @staticmethod
    def getWorkSheet(sheetName='') -> Worksheet:
        if not sheetName:
            raise InternalException("sheetName为空", "GoogleSheetClient:getWorkSheet")
        GlobalGoogleSheetClient = GoogleSheetClient.getGlobalGoogleSheetClient()
        try:
            print(f"开始获取表格数据: {sheetName}")
            return GlobalGoogleSheetClient.getClient().worksheet(sheetName)
        except Exception as e:
            max_retry = 3
            retried = 1
            while retried < max_retry:
                print(f"获取表格数据重试{retried}次,重新和谷歌认证连接。")
                retried += 1
                GlobalGoogleSheetClient._createCredentials()
                return GlobalGoogleSheetClient.getClient().worksheet(sheetName)

            raise InternalException("获取特定表格错误。", "GoogleSheetClient:getWorkSheet", e)

    @staticmethod
    def getSheets(sheetNames=[]) -> []:
        if sheetNames:
            result = []
            for sheetName in sheetNames:
                workSheet = GoogleSheetClient.getWorkSheet(sheetName)
                result.append(workSheet)
            return result

    @staticmethod
    def getSyncWorker(sourceSheetName: str, targetSheetNames: list):
        pass
        return


# ---------- 自测 ----------
if __name__ == "__main__":
    pass