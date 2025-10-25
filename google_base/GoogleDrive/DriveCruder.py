# drive_cruder.py
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from Exceptions.InternalException import InternalException
from google_base.GoogleDrive.DriveGateway import DriveGateway  # 按你的路径改 import


class DriveCruder:
    """
    在 DriveGateway 之上提供更顺手的组合/便捷方法；全部返回 dict，与上层 get() 兼容。
    """

    def __init__(self) -> None:
        self._gw = DriveGateway()

    # ---------- 读：列表、元信息 ----------

    def iter_files_in_folder(self, folder_or_id: str, *,
                             mime_type: Optional[str] = None,
                             page_size: int = 200,
                             fields: str = "files(id,name,mimeType,parents,webViewLink,createdTime,modifiedTime,driveId)") -> Iterable[Dict]:
        return self._gw.iter_in_folder(folder_or_id, mime_type=mime_type, page_size=page_size, fields=fields)

    def list_files_in_folder(self, folder_or_id: str, *,
                             mime_type: Optional[str] = None,
                             page_size: int = 200,
                             fields: str = "files(id,name,mimeType,parents,webViewLink,createdTime,modifiedTime,driveId)") -> List[Dict]:
        return self._gw.list_in_folder(folder_or_id, mime_type=mime_type, page_size=page_size, fields=fields)

    def get_file_meta(self, file_or_id: str, *,
                      fields: str = "id,name,mimeType,parents,webViewLink") -> Dict:
        return self._gw.get_meta(file_or_id, fields=fields)

    def get_file_parents(self, file_or_id: str) -> List[str]:
        return self._gw.get_parents(file_or_id)

    def is_folder(self, file_or_id: str) -> bool:
        return self._gw.is_folder(file_or_id)

    # ---------- 读：下载与链接 ----------

    def download_file_bytes(self, file_or_id: str) -> bytes:
        return self._gw.download_bytes(file_or_id)

    def get_web_view_link(self, file_or_id: str) -> str:
        meta = self._gw.get_meta(file_or_id, fields="id,webViewLink")
        return meta.get("webViewLink") or f"https://drive.google.com/file/d/{meta.get('id')}/view"

    # ---------- 写：移动 / 重命名 / 创建文件夹 ----------

    def move_file_to_folder(self, file_or_id: str, target_folder_or_id: str, *,
                            current_parent_or_id: Optional[str] = None) -> Dict:
        return self._gw.move_to_folder(file_or_id, target_folder_or_id, current_parent_or_id=current_parent_or_id)

    def rename_file(self, file_or_id: str, new_name: str) -> Dict:
        return self._gw.rename(file_or_id, new_name)

    def ensure_folder(self, name: str, *, parent_folder_or_id: Optional[str] = None) -> Dict:
        return self._gw.ensure_folder(name, parent_folder_or_id=parent_folder_or_id)

    # ---------- 批量小工具 ----------

    def move_all_pdfs(self, from_folder_or_id: str, to_folder_or_id: str) -> int:
        moved = 0
        for f in self._gw.iter_in_folder(from_folder_or_id, mime_type="application/pdf"):
            try:
                self._gw.move_to_folder(f.get("id"), to_folder_or_id, current_parent_or_id=from_folder_or_id)
                moved += 1
            except InternalException as e:
                print(f"[WARN] 移动失败: {f.get('name')} ({f.get('id')}): {e}")
        return moved


    def upload_file(self, file_path: str, *, name: Optional[str] = None,
                    parent_folder_or_id: Optional[str] = None,
                    mime_type: str = "application/pdf") -> Dict:
        return self._gw.upload_file(
            file_path,
            name=name,
            parent_folder_or_id=parent_folder_or_id,
            mime_type=mime_type,
        )
