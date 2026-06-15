import unittest

from airtouch2.at2plus.At2PlusClient import At2PlusClient
from airtouch2.common.Buffer import Buffer
from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubType
from airtouch2.protocol.at2plus.crc16_modbus import crc16
from airtouch2.protocol.at2plus.message_common import (
    AddressMsgType,
    AddressSource,
    Header,
    Message,
    MessageType,
)


def _make_client_with_capture():
    """An At2PlusClient whose outgoing messages are captured instead of sent."""
    client = At2PlusClient("localhost")
    sent: list[Message] = []

    async def fake_send(msg):
        sent.append(msg)

    client._client.send = fake_send
    return client, sent


class TestStatusAck(unittest.IsolatedAsyncioTestCase):
    async def test_ack_for_extended_status(self):
        client, sent = _make_client_with_capture()
        await client._acknowledge_status(ControlStatusSubType.EXTENDED_STATUS)

        self.assertEqual(len(sent), 1)
        out = sent[0].to_bytes()
        self.assertEqual(out[2], 0xC0)  # control/status reply address (not the usual 0x80)
        self.assertEqual(out[3], AddressSource.SELF)
        self.assertEqual(out[5], MessageType.CONTROL_STATUS)
        # minimal ack subdata: subtype echoed, 1-byte normal data, no repeats
        self.assertEqual(out[8:17], bytes([0x2B, 0, 0, 1, 0, 0, 0, 0, 0]))
        self.assertEqual(out[-2:], crc16(out[2:-2]))  # checksum valid

    async def test_ack_for_identity(self):
        client, sent = _make_client_with_capture()
        await client._acknowledge_status(ControlStatusSubType.IDENTITY)

        out = sent[0].to_bytes()
        self.assertEqual(out[8:17], bytes([0x45, 0, 0, 1, 0, 0, 0, 0, 0]))
        self.assertEqual(out[-2:], crc16(out[2:-2]))

    async def test_handle_message_acks_extended_status_broadcast(self):
        client, sent = _make_client_with_capture()
        # A real 0x2B extended-status payload captured from the controller.
        data = bytes.fromhex(
            "2b00000000040006808007ff818107ff828207ff838307ff90ff02c591ff07ff"
        )
        received = Message(
            Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, len(data), _received=True),
            Buffer.from_bytes(data),
        )

        async def fake_read():
            return received

        client._read_message = fake_read
        await client.handle_one_message()

        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0].to_bytes()[8], 0x2B)
