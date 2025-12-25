import unittest
from airtouch2.common.Buffer import Buffer
from airtouch2.protocol.at2plus.message_common import (
    AddressMsgType, AddressSource, HEADER_MAGIC, MESSAGE_ID,
    Header, Message, MessageType
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
    def test_to_bytes(self):
        """Test Message.to_bytes() produces valid serialization with checksum."""
        header = Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, 4)
        data = bytes([0x23, 0x00, 0x00, 0x00])  # Example data
        data_buffer = Buffer.from_bytes(data)

        message = Message(header, data_buffer)
        serialized = message.to_bytes()

        # Should have header (8) + data (4) + checksum (2) = 14 bytes
        self.assertEqual(len(serialized), 14)

        # Verify header magic
        self.assertEqual(serialized[0], HEADER_MAGIC)
        self.assertEqual(serialized[1], HEADER_MAGIC)

        # Verify data is included
        self.assertEqual(serialized[8:12], data)

        # Verify checksum is present (last 2 bytes, non-zero for this data)
        self.assertNotEqual(serialized[12:14], bytes([0x00, 0x00]))
