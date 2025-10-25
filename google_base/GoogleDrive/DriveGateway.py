# drive_gateway.py
from __future__ import annotations

import io
import os
import re
from typing import Dict, Iterable, List, Optional

try:
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "googleapiclient is missing. Install it via `pip install google-api-python-client`."
    ) from exc

from Exceptions.InternalException import InternalException
from google_base.GoogleDrive.GoogleDriveClient import GoogleDriveClient


class DriveGateway:
    """
    最小封装：只做 Drive API 调用，返回 dict（与 Google API 原样兼容）。
    不含业务语义；输入支持 URL/ID（内部统一解析为 ID）。
    """

    def __init__(self) -> None:
        self._svc = GoogleDriveClient.getDriveClient().getClient()

    # ---------- 工具 ----------

    @staticmethod
    def _extract_id(url_or_id: str) -> str:
        if not url_or_id:
            raise InternalException("url_or_id 不能为空。", "DriveGateway:_extract_id")
        if "http" not in url_or_id and "/" not in url_or_id:
            return url_or_id.strip()

        m = re.search(r"/(?:folders|file/d)/([a-zA-Z0-9\-_]+)", url_or_id)
        if m:
            return m.group(1)

        tail = url_or_id.rstrip("/").split("/")[-1]
        if tail:
            return tail

        raise InternalException("无法解析 ID，请检查 URL。", "DriveGateway:_extract_id")

    # ---------- 读取 ----------

    def get_meta(self, file_or_id: str, *,
                 fields: str = "id,name,mimeType,parents,webViewLink,createdTime,modifiedTime,driveId") -> Dict:
        fid = self._extract_id(file_or_id)
        try:
            return self._svc.files().get(
                fileId=fid,
                fields=fields,
                supportsAllDrives=True
            ).execute()
        except Exception as e:
            raise InternalException("获取元信息失败。", "DriveGateway:get_meta", e)

    def get_parents(self, file_or_id: str) -> List[str]:
        meta = self.get_meta(file_or_id, fields="id,parents")
        return meta.get("parents") or []

    def is_folder(self, file_or_id: str) -> bool:
        meta = self.get_meta(file_or_id, fields="id,mimeType")
        return meta.get("mimeType") == "application/vnd.google-apps.folder"

    def find_by_name(self, name: str, *,
                     in_folder: Optional[str] = None,
                     mime_type: Optional[str] = None,
                     fields: str = "files(id,name,mimeType,parents,webViewLink,createdTime,modifiedTime,driveId)") -> List[Dict]:
        if not name:
            return []
        parts = [f"name = '{name}'", "trashed = false"]
        if in_folder:
            parts.append(f"'{self._extract_id(in_folder)}' in parents")
        if mime_type:
            parts.append(f"mimeType = '{mime_type}'")
        q = " and ".join(parts)

        try:
            resp = self._svc.files().list(
                q=q,
                spaces="drive",
                fields=fields,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora="allDrives"
            ).execute()
            return resp.get("files", [])
        except Exception as e:
            raise InternalException("按名称查询失败。", "DriveGateway:find_by_name", e)

    def iter_in_folder(self, folder_or_id: str, *,
                       mime_type: Optional[str] = None,
                       page_size: int = 200,
                       fields: str = "files(id,name,mimeType,parents,webViewLink,createdTime,modifiedTime,driveId)") -> Iterable[Dict]:
        folder_id = self._extract_id(folder_or_id)
        parts = [f"'{folder_id}' in parents", "trashed = false"]
        if mime_type:
            parts.append(f"mimeType = '{mime_type}'")
        q = " and ".join(parts)
        list_fields = f"nextPageToken,{fields}"
        token = None
        try:
            while True:
                resp = self._svc.files().list(
                    q=q,
                    spaces="drive",
                    fields=list_fields,
                    pageSize=page_size,
                    pageToken=token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    corpora="allDrives"
                ).execute()
                for f in resp.get("files", []):
                    yield f
                token = resp.get("nextPageToken")
                if not token:
                    break
        except Exception as e:
            raise InternalException("列出文件失败。", "DriveGateway:iter_in_folder", e)

    def list_in_folder(self, folder_or_id: str, *,
                       mime_type: Optional[str] = None,
                       page_size: int = 200,
                       fields: str = "files(id,name,mimeType,parents,webViewLink,createdTime,modifiedTime,driveId)") -> List[Dict]:
        return list(self.iter_in_folder(folder_or_id, mime_type=mime_type, page_size=page_size, fields=fields))

    def download_bytes(self, file_or_id: str) -> bytes:
        fid = self._extract_id(file_or_id)
        try:
            request = self._svc.files().get_media(fileId=fid)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buf.getvalue()
        except Exception as e:
            raise InternalException("下载失败。", "DriveGateway:download_bytes", e)

    # ---------- 写 ----------


    def upload_file(self, file_path: str, *, name: Optional[str] = None,
                    parent_folder_or_id: Optional[str] = None,
                    mime_type: str = "application/pdf") -> Dict:
        target_name = name or os.path.basename(file_path)
        body: Dict = {"name": target_name}
        if parent_folder_or_id:
            body["parents"] = [self._extract_id(parent_folder_or_id)]
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=False)
        try:
            return self._svc.files().create(
                body=body,
                media_body=media,
                fields="id,name,mimeType,parents,webViewLink",
                supportsAllDrives=True
            ).execute()
        except Exception as e:
            raise InternalException("Failed to upload file to Google Drive.", "DriveGateway:upload_file", e)

    def move_to_folder(self, file_or_id: str, target_folder_or_id: str, *,
                       current_parent_or_id: Optional[str] = None) -> Dict:
        file_id = self._extract_id(file_or_id)
        target_id = self._extract_id(target_folder_or_id)
        try:
            if current_parent_or_id is None:
                parents = self.get_parents(file_id)
                if not parents:
                    raise InternalException("无法确定当前父级（parents 为空）。", "DriveGateway:move_to_folder")
                current_parent_or_id = parents[0]
            else:
                current_parent_or_id = self._extract_id(current_parent_or_id)

            if current_parent_or_id == target_id:
                return self.get_meta(file_id, fields="id,name,parents")

            return self._svc.files().update(
                fileId=file_id,
                addParents=target_id,
                removeParents=current_parent_or_id,
                fields="id,name,parents",
                supportsAllDrives=True
            ).execute()
        except Exception as e:
            raise InternalException("移动失败。", "DriveGateway:move_to_folder", e)

    def rename(self, file_or_id: str, new_name: str) -> Dict:
        if not new_name:
            raise InternalException("new_name 不能为空。", "DriveGateway:rename")
        fid = self._extract_id(file_or_id)
        try:
            return self._svc.files().update(
                fileId=fid,
                body={"name": new_name},
                fields="id,name,parents",
                supportsAllDrives=True
            ).execute()
        except Exception as e:
            raise InternalException("重命名失败。", "DriveGateway:rename", e)

    def ensure_folder(self, name: str, *, parent_folder_or_id: Optional[str] = None) -> Dict:
        if not name:
            raise InternalException("name 不能为空。", "DriveGateway:ensure_folder")

        parent_id = self._extract_id(parent_folder_or_id) if parent_folder_or_id else None
        exist = self.find_by_name(
            name=name,
            in_folder=parent_id,
            mime_type="application/vnd.google-apps.folder",
            fields="files(id,name,mimeType,parents,webViewLink)"
        )
        if exist:
            return exist[0]

        body: Dict = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            body["parents"] = [parent_id]

        try:
            return self._svc.files().create(
                body=body,
                fields="id,name,mimeType,parents,webViewLink",
                supportsAllDrives=True
            ).execute()
        except Exception as e:
            raise InternalException("创建文件夹失败。", "DriveGateway:ensure_folder", e)
