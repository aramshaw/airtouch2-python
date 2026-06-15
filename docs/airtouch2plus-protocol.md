# AirTouch 2+ Extended Protocol Notes

Reference for the undocumented messages the AirTouch 2+ controller sends beyond
the original AirTouch 2 protocol. Everything marked **[verified]** was confirmed
against a live controller (firmware on a single‑AC, 8‑zone Polyaire "Atch2PM"
unit) in June 2026; **[unverified]** items come from earlier reverse‑engineering
notes and have not yet been reproduced on the wire.

This supersedes the older `re_response/airtouch2plus_protocol_notes.md`, which
contained contradictions (notably labelling the console‑temperature sensors as
"system counters").

## Transport

- TCP, controller listens on **port 9200**. **[verified]**
- A client connects and immediately requests state by sending an (empty) group
  status and AC status message; the controller replies with the current state.
  **[verified]**
- A client that connects but fails to acknowledge certain broadcasts (see
  [ACK requirements](#acknowledgement-requirements)) gets silently dropped: the
  controller stops responding on that TCP session. Recovery is a new connection;
  worst case the controller needs a power cycle. **[verified]**

## Message framing

```
55 55 | A0 A1 | ID | TY | LEN_HI LEN_LO | <data … LEN bytes> | CRC_HI CRC_LO
 0  1    2  3    4    5     6      7        8 …                  last two
```

| Bytes | Field | Notes |
|------:|-------|-------|
| 0–1 | Magic | always `55 55` |
| 2–3 | Address | **received:** `B0`(self) `80`(normal) / `90`(extended). **sent:** `80`/`90` then `B0`. See ACK note for the `C0` special case. |
| 4 | Message ID | arbitrary; the controller echoes it |
| 5 | Message type | `C0` control/status, `1F` extended, `27` power |
| 6–7 | Data length | big‑endian |
| 8…  | Data | length per bytes 6–7 |
| last 2 | CRC | CRC‑16/MODBUS over **byte 2 → end of data** (i.e. `crc16(frame[2:-2])`) |

The CRC was already correct in the upstream library — the only change needed to
*send* messages was adding `Message.to_bytes()`. **[verified]**

### Control/status sub‑framing (message type `0xC0`)

The data of a `0xC0` message starts with an 8‑byte sub‑header:

```
ST 00 | NLEN(2) | RLEN(2) | RCNT(2) | <normal data NLEN bytes> | <RCNT × RLEN repeat blocks>
 0  1    2  3      4  5      6  7       8 …
```
`ST` = sub‑type. `NLEN` = normal‑data length, `RLEN` = repeat‑block length,
`RCNT` = repeat count. (All big‑endian.)

## Message catalogue

| Type / sub‑type | Name | Direction | ACK? | Status |
|---|---|---|---|---|
| `C0`/`23` | AC status | ← | no | supported upstream |
| `C0`/`21` | Group (zone) status | ← | no | supported upstream **[verified]** |
| `1F`/`11` | AC ability (brand/caps) | ← | no | supported upstream |
| `1F`/`12` | Group names | ← | no | supported upstream |
| `C0`/`2B` | Extended status (console temps, favourite availability) | ← | **yes** | **[verified]** |
| `C0`/`45` | Identity broadcast | ← | **yes** | **[verified]** |
| `27` | System power on/off | ← | no | **[verified]** |
| `C0`/`31` | Favourite status (names + active) | ← | no | **[unverified]** — never seen live |
| `C0`/`40` | Zone status | ← | (doc says yes) | **[unverified]** — never seen live |
| `C0`/`10` | AC status extended | ← | (doc says yes) | **[unverified]** — never seen live |

### `C0`/`2B` — Extended status **[verified]**

Sent unsolicited; ~every 30 s while the system is being interacted with, sparse
(minutes) when idle. **Must be acknowledged.** Carries `RCNT` 4‑byte sensor
blocks (`NLEN`=0, `RLEN`=4):

```
block = ID VAL FLAG_HI FLAG_LO
```

Example (real capture):
```
2b 00 00 00 00 04 00 06   80 80 07 ff  81 81 07 ff  82 82 07 ff  83 83 07 ff   90 ff 02 c5   91 ff 07 ff
└ sub-header: NLEN0 RLEN4 RCNT6        └── favourite availability ──┘          └ console0 ┘  └ console1 ┘
```

- **`0x80`–`0x83` = favourite availability.** When `ID == VAL` the favourite slot
  is configured. Above, all four are available (the test system has 4
  favourites). These bytes do **not** change when you switch between favourites —
  only when favourites are added/removed. **[verified]**
- **`0x90`/`0x91` = console (touchscreen) temperatures.** `FLAG_HI:FLAG_LO` is a
  16‑bit value; `temperature °C = (value − 512) / 10`. `0x07FF` = no sensor
  present. Above, console 0 = `0x02C5` → 19.7 °C, console 1 absent. Confirmed by
  watching the value track room temperature (`02:c4→02:c9` over a session) and a
  community finding. **[verified]**  *(The old notes wrongly called these "system
  counters".)*

**ACK:** `2B 00 00 01 00 00 00 00 00` as a `0xC0` message (see below).

### `C0`/`45` — Identity broadcast **[verified]**

Payload contains the ASCII string `Polyaire … Atch2PM` ("AirTouch 2 Plus
Module"). Seen a few minutes after connect (the old notes' "every ~13–24 h" is
not reliable). **Must be acknowledged.**

**ACK:** `45 00 00 01 00 00 00 00 00` as a `0xC0` message.

### `27` — System power **[verified]**

Top‑level message type (not a `0xC0` sub‑type). One data byte: `01` = on,
`00` = off. No ACK required; just recognise it so it isn't logged as unknown.

Example header: `55 55 b0 80 01 27 00 01`, data `00`.

### `C0`/`31` — Favourite status **[unverified]**

Per the earlier notes this carries the favourite **names** and the **active**
favourite, and "is sent when the active favourite changes". **However, across
~25 minutes and repeated panel favourite‑switches it was never observed** — the
switches only surfaced as `0x21` zone changes. Hypothesis: `0x31` is
**request‑only** (the official app likely subscribes to it). Resolving this is
the main open task for favourite support.

Documented format (from the earlier notes, **unverified**):
```
31 00 | NLEN=0002 | RLEN=000B | RCNT=0004 | <active selector 2B> | 4 × 11-byte favourite blocks
```
- Active selector byte 0 is a bitmap: `01`=fav0, `02`=fav1, `04`=fav2, `08`=fav3.
- Favourite block: `ID(1) | name(8 ASCII, null-padded) | unknown(2)`.

The library's `FavouriteStatus.py` parser already matches this format; what's
missing is a live `0x31` to feed it.

### `C0`/`21` — Group (zone) status **[verified]**

8‑byte blocks per zone. Byte 0: bit 6 (`0x40`) = power on, low nibble = zone id.
Byte 1: target damper %. Byte 3: current damper %. Activating a favourite
re‑writes these (which is how favourite changes are observed today).

## Acknowledgement requirements

- Only `0x2B` and `0x45` need acknowledging (**[verified]**). The earlier notes
  also list `0x10`/`0x40`, but those were never observed on the test system, so
  they are not handled.
- The ACK is a minimal control/status message echoing the sub‑type:
  `ST 00 00 01 00 00 00 00 00` (sub‑header with `NLEN`=1, plus one `00` payload
  byte).
- **Address:** these ACKs are sent with the control/status identifier `0xC0` in
  address byte 2 (i.e. `Header(0xC0, CONTROL_STATUS, …)`), giving a frame like
  `55 55 c0 b0 01 c0 00 09 …`. This is the value the proven implementation uses;
  whether the usual client address (`0x80`) would also be accepted has **not**
  been tested. **[partially verified]**
- **No rate‑limiting / cooldown is needed.** An earlier implementation
  rate‑limited duplicate ACKs; this was only a development‑time crutch.

## Open questions

- How does a client get `0x31` (favourite names + active)? Likely a request /
  subscription the official app sends. Needed for favourite read/select support.
- Activating a favourite from the network (write) — control message unknown.
- `0x10` / `0x40` semantics and whether they ever require ACKs on other systems.
- Whether `0x80` is accepted in place of `0xC0` for `0x2B`/`0x45` ACKs.

## Provenance

Live captures from controller `192.168.4.45:9200`, June 2026, recorded with
`tools/probe.py` (a listen‑and‑ACK probe built on the proven client). Raw
samples and per‑message logs are under `captures/`.
