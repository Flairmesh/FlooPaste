import threading
from RwcpSegment import RwcpSegment


class RwcpClient(object):
    """RWCP Client"""

    SYN_TIMEOUT_MS = 1500
    RST_TIMEOUT_MS = 1500
    DATA_TIMEOUT_MS_NORMAL = 1000
    DATA_TIMEOUT_MS_MAX = 2000

    CWIN_MAX = 8

    STATE_LISTEN = 0
    STATE_SYNC_SENT = 1
    STATE_ESTABLISHED = 2
    STATE_CLOSING = 3

    def __init__(self, delegate):
        self.delegate = delegate
        self.state = RwcpClient.STATE_LISTEN
        self.lastAckSequence = -1
        self.nextSequence = 0
        self.window = RwcpClient.CWIN_MAX
        self.credits = RwcpClient.CWIN_MAX
        self.isResendingSegments = False
        self.resendingIndex = 0
        self.pendingData = []
        self.unacknowledgedSegments = []
        self.timer = None
        self.timerRunning = False
        self.dataTimeout = RwcpClient.DATA_TIMEOUT_MS_NORMAL
        self.acknowledgedSegments = 0
        self.transferSize = 0
        self.progress = 0

    def commInit(self):
        self.state = RwcpClient.STATE_LISTEN
        self.lastAckSequence = -1
        self.nextSequence = 0
        self.window = RwcpClient.CWIN_MAX
        self.credits = RwcpClient.CWIN_MAX
        self.isResendingSegments = False
        self.resendingIndex = 0
        self.pendingData = []
        self.cancelTimeout()
        self.dataTimeout = RwcpClient.DATA_TIMEOUT_MS_NORMAL
        self.acknowledgedSegments = 0
        self.transferSize = 0
        self.progress = 0

    def sendData(self, payload_bytes, mtu_size):
        self.transferSize = len(payload_bytes)
        # print("total transfer size", self.transferSize)
        self.progress = 0
        bytes_to_send = self.transferSize
        offset = 0
        while bytes_to_send > 0:
            payload_size = bytes_to_send if bytes_to_send < mtu_size - 1 else mtu_size - 1
            payload: bytearray = payload_bytes[offset: offset + payload_size]
            offset += payload_size
            bytes_to_send -= payload_size
            if payload_size < mtu_size - 1:
                payload.extend(bytearray(mtu_size - 1 - payload_size))
            # print("add payload size", payload_size)
            self.appendPayload(payload)
        self.startTransfer()

    def appendPayload(self, payload_bytes):
        self.pendingData.append(payload_bytes)

    def startTransfer(self):
        # print("startTransfer")
        if self.state == RwcpClient.STATE_LISTEN:
            self.startSession()
        elif self.state == RwcpClient.STATE_ESTABLISHED:
            self.sendDataSegment()

    def abort(self):
        if self.state == RwcpClient.STATE_LISTEN:
            return
        self.reset(True)
        if not self.sendRstSegment():
            self.terminateSession()

    def startSession(self) -> bool:
        if self.state != RwcpClient.STATE_LISTEN:
            # print("Can not start new transfer while not in idle")
            return False
        if self.sendRstSegment():
            return True
        else:
            self.terminateSession()
            return False

    def terminateSession(self):
        self.reset(True)
        self.delegate.didCompleteDataSend(False)

    def processReceivedData(self, ack_bytes):
        if len(ack_bytes) < RwcpSegment.HEADER_SIZE:
            return
        index = 0
        while index < len(ack_bytes):
            ack = ack_bytes[index]
            sequence = ack & RwcpSegment.HEADER_MASK_SEQ_NUMBER
            opcode = ack & RwcpSegment.HEADER_MASK_OPCODE
            segment = RwcpSegment.create_valid_segment(opcode, sequence)
            match opcode:
                case RwcpSegment.HEADER_OPCODE_SYN_ACK:
                    self.receiveSyncAck(segment)
                case RwcpSegment.HEADER_OPCODE_DATA_ACK:
                    self.receiveDataAck(segment)
                case RwcpSegment.HEADER_OPCODE_RST:
                    self.receiveRst(segment)
                case RwcpSegment.HEADER_OPCODE_GAP:
                    self.receiveGap(segment)
            index += 1

    def receiveSyncAck(self, segment) -> bool:
        # print("Sync Ack")
        match self.state:
            case RwcpClient.STATE_SYNC_SENT:
                self.cancelTimeout()
                if self.validateAckSequence(RwcpSegment.HEADER_OPCODE_SYN, segment.sequence) >= 0:
                    self.state = RwcpClient.STATE_ESTABLISHED
                    if len(self.pendingData) > 0:
                        self.sendDataSegment()
                else:
                    self.terminateSession()
                    self.sendRstSegment()
                return True
            case RwcpClient.STATE_ESTABLISHED:
                self.cancelTimeout()
                if len(self.unacknowledgedSegments) > 0:
                    self.resendDataSegment()
                return True
            case RwcpClient.STATE_LISTEN | RwcpClient.STATE_CLOSING:
                return False

    def receiveDataAck(self, segment) -> bool:
        # print("Data Ack", self.state, "seq:", segment.sequence)
        match self.state:
            case RwcpClient.STATE_ESTABLISHED:
                self.cancelTimeout()
                if self.validateAckSequence(RwcpSegment.HEADER_OPCODE_DATA, segment.sequence) >= 0:
                    if self.credits > 0 and len(self.pendingData) > 0:
                        self.sendDataSegment()
                    elif len(self.pendingData) == 0 and len(self.unacknowledgedSegments) == 0:
                        self.sendRstSegment()
                    elif len(self.pendingData) == 0 and len(self.unacknowledgedSegments) > 0 \
                            or self.credits == 0 and len(self.pendingData) > 0:
                        self.setTimer(self.dataTimeout)
                return True
            case RwcpClient.STATE_CLOSING:
                return True
            case RwcpClient.STATE_LISTEN | RwcpClient.STATE_SYNC_SENT:
                return False

    def receiveRst(self, segment) -> bool:
        # print("Rst Ack ", self.state)
        match self.state:
            case RwcpClient.STATE_SYNC_SENT:
                return True
            case RwcpClient.STATE_ESTABLISHED:
                self.terminateSession()
                return True
            case RwcpClient.STATE_CLOSING:
                self.cancelTimeout()
                self.validateAckSequence(RwcpSegment.HEADER_OPCODE_RST, segment.sequence)
                self.reset(False)
                if len(self.pendingData):
                    if not self.sendSyncSegment():
                        self.terminateSession()
                else:
                    self.delegate.didCompleteDataSend(True)
                return True
            case RwcpClient.STATE_LISTEN:
                return False

    def receiveGap(self, segment) -> bool:
        match self.state:
            case RwcpClient.STATE_ESTABLISHED:
                if self.lastAckSequence > segment.sequence:
                    return True
                else:
                    self.decreaseWindow()
                    self.validateAckSequence(RwcpSegment.HEADER_OPCODE_DATA, segment.sequence)
                self.cancelTimeout()
                self.resendDataSegment()
                return True
            case RwcpClient.STATE_CLOSING:
                return True
            case RwcpClient.STATE_LISTEN | RwcpClient.STATE_SYNC_SENT:
                return False

    def validateAckSequence(self, opcode, sequence) -> int:
        not_validated = -1
        if sequence < 0:
            # print("sequence < 0")
            return not_validated
        if sequence > RwcpSegment.MAX_SEQUENCE:
            # print("sequence > 63")
            return not_validated
        if self.lastAckSequence < self.nextSequence and (
                sequence < self.lastAckSequence or sequence > self.nextSequence):
            # print("last Ack less than next and seq out of this range")
            return not_validated
        if self.lastAckSequence > self.nextSequence and self.lastAckSequence > sequence > self.nextSequence:
            # print("last Ack bigger than next and seq out of this range")
            return not_validated

        acknowledged = 0
        next_ack_sequence = self.lastAckSequence
        while next_ack_sequence != sequence:
            next_ack_sequence = self.increaseSequenceNumber(next_ack_sequence)
            # print("compare last seq: ", next_ack_sequence, "with ", sequence)
            if self.removeSegmentFromQueue(opcode, next_ack_sequence):
                self.lastAckSequence = next_ack_sequence
            if self.credits < self.window:
                self.credits += 1
            acknowledged += 1
        self.increaseWindow(acknowledged)
        return acknowledged

    def sendGapSegment(self) -> bool:
        if self.state == RwcpClient.STATE_LISTEN:
            segment = RwcpSegment.create_valid_segment(RwcpSegment.HEADER_OPCODE_GAP, 0)
            self.sendSegment(segment, 0)
            return True
        return False

    def sendRstSegment(self) -> bool:
        if self.state == RwcpClient.STATE_CLOSING:
            return True
        # print("send Rst Segment")
        self.reset(False)
        self.state = RwcpClient.STATE_CLOSING

        segment = RwcpSegment.create_valid_segment(RwcpSegment.HEADER_OPCODE_RST, self.nextSequence)
        if self.sendSegment(segment, RwcpClient.RST_TIMEOUT_MS):
            self.unacknowledgedSegments.append(segment)
            self.nextSequence = self.increaseSequenceNumber(self.nextSequence)
            self.credits -= 1
            return True
        return False

    def sendSyncSegment(self) -> bool:
        self.state = RwcpClient.STATE_SYNC_SENT
        # print("send Sync Segment")
        payload = bytes([self.transferSize >> 16 & 0xFF, self.transferSize >> 8 & 0xFF, self.transferSize & 0xFF])
        segment = RwcpSegment.create_valid_segment(RwcpSegment.HEADER_OPCODE_SYN, self.nextSequence, payload)
        if self.sendSegment(segment, RwcpClient.SYN_TIMEOUT_MS):
            self.unacknowledgedSegments.append(segment)
            self.nextSequence = self.increaseSequenceNumber(self.nextSequence)
            self.credits -= 1
            return True
        return False

    def sendDataSegment(self):
        # print("send Data Segment")
        while (self.credits > 0 and len(self.pendingData) > 0
               and not self.isResendingSegments and self.state == RwcpClient.STATE_ESTABLISHED):
            segment = RwcpSegment.create_valid_segment(RwcpSegment.HEADER_OPCODE_DATA, self.nextSequence,
                                                       self.pendingData[0])
            if not self.sendSegment(segment, self.dataTimeout):
                break
            self.pendingData.pop(0)
            self.unacknowledgedSegments.append(segment)
            self.nextSequence = self.increaseSequenceNumber(self.nextSequence)
            self.credits -= 1

    @staticmethod
    def increaseSequenceNumber(sequence) -> int:
        return (sequence + 1) % RwcpSegment.SEQUENCE_SPACE_SIZE

    @staticmethod
    def decreaseSequenceNumber(sequence, decrease) -> int:
        return (sequence - decrease + RwcpSegment.SEQUENCE_SPACE_SIZE) % RwcpSegment.SEQUENCE_SPACE_SIZE

    def resendSegment(self):
        if self.state == RwcpClient.STATE_ESTABLISHED:
            return
        # print("Resend Segment")
        self.isResendingSegments = True
        self.credits = self.window
        for segment in self.unacknowledgedSegments:
            delay = RwcpClient.SYN_TIMEOUT_MS if segment.flags == RwcpSegment.HEADER_OPCODE_SYN \
                else RwcpClient.RST_TIMEOUT_MS if segment.flags == RwcpSegment.HEADER_OPCODE_RST \
                else RwcpClient.DATA_TIMEOUT_MS_NORMAL
            if self.sendSegment(segment, delay):
                self.credits -= 1
        self.isResendingSegments = False

    def resendDataSegment(self):
        if self.state != RwcpClient.STATE_ESTABLISHED:
            return
        # print("Resend Data Segment")
        self.isResendingSegments = True
        self.credits = self.window
        moved = 0
        while len(self.unacknowledgedSegments) > self.credits:
            last_segment = self.unacknowledgedSegments.pop()
            if last_segment.flags == RwcpSegment.HEADER_OPCODE_DATA:
                self.pendingData.insert(0, last_segment.bytes[1:])
                moved += 1
        self.nextSequence = self.decreaseSequenceNumber(self.nextSequence, moved)
        self.resendingIndex = 0
        for segment in self.unacknowledgedSegments:
            if self.sendSegment(segment, self.dataTimeout):
                self.credits -= 1
                self.resendingIndex += 1
        self.isResendingSegments = False
        if self.credits > 0:
            if self.resendingIndex == 0 and len(self.pendingData) == 0:
                self.sendRstSegment()
            else:
                self.sendDataSegment()

    def sendSegment(self, segment, delay) -> bool:
        # print("Send Segment Seq:", segment.sequence)
        self.delegate.sendSegment(segment)
        if segment.flags == RwcpSegment.HEADER_OPCODE_GAP:
            return True
        if delay > 0:
            self.setTimer(delay)
        return True

    def removeSegmentFromQueue(self, opcode, sequence) -> bool:
        # print("removeSegmentFromQueue")
        index = 0
        for segment in self.unacknowledgedSegments:
            if segment.flags == opcode and segment.sequence == sequence:
                break
            index += 1
        if index < len(self.unacknowledgedSegments):
            del self.unacknowledgedSegments[index]
            if opcode == RwcpSegment.HEADER_OPCODE_DATA:
                self.progress += segment.length
                self.progress = self.transferSize if self.progress > self.transferSize else self.progress
                self.delegate.didMakeProgress(self.progress / self.transferSize)
            return True
        else:
            return False

    def reset(self, complete):
        # print("Rwcp reset")
        self.lastAckSequence = -1
        self.nextSequence = 0
        self.unacknowledgedSegments = []
        self.window = RwcpClient.CWIN_MAX
        self.credits = RwcpClient.CWIN_MAX
        self.acknowledgedSegments = 0
        self.state = RwcpClient.STATE_LISTEN
        self.progress = 0
        if complete:
            self.pendingData = []
            self.transferSize = 0

    def increaseWindow(self, acknowledged):
        self.acknowledgedSegments += acknowledged
        if self.acknowledgedSegments > self.window and self.window < RwcpClient.CWIN_MAX:
            self.acknowledgedSegments = 0
            self.window += 1
            self.credits += 1

    def decreaseWindow(self):
        self.window = (self.window - 1) / 2 + 1
        if self.window > RwcpClient.CWIN_MAX or self.window < 1:
            self.window = 1
        self.acknowledgedSegments = 0
        self.credits = self.window

    def setTimer(self, interval):
        self.cancelTimeout()
        # print("setTimer delay", interval)
        self.timer = threading.Timer(interval / 1000, self.segmentTimeout)
        self.timer.start()
        self.timerRunning = True

    def cancelTimeout(self):
        if self.timerRunning:
            # print("cancelTimer")
            self.timer.cancel()
            self.timer = None
            self.timerRunning = False

    def segmentTimeout(self):
        # print("TIME OUT>")
        if self.timerRunning:
            self.timer.cancel()
            self.timerRunning = False
            self.isResendingSegments = False
            self.acknowledgedSegments = 0
            if self.state == RwcpClient.STATE_ESTABLISHED:
                self.dataTimeout *= 2
                self.dataTimeout = RwcpClient.DATA_TIMEOUT_MS_MAX \
                    if self.dataTimeout > RwcpClient.DATA_TIMEOUT_MS_MAX else self.dataTimeout
                self.resendDataSegment()
            else:
                self.resendSegment()
