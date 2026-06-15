import unittest

from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubHeader
from airtouch2.protocol.at2plus.messages.ExtendedStatus import ExtendedStatusMessage


class TestExtendedStatus(unittest.TestCase):
    # A real 0x2B extended-status payload captured from the controller.
    # Sensor blocks: 0x80-0x83 (favourite availability), 0x90 console temp 19.7C,
    # 0x91 console absent (0x07ff = no reading).
    DATA = bytes.fromhex(
        "2b00000000040006808007ff818107ff828207ff838307ff90ff02c591ff07ff"
    )

    def _parse(self):
        subheader = ControlStatusSubHeader.from_bytes(self.DATA[:8])
        return ExtendedStatusMessage.from_subdata(subheader, self.DATA[8:])

    def test_decodes_present_console_temperature(self):
        message = self._parse()
        self.assertEqual(message.console_temperatures, {0: 19.7})

    def test_absent_console_is_omitted(self):
        # Console 1 (id 0x91) reports 0x07ff (no sensor) and must not appear.
        self.assertNotIn(1, self._parse().console_temperatures)
