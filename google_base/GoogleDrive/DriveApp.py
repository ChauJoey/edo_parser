from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Iterator, Tuple

from google_base.GoogleConfig import GoogleConfig
from google_base.GoogleDrive.DriveCruder import DriveCruder


# ─────────────────────────────────────────────────────────────────────────────
# DriveApp
# 面向 Workflow 的“最小应用层”封装：
# - 聚焦 EDO 三个固定目录（Input / Output / Fail）的常用操作；
# - 对上只暴露稳定的小接口，让 Workflow 无需关心底层 Drive API；
# - 不承载复杂业务规则（重命名策略/解析策略等仍由上层决定）。
# 典型用法：
#   app = DriveApp()
#   for f, data in app.iter_input_pdf_bytes():
#       # 1) 用 data 做识别/解析
#       # 2) 根据结果决定 app.move_to_output(...) / app.move_to_fail(...)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DriveFile:
    """
    轻量文件模型，供 Workflow 层直接使用。

    Attributes:
        id:       Drive 文件 ID。
        name:     文件名。
        mimeType: MIME 类型（如 "application/pdf"）。
        createdTime: 创建时间（ISO 字符串，原样透传 Drive）。
        parents:  父级文件夹 ID 列表（通常仅 1 个）。
    """
    id: str
    name: str
    mimeType: Optional[str] = None
    createdTime: Optional[str] = None
    parents: Optional[List[str]] = None


class DriveApp:
    """
    面向 Workflow 的最小 Drive 应用层（EDO 项目约定版本）。

    设计目标
    --------
    - “好用且克制”：只提供 Workflow 真正需要的最小方法集；
    - “稳定语义”：不把业务规则写死在这里（例如命名策略、解析逻辑）；
    - “目录内聚”：只服务于固定的 EDO 目录（Input/Output/Fail）。

    提供能力（仅 4+2 个）
    ---------------------
    1) list_input_files()          列出 Input 目录全部文件（默认只取 PDF）
    2) get_file_id_by_name()       在 Input 目录按名字取 fileId
    3) move_to_output()            从 Input 移动到 Output（可选改名）
    4) move_to_fail()              从 Input 移动到 Fail（可选改名）
    5) download_file_bytes()       下载文件为内存 bytes（供 Reader 使用）
    6) iter_input_pdf_bytes()      直接遍历 Input PDF，返回 (DriveFile, bytes)

    说明
    ----
    - 本类不做权限兜底；请确保服务账号对三个目录（最好是同一 Shared Drive 下）
      具备 Content manager 及以上权限。
    - 移动操作使用“只保留目标父级”的语义，避免出现“父级数量增加”的 403 错误。
    """

    def __init__(self) -> None:
        """
        初始化并绑定 EDO 三个目录的 ID。
        目录 ID 来源：GoogleConfig（建议配置为固定的文件夹 ID）。
        """
        self._cfg = GoogleConfig.getGlobalGoogleConfig()
        self._drv = DriveCruder()
        self._input_id = self._cfg.getEdoInputId()
        self._output_id = self._cfg.getEdoOutputId()
        self._fail_id = self._cfg.getEdoFailId()

    # ───────────────── 查询/读取 ─────────────────

    def list_input_files(self, *, mime_type: Optional[str] = "application/pdf") -> List[DriveFile]:
        """
        列出 EDO Input 文件夹内的所有文件（默认仅 PDF）。

        Args:
            mime_type: 可选 MIME 过滤；默认 "application/pdf"。传 None 表示不过滤。

        Returns:
            文件列表（DriveFile），字段为常用轻量视图。
        """
        files: List[Dict] = self._drv.list_files_in_folder(self._input_id, mime_type=mime_type)
        return [
            DriveFile(
                id=f.get("id"),
                name=f.get("name", ""),
                mimeType=f.get("mimeType"),
                createdTime=f.get("createdTime"),
                parents=f.get("parents"),
            )
            for f in files
        ]

    def get_file_id_by_name(self, name: str, *, mime_type: Optional[str] = None) -> Optional[str]:
        """
        在 EDO Input 目录中按文件名查找并返回 fileId。

        约定：
            - 精确匹配；如有重名，返回第一个匹配项；
            - 未找到返回 None。

        Args:
            name: 文件名（不含路径）。
            mime_type: 可选 MIME 过滤；默认不过滤。

        Returns:
            文件 ID 或 None。
        """
        for f in self._drv.iter_files_in_folder(self._input_id, mime_type=mime_type):
            if f.get("name") == name:
                return f.get("id")
        return None

    def download_file_bytes(self, file_id: str) -> bytes:
        """
        下载 Drive 文件到内存（bytes），通常交给 PDF Reader 的 read_bytes 使用。

        Args:
            file_id: Drive 文件 ID。

        Returns:
            文件原始字节流。
        """
        return self._drv.download_file_bytes(file_id)

    def iter_input_pdf_bytes(self) -> Iterator[Tuple[DriveFile, bytes]]:
        """
        便利器：遍历 Input 目录下的 PDF，逐个返回 (DriveFile, bytes)。

        用途：
            在一个循环里完成“读取 → 解析 → 决策移动”，避免中间落盘。

        Yields:
            (DriveFile, data) 二元组，其中 data 为文件字节流。
        """
        for f in self.list_input_files(mime_type="application/pdf"):
            data = self.download_file_bytes(f.id)
            yield f, data

    # ───────────────── 变更（移动/改名） ─────────────────

    def move_to_output(self, file_id: str, *, rename_to: Optional[str] = None) -> None:
        """
        将文件从 Input 移动到 Output，必要时先重命名。

        语义：
            - 若传入 rename_to，则先改名再移动；
            - 采用“只保留目标父级”的移动方式，避免 403（父级数量增加）错误。

        Args:
            file_id: 待移动文件的 Drive ID。
            rename_to: 可选；新文件名。
        """
        if rename_to:
            self._drv.rename_file(file_or_id=file_id, new_name=rename_to)
        self._drv.move_file_to_folder(
            file_or_id=file_id,
            target_folder_or_id=self._output_id,
        )

    def move_to_fail(self, file_id: str, *, rename_to: Optional[str] = None) -> None:
        """
        将文件从 Input 移动到 Fail，必要时先重命名。

        语义与 move_to_output 相同。

        Args:
            file_id: 待移动文件的 Drive ID。
            rename_to: 可选；新文件名（例如添加 "[FAIL]" 前缀等）。
        """
        if rename_to:
            self._drv.rename_file(file_or_id=file_id, new_name=rename_to)
        self._drv.move_file_to_folder(
            file_or_id=file_id,
            target_folder_or_id=self._fail_id,
        )

    def get_preview_link(self, file_id: str) -> str:
        """
        获取文件的 web 预览链接（webViewLink）。

        说明：
            - 若 Drive 未返回 webViewLink，则按固定模板拼接 URL。

        Args:
            file_id: Drive 文件 ID。

        Returns:
            可直接在浏览器打开的预览链接。
        """
        return self._drv.get_web_view_link(file_id)


# ─────────────────────────── 轻量自测（谨慎运行） ───────────────────────────
if __name__ == "__main__":
    app = DriveApp()

    # 1) 列出 Input PDF
    items = app.list_input_files()
    print(f"[Input PDFs] {len(items)} file(s)")
    for i, f in enumerate(items[:10], start=1):
        print(f"  {i:>2}. {f.name}  ({f.id})")

    if items:
        test = items[0]
        # 2) 预览链接
        link = app.get_preview_link(test.id)
        print("Preview:", link)

        # 3) 演示移动（注意：会真实移动文件；仅在测试环境执行）
        app.move_to_fail(test.id, rename_to=f"[FAIL]{test.name}")
        print("Moved to Fail.")
        app.move_to_output(test.id, rename_to=test.name.replace("[FAIL]", ""))
        print("Moved back to Output (from Input).")
