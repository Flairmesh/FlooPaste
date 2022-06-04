from threading import *
import time
import Clipboard
import serial
import serial.tools.list_ports
import hashlib
from RwcpSegment import RwcpSegment
from RwcpClient import RwcpClient
from FlooPacket import FlooPacket
from FlooPacketParser import FlooPacketParser


class FlooTransceiver(Thread):
    """FlooGoo data interface on USB COM"""

    PORT_OPENED = 0
    PORT_CLOSED = 1
    NOTIFICATION_TIMEOUT = 400

    def __init__(self):
        super(FlooTransceiver, self).__init__()
        self.port_name = None
        self.port_opened = False
        self.port = None
        self.sending = False
        self.rwcpClient = RwcpClient(self)
        self.clipObject = None
        self.flooParser = FlooPacketParser()
        self.notified = None
        self.notifiedCounter = 0
        self.lastClipItemHash = None

    def reset(self):
        print("port now reset")
        self.port_name = None
        self.port_opened = False
        self.port = None
        self.sending = False

    def monitor_port(self) -> bool:
        ports = [port.name for port in serial.tools.list_ports.grep('0A12:4007.*FMA100')]
        if ports:
            if not self.port_opened:
                self.port_name = ports[0]
                print("current port ", self.port_name, " state: ", self.port_opened)
                try:
                    print("try open")
                    self.port = serial.Serial(port=self.port_name, baudrate=921600,
                                              bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
                    # self.port.open()
                    self.port_opened = self.port.is_open
                    print("Change port state: ", self.port_opened)
                except:
                    return False
                if self.port_opened:

                    return True
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

    def monitorClipboard(self):
        clip_item = Clipboard.copy_item_from_clipboard()
        if clip_item is not None:
            new_hash = hashlib.sha256(clip_item.bytes).digest()
            if self.lastClipItemHash is None or self.lastClipItemHash != new_hash:
                self.lastClipItemHash = new_hash
                return clip_item
        return None

    def run(self):
        print("run_loop started")
        while True:
            if self.monitor_port():
                heart_beat_counter = 0
                while self.port.is_open:
                    heart_beat_counter += 1
                    if heart_beat_counter > 100:
                        heart_beat_counter = 0
                        if self.flooParser.len == 0:
                            new_clip_item = self.monitorClipboard()
                            if new_clip_item is not None:
                                floo_pkt = FlooPacket.create_valid_packet(new_clip_item.type, new_clip_item.bytes)
                                self.rwcpClient.sendData(floo_pkt.bytes, 255)
                                self.sending = True
                        if not self.sending:
                            print("Idle heart beating")
                            self.heartBeat()
                    # print("monitoring rx ... ")
                    if self.port.inWaiting() > 0:
                        if self.sending:
                            # Rwcp ack
                            print("Rwcp Ack")
                            self.rwcpClient.processReceivedData(self.port.read(self.port.inWaiting()))
                        else:
                            parsed_items = self.flooParser.run(self.port.read(self.port.inWaiting()))
                            if parsed_items is not None and len(parsed_items) > 0:
                                last_item = parsed_items[-1]
                                if last_item.type == FlooPacket.TYP_STR:
                                    Clipboard.send_utf8bytes_str_to_clipboard(last_item.bytes)
                                    self.notified = FlooPacket.TYP_STR
                                    self.notifiedCounter = FlooTransceiver.NOTIFICATION_TIMEOUT
                                elif last_item.type == FlooPacket.TYP_IMG:
                                    Clipboard.send_jpeg_to_clipboard(last_item.bytes)
                                    self.notified = FlooPacket.TYP_IMG
                                    self.notifiedCounter = FlooTransceiver.NOTIFICATION_TIMEOUT
                                self.lastClipItemHash = hashlib.sha256(last_item.bytes).digest()
                    else:
                        pass
                        # print("serial idle")
                    if self.notified is not None:
                        self.notifiedCounter -= 1
                        if self.notifiedCounter == 0:
                            self.notified = None
                    time.sleep(0.01)
            self.reset()
            time.sleep(1)  # check port after 1 second

    def setNotification(self):
        pass

    def sendSegment(self, segment):
        if self.port.is_open:
            # print("port out", segment.bytes)
            self.port.write(segment.bytes)

    def didMakeProgress(self, progress):
        print("transfer progress ", progress)
        pass

    def didCompleteDataSend(self, success):
        print("transfer done")
        self.sending = False
        pass
