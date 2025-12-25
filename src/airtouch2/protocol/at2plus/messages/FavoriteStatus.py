from __future__ import annotations
from dataclasses import dataclass
import logging

from airtouch2.protocol.at2plus.control_status_common import ControlStatusSubHeader

_LOGGER = logging.getLogger(__name__)


@dataclass
class Favorite:
    """A favorite scene with ID and name."""
    id: int
    name: str


@dataclass
class FavoriteStatusMessage:
    """Status of all favorites reported by the controller."""
    active_favorite_id: int | None
    favorites: list[Favorite]

    @staticmethod
    def from_data(subheader: ControlStatusSubHeader, data: bytes) -> FavoriteStatusMessage:
        """Parse favorite status from message subdata."""
        # Active favorite is a bitmask in first byte of normal data
        active_mask = subheader.subdata_length.normal > 0 and data[0]
        active_id = (active_mask.bit_length() - 1) if active_mask > 0 else None

        favorites: list[Favorite] = []
        offset = subheader.subdata_length.normal
        repeat_len = subheader.subdata_length.repeat_length

        for i in range(subheader.subdata_length.repeat_count):
            start = offset + i * repeat_len
            block = data[start:start + repeat_len]
            fav_id = block[0]
            # Name is null-terminated ASCII in bytes 1-8
            fav_name = block[1:9].split(b"\x00")[0].decode("ascii")
            favorites.append(Favorite(id=fav_id, name=fav_name))

        return FavoriteStatusMessage(active_favorite_id=active_id, favorites=favorites)
