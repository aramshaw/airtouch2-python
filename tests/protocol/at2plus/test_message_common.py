import unittest
from airtouch2.common.Buffer import Buffer
from airtouch2.protocol.at2plus.crc16_modbus import crc16
from airtouch2.protocol.at2plus.message_common import (
    AddressMsgType,
    AddressSource,
    HEADER_MAGIC,
    MESSAGE_ID,
    Header,
    Message,
    MessageType,
)


class TestHeader(unittest.TestCase):
    def test_serialize(self):
        header = Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, 15)
        serialized = header.to_bytes()

        expected = bytes([HEADER_MAGIC, HEADER_MAGIC, AddressMsgType.NORMAL, AddressSource.SELF]) + bytes([MESSAGE_ID, MessageType.CONTROL_STATUS]) + (15).to_bytes(2, 'big')
        self.assertEqual(serialized.hex(':'), expected.hex(':'))

    def test_deserialize(self):
        raw = bytes([HEADER_MAGIC, HEADER_MAGIC, AddressSource.SELF, AddressMsgType.NORMAL]) + bytes([MESSAGE_ID, MessageType.CONTROL_STATUS]) + (15).to_bytes(2, 'big')
        header = Header.from_bytes(raw)

        self.assertEqual(raw.hex(':'), header.to_bytes().hex(':'))


class TestMessage(unittest.TestCase):
    def test_to_bytes_frames_header_data_and_checksum(self):
        data = bytes([0x2B, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
        message = Message(
            Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, len(data)),
            Buffer.from_bytes(data),
        )

        out = message.to_bytes()

        # magic, then header tail, then the data payload
        self.assertEqual(out[0:2], bytes([HEADER_MAGIC, HEADER_MAGIC]))
        self.assertEqual(out[8:8 + len(data)], data)
        # trailing 2-byte CRC is computed from the address field (offset 2) to end of data
        self.assertEqual(out[-2:], crc16(out[2:-2]))
        # full length = 8 header + data + 2 checksum
        self.assertEqual(len(out), 8 + len(data) + 2)

    def test_to_bytes_uses_control_status_reply_address(self):
        # ACKs for undocumented status messages are sent with 0xC0 in the address field.
        data = bytes([0x45, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
        message = Message(Header(0xC0, MessageType.CONTROL_STATUS, len(data)), Buffer.from_bytes(data))

        out = message.to_bytes()

        self.assertEqual(out[2], 0xC0)
        self.assertEqual(out[3], AddressSource.SELF)
        self.assertEqual(out[-2:], crc16(out[2:-2]))


class TestHeaderUnknownAddressSource(unittest.TestCase):
    def test_tolerates_unknown_address_source(self):
        # The controller sends 0xFD as the address-source byte on the favourite
        # activation ack path. The source field is informational (not used to
        # build the Header), so parsing must not raise on an unknown value.
        header = Header.from_bytes(bytes.fromhex("5555fd800bc00036"))
        self.assertEqual(header.type, MessageType.CONTROL_STATUS)
        self.assertEqual(header.data_length, 0x36)


class TestPowerStatusType(unittest.TestCase):
    def test_power_status_type_recognised(self):
        self.assertEqual(MessageType(0x27), MessageType.POWER_STATUS)

    def test_header_parses_real_power_message(self):
        # Real 0x27 power broadcast header captured from the controller.
        header = Header.from_bytes(bytes.fromhex("5555b08001270001"))
        self.assertEqual(header.type, MessageType.POWER_STATUS)
        self.assertEqual(header.data_length, 1)
