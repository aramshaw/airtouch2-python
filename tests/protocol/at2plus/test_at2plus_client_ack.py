import unittest

from airtouch2.at2plus.At2PlusClient import At2PlusClient
from airtouch2.common.Buffer import Buffer
from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubType
from airtouch2.protocol.at2plus.crc16_modbus import crc16
from airtouch2.protocol.at2plus.messages.AcStatus import AcStatusMessage
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


class TestExtendedStatusHandling(unittest.IsolatedAsyncioTestCase):
    async def test_updates_console_temperatures_and_still_acks(self):
        client, sent = _make_client_with_capture()
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

        notified = []
        client.add_console_temperature_callback(lambda: notified.append(dict(client.console_temperatures)))

        await client.handle_one_message()

        self.assertEqual(client.console_temperatures, {0: 19.7})
        self.assertEqual(notified, [{0: 19.7}])  # callback fired with the new reading
        self.assertEqual(len(sent), 1)  # 0x2B still acknowledged


class TestConnectionState(unittest.IsolatedAsyncioTestCase):
    async def test_connected_flag_and_callback_transitions(self):
        client, _ = _make_client_with_capture()
        events = []
        client.add_connection_callback(lambda: events.append(client.connected))

        self.assertFalse(client.connected)
        await client._on_connect()   # (re)connect: marks connected + sends handshake
        self.assertTrue(client.connected)
        client._on_disconnect()      # NetClient signalling a lost connection
        self.assertFalse(client.connected)
        self.assertEqual(events, [True, False])


class TestKeepAlivePoll(unittest.IsolatedAsyncioTestCase):
    """The controller resets the socket after ~16 min of silence; a periodic
    lightweight status request keeps the session alive (see
    docs/controller-investigation.md)."""

    async def test_poll_sends_status_request_when_connected(self):
        client, sent = _make_client_with_capture()
        client.connected = True
        await client._send_keepalive_poll()
        self.assertEqual(len(sent), 1)
        self.assertIsInstance(sent[0], AcStatusMessage)

    async def test_poll_sends_nothing_when_disconnected(self):
        client, sent = _make_client_with_capture()
        client.connected = False
        await client._send_keepalive_poll()
        self.assertEqual(len(sent), 0)
