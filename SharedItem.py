from FlooPacket import FlooPacket


class SharedItem(object):
    def __init__(self, item_type, payload: bytes, hash_value):
        self.type = item_type
        self.bytes = payload
        self.hashValue = hash_value

    @classmethod
    def create_valid_item(cls, pkt_type, payload: bytes, hash_value=None):
        if FlooPacket.TYP_EMP < pkt_type < FlooPacket.TYP_MAX:
            return cls(pkt_type, payload, hash_value)
        else:
            return None
