from __future__ import annotations
from dataclasses import dataclass
import logging

from airtouch2.protocol.at2plus.control_status_common import (
    CONTROL_STATUS_SUBHEADER_LENGTH,
    ControlStatusSubHeader,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class Favourite:
    """A favourite scene, containing its ID and name."""

    id: int
    name: str


@dataclass
class FavouriteStatusMessage:
    """The status of all Favourites as reported by the controller."""

    active_favourite_id: int | None
    favourites: list[Favourite]

    @staticmethod
    def from_data(
        subheader: ControlStatusSubHeader, data: bytes
    ) -> FavouriteStatusMessage:
        """Parse the favourite status from message subdata."""
        # The active favourite is a bitmask in the first byte of the normal data
        active_mask = subheader.subdata_length.normal > 0 and data[0]
        active_id = (active_mask.bit_length() - 1) if active_mask > 0 else None

        favourites: list[Favourite] = []

        # The repeating blocks start after the normal data
        offset = subheader.subdata_length.normal
        repeat_len = subheader.subdata_length.repeat_length

        for i in range(subheader.subdata_length.repeat_count):
            start = offset + i * repeat_len
            block = data[start : start + repeat_len]

            fav_id = block[0]
            # Name is a null-terminated string in the next 8 bytes
            fav_name = block[1:9].split(b"\x00")[0].decode("ascii")

            favourites.append(Favourite(id=fav_id, name=fav_name))
            _LOGGER.debug(f"Discovered favourite: ID={fav_id}, Name='{fav_name}'")

        if active_id is not None:
            _LOGGER.debug(f"Active favourite ID: {active_id}")

        return FavouriteStatusMessage(
            active_favourite_id=active_id, favourites=favourites
        )
