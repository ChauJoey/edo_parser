# run_drive_preview.py
from google_base.GoogleDrive.DriveApp import DriveApp
from reader.pdf_reader import PDFReader

if __name__ == "__main__":
    app = DriveApp()
    reader = PDFReader()

    items = app.list_input_files()
    if not items:
        print("❌ Input 文件夹里没有 PDF。")
        raise SystemExit(0)

    test_file = items[0]
    print(f"✅ 测试文件: {test_file.name} ({test_file.id})")

    data = app.download_file_bytes(test_file.id)
    print(f"📦 已下载 {len(data)} 字节")

    # 使用你现有的 PDFReader 来读 bytes（我给你加了这个方法的测试版本如下）
    # 如果你的 PDFReader 还没有 read_bytes，请把下面的类方法加进 pdf_reader.py 里
    try:
        text = reader.read_bytes(data)  # 见下方“给 PDFReader 增加 read_bytes”
    except AttributeError:
        print("你的 PDFReader 还没有 read_bytes()，请按注释添加~")
        raise

    print("─────────────── PDF 内容预览 ───────────────")
    print(text[:1000])  # 只展示前 1000 字符
    print("──────────────────────────────────────────")

    link = app.get_preview_link(test_file.id)
    print(f"🌐 预览链接: {link}")
