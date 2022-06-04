import io
import win32clipboard
from io import BytesIO
from PIL import Image
from SharedItem import SharedItem
from FlooPacket import FlooPacket


def copy_item_from_clipboard() -> SharedItem:
    item = None
    win32clipboard.OpenClipboard()
    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
        clip_image = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
        stream = io.BytesIO(clip_image)
        image = Image.open(stream)
        origin_width = image.width
        origin_height = image.height
        if origin_height > origin_width:
            ratio = 768 / origin_height
            share_image = image.resize([int(origin_width / ratio), int(origin_height / ratio)])
        else:
            ratio = 768 / origin_width
            share_image = image.resize([int(origin_width / ratio), int(origin_height / ratio)])
        output = BytesIO()
        share_image.convert("RGB").save(output, "JPEG", quality=40)
        item = SharedItem.create_valid_item(FlooPacket.TYP_IMG, output.getvalue())
        stream.close()
        output.close()
    elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
        clip_str = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        item = SharedItem.create_valid_item(FlooPacket.TYP_STR, clip_str.encode())
    win32clipboard.CloseClipboard()
    return item


def send_utf8bytes_str_to_clipboard(utf8bytes: bytes):
    send_to_clipboard(win32clipboard.CF_UNICODETEXT, utf8bytes.decode("utf-8"))


def send_jpeg_to_clipboard(jpeg_data: bytes):
    stream = io.BytesIO(jpeg_data)
    image = Image.open(stream)
    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    stream.close()
    send_to_clipboard(win32clipboard.CF_DIB, data)


def send_to_clipboard(clip_type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    # win32clipboard.SetClipboardText()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()
