
from FlooPacket import FlooPacket
from SharedItem import SharedItem

class FlooPacketParser(object):
    """FlooGoo Packet Parser"""

    HEAD = 0
    TYPE = 1
    LEN0 = 2
    LEN1 = 3
    LEN2 = 4
    PAYLOAD = 5
    INVALID = 6

    def __init__(self):
        self.state = self.HEAD
        self.payload = bytearray()
        self.len = 0
        self.type = FlooPacket.TYP_EMP

    def run(self, payload: bytes) -> [SharedItem]:
        parsed_items = []
        index = 0
        while index < len(payload):
            value = payload[index]
            match self.state:
                case FlooPacketParser.HEAD:
                    if value == FlooPacket.HEADER:
                        self.state = FlooPacketParser.TYPE
                        print("FlooPkt start")
                    else:
                        print("BAI msg byte, ignore")
                    index += 1
                case FlooPacketParser.TYPE:
                    self.type = value
                    self.state = FlooPacketParser.LEN0
                    index += 1
                case FlooPacketParser.LEN0:
                    self.len = value << 16
                    self.state = FlooPacketParser.LEN1
                    index += 1
                case FlooPacketParser.LEN1:
                    self.len += value << 8
                    self.state = FlooPacketParser.LEN2
                    index += 1
                case FlooPacketParser.LEN2:
                    self.len += value
                    self.state = FlooPacketParser.PAYLOAD
                    index += 1
                case FlooPacketParser.PAYLOAD:
                    if len(payload) - index < self.len:
                        self.payload.extend(payload[index:])
                        self.len -= len(payload) - index
                        index = len(payload)
                    else:
                        self.payload.extend(payload[index: index + self.len])
                        index += self.len
                        self.len = 0
                        new_item = SharedItem.create_valid_item(self.type, self.payload)
                        if new_item is not None:
                            parsed_items.append(new_item)
                        self.state = FlooPacketParser.HEAD
                        print("FlooPkt parser reset")
                        self.payload = bytearray()
        if len(parsed_items) > 0:
            # print("parsed a new item")
            return parsed_items
        else:
            return None






