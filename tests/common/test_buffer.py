import unittest
from airtouch2.common.Buffer import Buffer


class TestBuffer(unittest.TestCase):
    def test_get_data_from_offset_basic(self):
        """Test get_data_from_offset returns data from offset to head."""
        buffer = Buffer(10)
        buffer.append_bytes(bytes([0x01, 0x02, 0x03, 0x04, 0x05]))

        # Get data from offset 2 (should return bytes 3, 4, 5)
        result = buffer.get_data_from_offset(2)
        self.assertEqual(result, bytes([0x03, 0x04, 0x05]))

    def test_get_data_from_offset_zero(self):
        """Test get_data_from_offset with offset 0 returns all data."""
        buffer = Buffer(5)
        buffer.append_bytes(bytes([0xAA, 0xBB, 0xCC, 0xDD, 0xEE]))

        result = buffer.get_data_from_offset(0)
        self.assertEqual(result, bytes([0xAA, 0xBB, 0xCC, 0xDD, 0xEE]))

    def test_get_data_from_offset_at_head(self):
        """Test get_data_from_offset at head position returns empty."""
        buffer = Buffer(5)
        buffer.append_bytes(bytes([0x01, 0x02, 0x03, 0x04, 0x05]))

        result = buffer.get_data_from_offset(5)
        self.assertEqual(result, bytes())

    def test_get_data_from_offset_beyond_head(self):
        """Test get_data_from_offset beyond head returns empty."""
        buffer = Buffer(10)
        buffer.append_bytes(bytes([0x01, 0x02, 0x03]))

        result = buffer.get_data_from_offset(10)
        self.assertEqual(result, bytes())


if __name__ == '__main__':
    unittest.main()
