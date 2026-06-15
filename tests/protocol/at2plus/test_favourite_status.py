import unittest

from airtouch2.at2plus.At2PlusClient import At2PlusClient
from airtouch2.common.Buffer import Buffer
from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubHeader
from airtouch2.protocol.at2plus.crc16_modbus import crc16
from airtouch2.protocol.at2plus.message_common import (
    AddressMsgType,
    Header,
    Message,
    MessageType,
)
from airtouch2.protocol.at2plus.messages.FavouriteStatus import (
    FavouriteStatusMessage,
    RequestFavouriteStatusMessage,
)

# A real 0x31 favourite-status reply captured from the controller (data after the
# 8-byte message header). Favourites: 0=main (active), 1=gym, 2=night, 3=Fav4.
FAVOURITE_REPLY = bytes.fromhex(
    "31000002000b00040108"
    "006d61696e000000001b00"  # 0: main
    "0167796d00000000009b00"  # 1: gym
    "026e696768740000001100"  # 2: night
    "0346617634000000000000"  # 3: Fav4
)


def _client_with_capture():
    client = At2PlusClient("localhost")
    sent: list[Message] = []

    async def fake_send(message):
        sent.append(message)

    client._client.send = fake_send
    return client, sent


class TestFavouriteStatusParse(unittest.TestCase):
    def _parse(self) -> FavouriteStatusMessage:
        subheader = ControlStatusSubHeader.from_bytes(FAVOURITE_REPLY[:8])
        return FavouriteStatusMessage.from_data(subheader, FAVOURITE_REPLY[8:])

    def test_parses_names_and_ids(self):
        self.assertEqual(
            [(f.id, f.name) for f in self._parse().favourites],
            [(0, "main"), (1, "gym"), (2, "night"), (3, "Fav4")],
        )

    def test_active_favourite(self):
        self.assertEqual(self._parse().active_favourite_id, 0)


class TestFavouriteRequest(unittest.TestCase):
    def test_request_frame(self):
        out = RequestFavouriteStatusMessage().to_bytes()
        # 55 55 80 b0 01 c0 00 08  31 00 00 00 00 0b 00 00  (the validated request)
        self.assertEqual(out[:16].hex(), "555580b001c0000831000000000b0000")
        self.assertEqual(out[-2:], crc16(out[2:-2]))


class TestClientFavourites(unittest.IsolatedAsyncioTestCase):
    async def test_on_connect_requests_favourites(self):
        client, sent = _client_with_capture()
        await client._on_connect()
        subtypes = [m.to_bytes()[8] for m in sent]
        self.assertIn(0x31, subtypes)  # favourites requested alongside group/AC status

    async def test_handles_favourite_status_reply(self):
        client, sent = _client_with_capture()
        received = Message(
            Header(AddressMsgType.NORMAL, MessageType.CONTROL_STATUS, len(FAVOURITE_REPLY), _received=True),
            Buffer.from_bytes(FAVOURITE_REPLY),
        )

        async def fake_read():
            return received

        client._read_message = fake_read
        fired = []
        client.add_favourite_callback(lambda: fired.append(True))

        await client.handle_one_message()

        self.assertEqual(
            [(f.id, f.name) for f in client.favourites],
            [(0, "main"), (1, "gym"), (2, "night"), (3, "Fav4")],
        )
        self.assertEqual(client.active_favourite_id, 0)
        self.assertEqual(fired, [True])  # change callback fired
