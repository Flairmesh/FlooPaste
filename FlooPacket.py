class FlooPacket(object):
    """FlooGoo Packet"""

    LEN_LIMIT = 16777216

    HEADER = 0xFF

    TYP_EMP = 0
    TYP_STR = 1
    TYP_IMG = 2
    TYP_MAX = 3

    def __init__(self, pkt_type, payload: bytes):
        self.bytes = bytearray([self.HEADER, pkt_type])
        payload_len = len(payload)
        self.bytes.extend([payload_len >> 16 & 0xFF, payload_len >> 8 & 0xFF, payload_len & 0xFF])
        self.bytes.extend(payload)

    @classmethod
    def create_valid_packet(cls, pkt_type, payload: bytes):
        if FlooPacket.TYP_EMP < pkt_type < FlooPacket.TYP_MAX:
            return cls(pkt_type, payload)
        else:
            return None
