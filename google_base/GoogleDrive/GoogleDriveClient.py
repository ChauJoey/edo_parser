import re
from oauth2client.service_account import ServiceAccountCredentials
from Decorators.SingletonDecorator import Singleton
from google_base.GoogleConfig import GoogleConfig
from Exceptions.InternalException import InternalException
from typing import List, Dict, Optional
from googleapiclient.discovery import build

class GoogleDriveClient(metaclass=Singleton):
    """
    GoogleDriveClient
    -----------------
    用于建立与 Google Drive 的连接（全局单例模式）。
    职责：
      1. 完成 Google Drive API 的身份验证。
      2. 建立 v3 service 客户端以支持文件操作。
      3. 提供 getClient()、getAuthorization() 接口供上层调用。
      4. 后续扩展将包含列出、移动、下载文件等操作。

    设计说明：
      - 与 GoogleSheetClient 保持一致的接口风格。
      - 使用 SingletonDecorator 确保全局唯一实例。
      - 所有 API 操作都基于 Drive 文件夹 ID。
    """

    _singletonCreated: bool = False  # 标志是否已创建过单例实例。

    def __init__(self):
        """
        初始化 GoogleDriveClient。
        从 GoogleConfig 获取凭证配置，并初始化 service、authorization 占位符。
        """
        if not self._singletonCreated:
            # 读取全局配置（包含 JSON 凭证路径、Scope、文件夹 ID 等）
            self._config: GoogleConfig = GoogleConfig.getGlobalGoogleConfig()

            # Drive v3 客户端对象，在首次连接后创建
            self._service = None

            # 授权凭证对象（ServiceAccountCredentials）
            self._authorization = None

            # 标志单例实例已创建
            self._singletonCreated = True

    def _createCredentials(self):
        """
        内部方法：创建 Google Drive 凭证连接。
        从 JSON 文件加载 Service Account 凭证，并构建 Drive API v3 客户端。

        若认证或连接失败，将抛出自定义 InternalException。
        """
        try:
            print("Google Drive 开始认证。")
            credential = ServiceAccountCredentials.from_json_keyfile_name(
                self._config.getJsonConfigFilePath(),
                self._config.getScope()
            )

            # 保存凭证与服务实例
            self._authorization = credential
            self._service = build('drive', 'v3', credentials=self._authorization)

        except Exception as e:
            raise InternalException(
                "连接 Google Drive 错误。",
                "GoogleDriveClient:_createCredentials",
                e
            )

    def getClient(self):
        """
        获取 Google Drive v3 客户端。
        若尚未初始化（_service 为 None），则自动触发认证流程。
        """
        if self._service is None:
            self._createCredentials()
        return self._service

    def getAuthorization(self):
        """
        获取授权凭证对象（ServiceAccountCredentials）。
        """
        return self._authorization

    @classmethod
    def getDriveClient(cls):
        """
        返回全局唯一的 GoogleDriveClient 实例。
        若未完成认证，将自动执行 _createCredentials()。
        """
        inst = cls()
        if inst.getAuthorization() is None:
            inst._createCredentials()
        return inst



if __name__ == "__main__":
    pass