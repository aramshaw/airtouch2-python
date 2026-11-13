import unittest

from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubHeader
from airtouch2.protocol.at2plus.messages.ExtendedStatus import ExtendedStatusMessage


class TestExtendedStatus(unittest.TestCase):
    # A real 0x2B extended-status payload captured from the controller.
    # Sensor blocks: 0x80-0x83 (favourite availability), 0x90 console temp
    # 0x02c5 = 709 -> (709 - 500) / 10 = 20.9C, 0x91 console absent (0x07ff = no reading).
    DATA = bytes.fromhex(
        "2b00000000040006808007ff818107ff828207ff838307ff90ff02c591ff07ff"
    )

    def _parse(self):
        subheader = ControlStatusSubHeader.from_bytes(self.DATA[:8])
        return ExtendedStatusMessage.from_subdata(subheader, self.DATA[8:])

    def test_decodes_present_console_temperature(self):
        message = self._parse()
        # Same encoding as AC status. Checked 2026-11-14 against a T&H sensor
        # beside the console: 500 read within ~0.3C, 512 read ~1.5C low.
        self.assertEqual(message.console_temperatures, {0: 20.9})

    def test_absent_console_is_omitted(self):
        # Console 1 (id 0x91) reports 0x07ff (no sensor) and must not appear.
        self.assertNotIn(1, self._parse().console_temperatures)
