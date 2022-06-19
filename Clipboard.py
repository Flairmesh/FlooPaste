import ctypes
import threading
import io
import validators
import webbrowser
import win32api, win32clipboard, win32con, win32gui
from io import BytesIO
from PIL import Image
from SharedItem import SharedItem
from FlooPacket import FlooPacket
import hashlib
import string
import random


class Clipboard:

    IMAGE_RESOLUTION = [512, 768, 1024]
    COMPRESS_QUALITY = [80, 80, 80]

    def __init__(self, delegate, img_opt):
        self.delegate = delegate
        self.imgOpt = img_opt
        self.lastHash = Clipboard.randomHash()
        # self.item = self.copy_item_from_clipboard()
        # delegate.newClipItem = self.item

    def setImageOpt(self, image_opt):
        self.imgOpt = image_opt

    def _create_window(self) -> int:
        """
        Create a window for listening to messages
        :return: window hwnd
        """
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._process_message
        wc.lpszClassName = self.__class__.__name__
        wc.hInstance = win32api.GetModuleHandle(None)
        class_atom = win32gui.RegisterClass(wc)
        return win32gui.CreateWindow(class_atom, self.__class__.__name__, 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None)

    def listen(self):
        def runner():
            hwnd = self._create_window()
            ctypes.windll.user32.AddClipboardFormatListener(hwnd)
            win32gui.PumpMessages()

        th = threading.Thread(target=runner, daemon=True)
        th.start()
        # while th.is_alive():
            # th.join(0.25)

    def _process_message(self, hwnd: int, msg: int, wparam: int, lparam: int):
        WM_CLIPBOARDUPDATE = 0x031D
        if msg == WM_CLIPBOARDUPDATE:
            self._process_clip()
        elif msg == win32con.WM_POWERBROADCAST:
            if wparam == win32con.PBT_APMSUSPEND:
                # print("Now sleep")
                self.delegate.setSleep(True)
            elif wparam == win32con.PBT_APMRESUMEAUTOMATIC:
                # print("Now resume")
                self.delegate.setSleep(False)
        return 0

    def _process_clip(self):
        item = self.copy_item_from_clipboard()
        if not item:
            return
        if item.hashValue != self.lastHash:
            self.delegate.newClipItem = item
            self.lastHash = item.hashValue

    @staticmethod
    def randomHash() -> bytes:
        letters = string.punctuation
        random_str = ''.join(random.choice(letters) for i in range(128))
        return hashlib.sha256(str.encode(random_str)).digest()

    def copy_item_from_clipboard(self) -> SharedItem:
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
                if max(origin_height, origin_width) > Clipboard.IMAGE_RESOLUTION[self.imgOpt]:
                    if origin_height > origin_width:
                        ratio = Clipboard.IMAGE_RESOLUTION[self.imgOpt] / origin_height
                        share_image = image.resize([int(origin_width * ratio), int(origin_height * ratio)])
                    else:
                        ratio = Clipboard.IMAGE_RESOLUTION[self.imgOpt] / origin_width
                        share_image = image.resize([int(origin_width * ratio), int(origin_height * ratio)])
                    # print("scaled image size", share_image.size)
                    share_image.convert("RGB").save(output, "JPEG", quality=Clipboard.COMPRESS_QUALITY[self.imgOpt])
                    item = SharedItem.create_valid_item(FlooPacket.TYP_IMG, output.getvalue(), hash_value)
                else:
                    image.convert("RGB").save(output, "JPEG", quality=Clipboard.COMPRESS_QUALITY[self.imgOpt])
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

    def send_utf8bytes_str_to_clipboard(self, utf8bytes: bytes, url_open: bool):
        decoded_str = utf8bytes.decode("utf-8")
        if url_open:
            valid = validators.url(decoded_str)
            if valid:
                webbrowser.open(decoded_str)
                return
        self.send_to_clipboard(win32clipboard.CF_UNICODETEXT, decoded_str)
        self.lastHash = hashlib.sha256(utf8bytes).digest()

    def send_jpeg_to_clipboard(self, jpeg_data: bytes):
        stream = io.BytesIO(jpeg_data)
        image = Image.open(stream)
        output = BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        stream.close()
        self.send_to_clipboard(win32clipboard.CF_DIB, data)
        self.lastHash = hashlib.sha256(data).digest()

    def send_to_clipboard(self, clip_type, data):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(clip_type, data)
        win32clipboard.CloseClipboard()
