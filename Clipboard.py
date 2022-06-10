import io
import validators
import webbrowser
import win32api
import win32clipboard
from io import BytesIO
from PIL import Image
from SharedItem import SharedItem
from FlooPacket import FlooPacket
import hashlib
import string
import random

IMAGE_RESOLUTION = [512, 768, 1024]
COMPRESS_QUALITY = [80, 80, 80]


def randomHash() -> bytes:
    letters = string.punctuation
    random_str = ''.join(random.choice(letters) for i in range(128))
    return hashlib.sha256(str.encode(random_str)).digest()


def copy_item_from_clipboard(imgOpt: int) -> SharedItem:
    item = None
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            clip_image = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            win32clipboard.CloseClipboard()
            stream = io.BytesIO(clip_image)
            image = Image.open(stream)
            hash_value = hashlib.sha256(clip_image[0:-1]).digest()
            # print("clipboard image hash first 20", clip_image[-20:], "size", len(clip_image))
            origin_width = image.width
            origin_height = image.height
            output = BytesIO()
            if max(origin_height, origin_width) > IMAGE_RESOLUTION[imgOpt]:
                if origin_height > origin_width:
                    ratio = IMAGE_RESOLUTION[imgOpt] / origin_height
                    share_image = image.resize([int(origin_width * ratio), int(origin_height * ratio)])
                else:
                    ratio = IMAGE_RESOLUTION[imgOpt] / origin_width
                    share_image = image.resize([int(origin_width * ratio), int(origin_height * ratio)])
                # print("scaled image size", share_image.size)
                share_image.convert("RGB").save(output, "JPEG", quality=COMPRESS_QUALITY[imgOpt])
                item = SharedItem.create_valid_item(FlooPacket.TYP_IMG, output.getvalue(), hash_value)
            else:
                image.convert("RGB").save(output, "JPEG", quality=COMPRESS_QUALITY[imgOpt])
                item = SharedItem.create_valid_item(FlooPacket.TYP_IMG, output.getvalue(), hash_value)
            stream.close()
            output.close()
        elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            clip_str = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            utf8_bytes = clip_str.encode()
            hash_value = hashlib.sha256(utf8_bytes).digest()
            item = SharedItem.create_valid_item(FlooPacket.TYP_STR, utf8_bytes, hash_value)
        else:
            win32clipboard.CloseClipboard()
    except win32api.error:
        return None
    return item


def send_utf8bytes_str_to_clipboard(utf8bytes: bytes, url_open: bool):
    decoded_str = utf8bytes.decode("utf-8")
    if url_open:
        valid = validators.url(decoded_str)
        if valid:
            webbrowser.open(decoded_str)
            return hashlib.sha256(utf8bytes).digest()
    send_to_clipboard(win32clipboard.CF_UNICODETEXT, decoded_str)
    return hashlib.sha256(utf8bytes).digest()


def send_jpeg_to_clipboard(jpeg_data: bytes):
    stream = io.BytesIO(jpeg_data)
    image = Image.open(stream)
    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    stream.close()
    send_to_clipboard(win32clipboard.CF_DIB, data)
    hash_value = hashlib.sha256(data).digest()
    # print("send image to clip with first ", data[-20:], "len", len(data))
    return hash_value


def send_to_clipboard(clip_type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    # win32clipboard.SetClipboardText()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()
