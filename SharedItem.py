from FlooPacket import FlooPacket


class SharedItem(object):
    def __init__(self, item_type, payload: bytes):
        self.type = item_type
        self.bytes = payload

    @classmethod
    def create_valid_item(cls, pkt_type, payload: bytes):
        if FlooPacket.TYP_EMP < pkt_type < FlooPacket.TYP_MAX:
            return cls(pkt_type, payload)
        else:
            return None
