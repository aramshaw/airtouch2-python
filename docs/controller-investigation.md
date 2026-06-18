# AirTouch 2+ — connection-reliability investigation: findings & conclusion (2026-06-18)

## Conclusion
The recurring "becomes unavailable" is a **controller-side firmware lockup**, not
an integration bug. Proven by the long-used old code hanging identically on the
current controller.

## Two distinct failure modes (these were initially conflated)
- **A — ACK-lockout dropout** *(SOLVED)*: the controller drops the TCP session if
  the client doesn't ACK its undocumented `0x2B`/`0x45` broadcasts. Fixed by the
  ACK support in this library. This was the original "becomes unavailable" bug.
- **B — Controller firmware network hang** *(not fixable in software)*: the
  controller's whole network stack freezes every ~1–3 h, refusing ALL clients
  (Home Assistant + the official app) while the wall panel keeps working.
  Self-recovers in ~45 min–3 h, or persists until restart. Independent of the client.

The old code fixed A (it ACKed) and was blind to B (no "unavailable" state, plus
the controller self-recovers) — which is why B went unnoticed for so long.

## Evidence that B is controller-side
1. Disabling TCP keepalive (build v0.3.3) changed nothing — eliminated.
2. Every controller message was ACKed 100% (byte-identical, correct CRC); zero
   unknown-type warnings; no "hammering" — ACK coverage eliminated.
3. Signature: the `0x2B` heartbeat *stretches* (30 s → minutes) then goes silent —
   the controller slowing/freezing, not reacting to client traffic.
4. During a hang, a neutral machine can't even ICMP-ping the controller — a TCP
   client cannot cause that.
5. The official phone app is locked out too (runs none of our code).
6. **The old code (baseline build v0.4.0) hangs identically** — 3 resets in ~5 h,
   same heartbeat-stretch-then-freeze, self-recovering ~45 min.

## Delivered (software goals — all met)
- Connection-dropout fix (ACK `0x2B`/`0x45`) — problem A solved.
- Favourites read + write (`0x31` request, `0x30` activate).
- Console/touchscreen temperature sensor.
- Clean TDD commits + live-verified protocol doc (`airtouch2plus-protocol.md`).
- Graceful handling: entities go *unavailable*; client auto-recovers when the
  controller un-hangs (no manual restart needed for self-recovering hangs).

## Controller hang — characteristics
- Frequency ~1–3 h (variable); affects all network clients; wall panel unaffected.
- Recovery: self-recovers (~45 min–3 h) or persists until a controller restart.
- Firmware at time of investigation: **Console 1.2.4, Main Module 2.2.0.2**.

## Mitigations (controller is hard-wired — no power-cycle option)
- **Resilient morning automation**: retry AC-on every few minutes over a window
  until it actually turns on (the client auto-reconnects once the controller
  recovers), so a transient hang doesn't silently skip the morning start.
- **Firmware / Polyaire**: check for a firmware update; report the network-stack
  hang to Polyaire.
- Run **v0.3.3** (full features + graceful recovery) as the daily build.
