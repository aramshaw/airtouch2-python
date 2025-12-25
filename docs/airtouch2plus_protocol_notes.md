# AirTouch 2+ Extended Protocol Notes

This document describes extended message types discovered in AirTouch 2+ (AT2+) controllers
that are not covered in the standard AirTouch 2 documentation.

## Overview

AirTouch 2+ controllers send additional message types beyond the documented protocol.
These messages require proper handling to maintain stable connections and expose
additional functionality like favorites/scenes.

## Message Types

### MessageType (Header byte 5)

| Value | Name | Description |
|-------|------|-------------|
| 0xC0 | CONTROL_STATUS | Standard control/status messages |
| 0x1F | EXTENDED | Extended messages (abilities, group names) |
| 0x27 | POWER_STATUS | System on/off status broadcast |

### ControlStatusSubType (Data byte 0)

| Value | Name | Description | ACK Required |
|-------|------|-------------|--------------|
| 0x10 | AC_STATUS_EXTENDED | Extended AC status format | No |
| 0x20 | GROUP_CONTROL | Zone/group control | No |
| 0x21 | GROUP_STATUS | Zone/group status | No |
| 0x22 | AC_CONTROL | AC unit control | No |
| 0x23 | AC_STATUS | AC unit status | No |
| 0x2B | EXTENDED_STATUS | System status (timers, counters) | Yes |
| 0x31 | FAVORITE_STATUS | Favorite scene names and active status | No |
| 0x40 | ZONE_STATUS | Zone control status | No |
| 0x45 | SYSTEM_IDENTITY | System identity broadcast | Yes |

## Message Details

### POWER_STATUS (0x27)

Broadcast when the system power state changes.

**Structure:**
```
Header: 55 55 80 80 01 27 00 01 [crc16]
Data: 01 = ON, 00 = OFF
```

No acknowledgment required.

### EXTENDED_STATUS (0x2B)

Periodic broadcast containing system status information including timers and counters.

**Structure:**
```
Subheader: 2B 00 [normal_len:2] [repeat_len:2] [repeat_count:2]
Data: Variable length status information
```

**ACK Required:** Yes - must send acknowledgment to maintain connection stability.

### FAVORITE_STATUS (0x31)

Reports configured favorite scenes and which one is currently active.

**Structure:**
```
Subheader: 31 00 00 01 00 09 00 XX
           |        |    |    |
           |        |    |    +-- Number of favorites (repeat count)
           |        |    +------- Each favorite is 9 bytes (repeat length)
           |        +------------ 1 byte normal data (active bitmask)
           +---------------------- Subtype 0x31

Normal data (1 byte):
  - Bitmask indicating active favorite
  - bit_length() - 1 gives the active favorite ID
  - 0 = no favorite active

Repeat data (9 bytes each):
  Byte 0: Favorite ID (0-7)
  Bytes 1-8: Favorite name (null-terminated ASCII)
```

**Example:**
```
31 00 00 01 00 09 00 04    <- Header: 4 favorites, 9 bytes each
02                          <- Active favorite bitmask (ID 1 active)
00 4D 61 73 74 65 72 00 00  <- ID 0: "Master"
01 53 6C 65 65 70 00 00 00  <- ID 1: "Sleep"  (active)
02 41 77 61 79 00 00 00 00  <- ID 2: "Away"
03 48 6F 6D 65 00 00 00 00  <- ID 3: "Home"
```

No acknowledgment required.

### SYSTEM_IDENTITY (0x45)

System identity broadcast, typically containing "Polyaire Atch2PM" or similar.

**Structure:**
```
Subheader: 45 00 [normal_len:2] [repeat_len:2] [repeat_count:2]
Data: System identification string
```

**ACK Required:** Yes - must send acknowledgment to maintain connection stability.

## ACK Response Format

For message types requiring acknowledgment (0x2B, 0x45), send this response:

**Structure:**
```
Header: 55 55 C0 B0 01 C0 00 09 [crc16]
        |     |     |  |  |
        |     |     |  |  +-- Data length (9 bytes)
        |     |     |  +----- Message type (CONTROL_STATUS)
        |     |     +-------- Message ID
        |     +-------------- Address: 0xC0 0xB0 for ACK messages
        +-------------------- Magic bytes

Data (9 bytes):
  Byte 0: Original subtype (0x2B or 0x45)
  Byte 1: 0x00 (reserved)
  Bytes 2-3: Normal data length (0x00 0x01)
  Bytes 4-5: Repeat data length (0x00 0x00)
  Bytes 6-7: Repeat count (0x00 0x00)
  Byte 8: 0x00 (payload)
```

**Important:** ACK messages use address field 0xC0 instead of the standard 0x80.

### Rate Limiting

To prevent flooding the controller with duplicate ACKs:
- Track sent ACKs by content hash
- Minimum interval between identical ACKs: 300ms
- This prevents issues when multiple status messages arrive in quick succession

## Connection Stability

Without proper ACK responses for 0x2B and 0x45 messages, the AirTouch 2+ controller
may refuse new connections. The controller appears to expect acknowledgment of these
broadcast messages to confirm the client is actively processing them.

## References

- [AirTouch 2 Communication Protocol](https://github.com/nathanvdh/airtouch2-python/blob/master/docs/AirTouch2_Communication_Protocol.pdf) - Official protocol documentation
- Live testing with AirTouch 2+ controller hardware
