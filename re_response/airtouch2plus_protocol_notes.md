# AirTouch2+ Extended Protocol Documentation

## Overview

This document describes additional protocol messages discovered in AirTouch2+ controllers that extend beyond the standard documented protocol. These messages were reverse-engineered from live controller communications and cross-referenced with available AirTouch2 protocol documentation.

## Background

The AirTouch2+ controller sends several undocumented message types that must be properly acknowledged to maintain stable communication. Without proper handling of these messages, the controller may refuse new connections from both Home Assistant integrations and mobile applications.

## Message Types Identified

### Control Status Messages (0xC0)

#### 0x10 - AC Status Extended

**Purpose**: Provides extended AC status information beyond the standard 0x23 AC Status message.

**Structure**:
```
Byte 0: 0x10 (Message subtype)
Byte 1: 0x00 (Reserved)
Bytes 2-7: Standard control status subheader
Byte 8: AC ID
Byte 9: Status byte (bit 7 = power on/off)
Byte 10: Mode and fan speed (lower 4 bits = mode, upper 4 bits = fan)
Byte 11: Additional flags
Byte 12: Temperature value (divide by 10 for actual temperature)
```

**Correlation**: Maps to offsets 0x162-0x163 in AirTouch2 documentation (AC1/AC2 status)

**Required Acknowledgment**:
```
2B 00 00 02 00 00 00 00 00 00
```

#### 0x2B - Extended Status

**Purpose**: System status including available favorites, timers, and system counters.

**Structure**:
```
Byte 0: 0x2B (Message subtype)
Byte 1: 0x00 (Reserved)
Bytes 2-7: Standard control status subheader
Byte 8: Number of entries
Byte 9: Number of sections
Bytes 10+: Repeating 4-byte sections:
  - Byte 0: ID (0x80-0x83 = favorites, 0x90-0x91 = system counters)
  - Byte 1: Value
  - Bytes 2-3: Flags/counter data
```

**Favorites Section (0x80-0x83)**:
- ID byte matches value byte when favorite is available
- Flags provide additional status information
- Favorite 0 = 0x80, Favorite 1 = 0x81, etc.

**System Counters (0x90-0x91)**:
- System status and operational counters
- Flags contain 16-bit counter values

**Correlation**: Relates to timer offsets 0x15A-0x161 in AirTouch2 documentation

**Required Acknowledgment**:
A simple 1-byte payload is required.
```
2B 00 00 01 00 00 00 00 00
```
**Note**: This acknowledgment requires a special header address of `0xC0` instead of the standard `0x80`.

#### 0x31 - Favorite Status

**Purpose**: Provides names and active status of configured favorite scenes.

**Structure**:
```
Byte 0: 0x31 (Message subtype)
Byte 1: 0x00 (Reserved)
Bytes 2-7: Standard control status subheader (typically 00 02 00 0B 00 04)
Byte 8: Active selector (bitmap indicating which favorite is active)
Bytes 9+: Favorite entries
```

**Active Selector Bitmap**:
- Bit 0 (0x01): Favorite 0 active
- Bit 1 (0x02): Favorite 1 active  
- Bit 2 (0x04): Favorite 2 active
- Bit 3 (0x08): Favorite 3 active

**Favorite Entry Format**:

*Favorite 0 (special case - no ID byte)*:
```
Status Byte | Separator | Name Bytes | Null Padding
```

*Favorites 1-3*:
```
Status Byte | Separator | Favorite ID | Name Bytes | Null Padding
```

**Example Parsing**:
```
31:00:00:02:00:0b:00:04:01:08:00:6d:61:69:6e:00:00:00:00:1b:00:01:67:79:6d:00:00:00:00:00:00
│                            │  │  │  └─────────┘                │  │  │  └───────────┘
│                            │  │  │    "main"                   │  │  │    "gym"  
│                            │  │  │                             │  │  │
│                            │  │  └─ separator                  │  │  └─ favorite ID (1)
│                            │  └─ status byte                   │  └─ separator
│                            └─ active selector (0x01 = fav 0)   └─ status byte
└─ message header
```

**Required Acknowledgment**:
```
31 00 00 01 00 00 00 00 00
```

#### 0x40 - Zone Status

**Purpose**: Provides zone control percentages and status.

**Structure**:
```
Byte 0: 0x40 (Message subtype)
Byte 1: 0x00 (Reserved)
Bytes 2-7: Standard control status subheader
Bytes 8+: Repeating 8-byte zone blocks:
  - Byte 0: Zone ID
  - Byte 1: Percentage value
  - Bytes 2-7: Additional zone flags/status
```

**Correlation**: Maps to zone percentage offsets 0x114-0x123 in AirTouch2 documentation

**Required Acknowledgment**:
```
40 00 00 01 00 00 00 00 00
```
#### 0x45 - System Identity Broadcast

**Purpose**: Broadcasts system identity information. The payload contains the string "Polyaire Atch2PM", likely identifying the manufacturer and "AirTouch 2 Plus Module". This message appears to be sent periodically (e.g., every 13 hours).

**Required Acknowledgment - still testing**:
A simple 1-byte payload is required.
```
45 00 00 01 00 00 00 00 00
```
**Note**: This acknowledgment requires a special header address of `0xC0` instead of the standard `0x80`.

### Unknown Message Types

#### 0x27 - Unknown Message Type

**Purpose**: Unknown function, appears to be short status messages.

**Observed Data**: Simple payloads (typically single bytes like 0x00, 0x01)

**Required Handling**: Log and ignore - no acknowledgment appears necessary.

## Protocol Requirements

### Acknowledgment Format

All control status acknowledgments follow this structure:

```
Header (8 bytes):
  Byte 0: Message subtype (matches incoming message)
  Byte 1: 0x00 (Reserved)
  Bytes 2-3: Normal data length (big-endian)
  Bytes 4-5: Repeat data length (big-endian, typically 0x00 0x00)
  Bytes 6-7: Repeat count (big-endian, typically 0x00 0x00)
  
Data (variable length):
  Minimal response data as specified per message type
```

### Message Header Requirements

- **Address Message Type**: `AddressMsgType.NORMAL` (`0x80`) for most messages.
  - **Exception**: Acknowledgments for message subtypes `0x2B` and `0x45` must use the address `0xC0`. 
- **Message Type**: `MessageType.CONTROL_STATUS` (`0xC0`)
- **CRC16**: Proper MODBUS CRC16 checksum required

### Critical Implementation Notes

1. **Connection Stability**: The controller will refuse new connections if these messages are not properly acknowledged.

2. **Timing**: Acknowledgments should be sent immediately upon receiving these message types.

3. **Error Handling**: Unknown message types should be logged but not cause processing failures.

4. **Enum Handling**: Add these message types to your protocol enums to prevent ValueError exceptions:

```python
class ControlStatusSubType(IntEnum):
    # ... existing values ...
    AC_STATUS_EXTENDED = 0x10
    EXTENDED_STATUS = 0x2B  
    FAVORITE_STATUS = 0x31
    ZONE_STATUS = 0x40

class MessageType(IntEnum):
    # ... existing values ...
    UNKNOWN_27 = 0x27
```

## Implementation Example

```python
async def _send_ack_response(self, msg_type: int):
    """Send protocol-compliant acknowledgment."""
    ack_data: bytes
    if msg_type == 0x2B:  # Extended Status
        ack_data = bytes([0x2B, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
    elif msg_type == 0x45:  # System Identity
        ack_data = bytes([0x45, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
    else:
        # Generic ACK for other subtypes if needed
        ack_data = bytes([msg_type, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    # Create header with correct address
    if msg_type == 0x2B or msg_type == 0x45:
        header = Header(0xC0, MessageType.CONTROL_STATUS, len(ack_data))
    else:
        header = Header(0x80, MessageType.CONTROL_STATUS, len(ack_data))
    
    # Create and send message with proper headers and checksum
    # ... implementation details ...```

## Future Enhancement Opportunities

### Favorite Scene Control
The 0x31 message provides complete favorite scene information that could be used to:
- Display available scenes in Home Assistant
- Show which scene is currently active
- Potentially trigger scene changes (requires further reverse engineering)

### Enhanced Zone Management  
The 0x40 message provides detailed zone status that could enable:
- Individual zone percentage display
- Zone-specific status indicators
- Advanced zone control features

### System Monitoring
The 0x2B message contains system counters and status that could provide:
- System health monitoring
- Usage statistics
- Advanced diagnostics

## References

- AirTouch2 Protocol Documentation (offsets 0x158-0x18A)
- Live protocol captures from AirTouch2+ controller communications
- Reverse engineering analysis of controller behavior

## Changelog

- **Initial Version**: Documented 0x2B, 0x10, 0x31, 0x40, and 0x27 message types
- **Protocol Requirements**: Added acknowledgment format specifications
- **Implementation Guide**: Added code examples and enum definitions