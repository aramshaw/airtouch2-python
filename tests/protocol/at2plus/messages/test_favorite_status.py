import unittest
from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubHeader, ControlStatusSubType, SubDataLength
from airtouch2.protocol.at2plus.messages.FavoriteStatus import Favorite, FavoriteStatusMessage


class TestFavorite(unittest.TestCase):
    def test_dataclass(self):
        """Test Favorite dataclass creation."""
        fav = Favorite(id=0, name="Master")
        self.assertEqual(fav.id, 0)
        self.assertEqual(fav.name, "Master")


class TestFavoriteStatusMessage(unittest.TestCase):
    def test_parse_no_favorites(self):
        """Test parsing with no favorites."""
        subheader = ControlStatusSubHeader(
            ControlStatusSubType.FAVORITE_STATUS,
            SubDataLength(normal=1, repeat_count=0, repeat_length=9)
        )
        data = bytes([0x00])  # No active favorite

        msg = FavoriteStatusMessage.from_data(subheader, data)

        self.assertIsNone(msg.active_favorite_id)
        self.assertEqual(len(msg.favorites), 0)

    def test_parse_single_favorite(self):
        """Test parsing a single favorite."""
        subheader = ControlStatusSubHeader(
            ControlStatusSubType.FAVORITE_STATUS,
            SubDataLength(normal=1, repeat_count=1, repeat_length=9)
        )
        # Active bitmask 0x01 = favorite ID 0 active
        # Favorite: ID=0, name="Master\0\0"
        data = bytes([0x01]) + bytes([0x00]) + b"Master\x00\x00"

        msg = FavoriteStatusMessage.from_data(subheader, data)

        self.assertEqual(msg.active_favorite_id, 0)
        self.assertEqual(len(msg.favorites), 1)
        self.assertEqual(msg.favorites[0].id, 0)
        self.assertEqual(msg.favorites[0].name, "Master")

    def test_parse_multiple_favorites(self):
        """Test parsing multiple favorites with one active."""
        subheader = ControlStatusSubHeader(
            ControlStatusSubType.FAVORITE_STATUS,
            SubDataLength(normal=1, repeat_count=3, repeat_length=9)
        )
        # Active bitmask 0x04 = favorite ID 2 active (bit 2 set)
        data = bytes([0x04])
        data += bytes([0x00]) + b"Home\x00\x00\x00\x00"    # ID 0
        data += bytes([0x01]) + b"Away\x00\x00\x00\x00"    # ID 1
        data += bytes([0x02]) + b"Sleep\x00\x00\x00"       # ID 2 (active)

        msg = FavoriteStatusMessage.from_data(subheader, data)

        self.assertEqual(msg.active_favorite_id, 2)
        self.assertEqual(len(msg.favorites), 3)
        self.assertEqual(msg.favorites[0].id, 0)
        self.assertEqual(msg.favorites[0].name, "Home")
        self.assertEqual(msg.favorites[1].id, 1)
        self.assertEqual(msg.favorites[1].name, "Away")
        self.assertEqual(msg.favorites[2].id, 2)
        self.assertEqual(msg.favorites[2].name, "Sleep")

    def test_parse_no_active_favorite(self):
        """Test parsing favorites with none active."""
        subheader = ControlStatusSubHeader(
            ControlStatusSubType.FAVORITE_STATUS,
            SubDataLength(normal=1, repeat_count=2, repeat_length=9)
        )
        # Active bitmask 0x00 = no favorite active
        data = bytes([0x00])
        data += bytes([0x00]) + b"Scene1\x00\x00"
        data += bytes([0x01]) + b"Scene2\x00\x00"

        msg = FavoriteStatusMessage.from_data(subheader, data)

        self.assertIsNone(msg.active_favorite_id)
        self.assertEqual(len(msg.favorites), 2)


if __name__ == '__main__':
    unittest.main()
