from threading import *
import time, os, sys
from Clipboard import Clipboard
import serial
import serial.tools.list_ports
from RwcpSegment import RwcpSegment
from RwcpClient import RwcpClient
from FlooPacket import FlooPacket
from FlooPacketParser import FlooPacketParser
# from plyer import notification
from notifypy import Notify


class FlooTransceiver(Thread):
    """FlooGoo data interface on USB COM"""

    PORT_OPENED = 0
    PORT_CLOSED = 1
    NOTIFICATION_TIMEOUT = 400

    def __init__(self, url_opt, image_opt, share_to_mobile, notif_on_image):
        super(FlooTransceiver, self).__init__()
        self.isSleep = False
        self.port_name = None
        self.port_opened = False
        self.port = None
        self.sending = False
        self.rwcpClient = RwcpClient(self)
        self.clipObject = None
        self.flooParser = FlooPacketParser()
        self.notified = None
        self.notifiedCounter = 0
        # self.lastClipItemHash = None
        self.newClipItem = None
        self.autoUrl = url_opt
        self.imageOpt = image_opt
        self.shareToMobile = share_to_mobile
        self.notifOnImage = notif_on_image
        self.clipboard = Clipboard(self, self.imageOpt)
        self.clipboard.listen()

    def setImageOpt(self, image_opt):
        self.imageOpt = image_opt
        self.clipboard.setImageOpt(image_opt)

    def setAutoUrl(self, auto_url):
        self.autoUrl = auto_url

    def setShareToMobile(self, share_to_mobile):
        self.shareToMobile = share_to_mobile

    def setNotifOnImage(self, notif_on_image):
        self.notifOnImage = notif_on_image

    def setSleep(self, flag):
        self.isSleep = flag

    def reset(self):
        # print("port now reset")
        if self.port_opened:
            self.port.close()
        self.port_name = None
        self.port_opened = False
        self.port = None
        self.sending = False

    def monitor_port(self) -> bool:
        if self.isSleep:

            return False

        ports = [port.name for port in serial.tools.list_ports.grep('0A12:4007.*FMA100')]
        if ports:
            if not self.port_opened:
                self.port_name = ports[0]
                # print("current port ", self.port_name, " state: ", self.port_opened)
                try:
                    # print("try open")
                    self.port = serial.Serial(port=self.port_name, baudrate=921600,
                                              bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
                    # self.port.open()
                    self.port_opened = self.port.is_open
                    return self.port_opened
                    # print("Change port state: ", self.port_opened)
                except Exception as exec0:
                    print(exec0)
                    return False
        else:
            if self.port_opened:
                self.port.close()
                self.reset()
        return False

    def heartBeat(self):
        if self.port is not None and self.port.is_open:
            if not self.sending:
                # print("Send heart beats ...")
                gap_seg = RwcpSegment.create_valid_segment(RwcpSegment.HEADER_OPCODE_GAP, 0)
                self.port.write(gap_seg.bytes)
            return self.port_name
        else:
            return None

        # A valid COM port name reported to the caller indicates transceiver is working
        return self.port_name

    def run(self):
        while True:
            if self.monitor_port():
                heart_beat_counter = 0
                while self.port is not None and self.port.is_open and not self.isSleep:
                    # print("monitoring rx ... ")
                    try:
                        if self.port.inWaiting() > 0:
                            if self.sending:
                                # Rwcp ack
                                # print("Rwcp Ack")
                                self.rwcpClient.processReceivedData(self.port.read(self.port.inWaiting()))
                            else:
                                parsed_items = self.flooParser.run(self.port.read(self.port.inWaiting()))
                                if parsed_items is not None and len(parsed_items) > 0:
                                    last_item = parsed_items[-1]
                                    if last_item.type == FlooPacket.TYP_STR:
                                        self.clipboard.send_utf8bytes_str_to_clipboard(last_item.bytes,
                                                                                       self.autoUrl)
                                        self.notified = FlooPacket.TYP_STR
                                        self.notifiedCounter = FlooTransceiver.NOTIFICATION_TIMEOUT
                                    elif last_item.type == FlooPacket.TYP_IMG:
                                        self.clipboard.send_jpeg_to_clipboard(last_item.bytes)
                                        self.notified = FlooPacket.TYP_IMG
                                        self.notifiedCounter = FlooTransceiver.NOTIFICATION_TIMEOUT
                                        if self.notifOnImage is not None:
                                            notif = Notify()
                                            notif.application_name = "FlooPaste"
                                            notif.title = "FlooPaste"
                                            file_path = os.path.abspath(os.path.dirname(sys.argv[0]))
                                            notif.icon = file_path + '\FlooPasteNotif.ico'
                                            notif.message = self.notifOnImage
                                            notif.send(block=False)
                        # print("serial idle")
                        if self.notified is not None:
                            self.notifiedCounter -= 1
                            if self.notifiedCounter == 0:
                                self.notified = None
                        if self.shareToMobile:
                            if self.newClipItem is not None and self.flooParser.state == FlooPacketParser.HEAD:
                                print("Send new clipboard item ")
                                floo_pkt = FlooPacket.create_valid_packet(self.newClipItem.type, self.newClipItem.bytes)
                                self.newClipItem = None
                                self.rwcpClient.sendData(floo_pkt.bytes, 255)
                                self.sending = True
                        if not self.sending:
                            # print("Idle heart beating")
                            self.heartBeat()
                    except Exception as exec0:
                        print(exec0)
                        self.reset()
                    time.sleep(0.01)
            self.reset()
            time.sleep(1)  # check port after 1 second

    def sendSegment(self, segment):
        if self.port.is_open:
            # print("port out", segment.bytes)
            self.port.write(segment.bytes)

    def didMakeProgress(self, progress):
        # print("transfer progress ", progress)
        pass

    def didCompleteDataSend(self, success):
        # print("transfer done")
        self.sending = False
        pass
