class RwcpSegment(object):
    """RWCP Segment"""

    MAX_PAYLOAD_LEN = 254
    MAX_SEQUENCE = 63
    SEQUENCE_SPACE_SIZE = 64
    HEADER_MASK_SEQ_NUMBER = 0x3F
    HEADER_MASK_OPCODE = 0xC0
    HEADER_OPCODE_DATA = (0 << 6)
    HEADER_OPCODE_DATA_ACK = (0 << 6)
    HEADER_OPCODE_SYN = (1 << 6)
    HEADER_OPCODE_SYN_ACK = (1 << 6)
    HEADER_OPCODE_RST = (2 << 6)
    HEADER_OPCODE_RST_ACK = (2 << 6)
    HEADER_OPCODE_GAP = (3 << 6)
    HEADER_SIZE = 1

    def __init__(self, op_code, sequence, payload: bytes):
        self.flags = op_code
        self.sequence = sequence
        self.length = 0 if payload is None else len(payload)
        self.bytes = bytearray([op_code & self.HEADER_MASK_OPCODE | sequence & self.HEADER_MASK_SEQ_NUMBER])
        if payload is not None:
            self.bytes.extend(payload)

    @classmethod
    def create_valid_segment(cls, op_code, sequence, payload: bytes = None):
        if (sequence > cls.MAX_SEQUENCE or sequence < 0
                or payload is not None and len(payload) > cls.MAX_PAYLOAD_LEN):
            return None
        if op_code == RwcpSegment.HEADER_OPCODE_SYN and payload is not None and len(payload) != 3:
            return None
        return cls(op_code, sequence, payload)

