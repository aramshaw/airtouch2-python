# AirTouch 2+ Integration — Session Summary (2026-06-15)

A working record of the session: situation, goals, learnings, gaps and final
status. Companion to [`airtouch2plus-protocol.md`](airtouch2plus-protocol.md)
(the verified wire-protocol reference).

## Situation (where we started)

- An **AirTouch 2+** controller with the goal of reliable Home Assistant control.
- The existing community integration (nathanvdh's `airtouch2-python` library +
  `homeassistant-airtouch2plus`) **kept dropping the connection** ("becomes
  unavailable").
- A prior fix attempt had been opened as
  [PR #16](https://github.com/nathanvdh/airtouch2-python/pull/16) but with **16
  messy commits**; the maintainer declined it (wanted clean commits, had
  unanswered technical objections, and is time-poor).
- The working code was **scattered and contradictory**: broken `master`
  branches, multiple feature branches, a self-contradicting protocol-notes doc,
  and a cludged local deploy.

## Goals

1. Clean up the code (remove dead ends, make it solid, package neatly).
2. Produce **clean, incremental commits** off the maintainer's base for review.
3. Maintain a **fork** if it isn't merged.
4. Add **Favourites** (zone scene presets) to HA.
5. Incorporate the **touchscreen-temperature** finding (mattjamesaus's review).
6. *(Emerged)* Full **read + write** favourite control; a **HACS-installable
   fork** to soak-test before upstreaming.

## What we did & learned

**Established the real source of truth.** Both `master` branches were
broken/stale (the library `master` won't even import). The working code lived on
the `fix-undocumented*` branches — confirmed byte-identical to the actually
deployed code.

**Built a safe live probe** (`tools/probe.py`) that reuses the proven client (so
it ACKs correctly and can't lock the controller) and **captured real protocol
data** from `192.168.4.45:9200`.

**Decoded and verified the protocol live:**

- **Root cause of the dropouts:** the controller silently kills the TCP session
  if the client doesn't **ACK** its undocumented `0x2B` (extended status, ~30 s)
  and `0x45` (identity) broadcasts. The ACK is a minimal control/status message
  sent with the `0xC0` address.
- **The old PR's "checksum fix" was a no-op** (cosmetic). The real enabling
  change was adding `Message.to_bytes()` so ACKs can be *sent*.
- **Touchscreen temperature** (mattjamesaus): carried in `0x2B` at sensor ids
  `0x90`/`0x91`, value `(raw − 512) / 10 °C`, `0x07FF` = no sensor.
- **`0x27`** = system power broadcast (`01`=on / `00`=off), no ACK.
- **Favourites breakthrough:** `0x31` (read) is **request-only** — the
  controller never broadcasts it (why passive listening never saw it).
  Requesting it returns the list + active favourite. `0x30` (write/activate) =
  `[1<<id, 0x08]`. **Both verified live** (main↔gym round trip — active favourite
  and zones followed each command).
- **Maintainer's 3 objections resolved:** rate-limit → dropped (dev crutch),
  `0x10` special-case → dropped (never observed), `0xC0` address → kept (proven;
  `0x80` not tested — documented honestly rather than claimed).

**Rebuilt the library cleanly** on current upstream, TDD throughout — **48
tests**, every change live-verified, including a 15-minute zero-dropout soak.

**Built the HA integration side:** favourite **select** (read + activate) and
console-temperature **sensor**.

**Published a HACS-installable fork** and made it reliable (bundled the library
after `git+https` proved flaky on HA OS).

## Gaps / open items

- **Soak test not yet run** (install v0.3.1, run with debug logging).
- **Unconfirmed:** did the Gym dampers *physically* move on activation?
- **`0xC0` vs `0x80` ACK address** never empirically tested — kept proven `0xC0`.
- **Bundled library = duplicated code** — a library fix during the soak needs a
  re-copy + new release. Long-term: publish to PyPI (or git dep) for upstream.
- **HACS card still shows as the upstream author's** — cosmetic, deferred to
  [issue #1](https://github.com/aramshaw/homeassistant-airtouch2plus/issues/1).
- **Upstream PR: parked** until the soak passes.
- **Protocol unknowns:** the `0x08` byte in the favourite selector; `0x10`/`0x40`
  semantics (never seen on this system).
- **Not built:** local Docker HA (deferred — soak-testing on real HA). The other
  agent's `feature/at2plus-extended-protocol` branch was abandoned as agreed.

## Final status & artifacts

**Library — `aramshaw/airtouch2-python`** (9 commits, 48 tests, pushed on
`feat/at2plus-favourites`):

| Commit | |
|---|---|
| `17ebecd` | `Message.to_bytes()` (enables sending) |
| `2abc397` | recognise `0x27`/`0x2B`/`0x45` |
| `bb4213e` | **ACK `0x2B`/`0x45` — the dropout fix** |
| `9253b3b` | console temperature decode |
| `7b22881` | live-verified protocol doc |
| `844343e` | favourite **read** |
| `65c4c25` | favourite **write** (activate) |
| `2bbd656` | doc: favourites verified |
| `952c1cc` | bump to v0.9.0 |

- Commits 1–5 = the **core** (also on a local `fix/at2plus-undocumented-acks`
  branch) → basis for the eventual upstream PR.
- Commits 6–9 = **favourites + version**, fork-only.

**HA integration — `aramshaw/homeassistant-airtouch2plus`**
(`feat/favourites-and-console-temp`, pushed):

- `30c2444` favourite select + console-temp sensor; `3d30968` bundle the library.
- Releases: **v0.3.1 (current, bundled)**, v0.3.0 (superseded). Issue #1 open.

**Local workspace** — `C:\Users\User\Repos\airtouch-take-2\`: both repo clones,
`.venv`, `tools/probe.py` (with `--request-favourites` / `--activate-favourite`
experiment modes), `captures/` (logs, message JSONL, raw `.bin` fixtures).

**Bottom line:** dropout fix + console temperature + favourites read/write are
**done, tested, and live-verified**, shipped as a HACS-installable preview
(**v0.3.1**). Next: soak-test on real HA with debug logging, then polish the HACS
naming (#1) and prepare the clean upstream PR.

## Next steps

1. Install **v0.3.1** via HACS; enable debug logging for `airtouch2` and
   `custom_components.airtouch2plus`; soak-test.
2. Confirm favourite switching moves dampers; confirm no dropouts over days.
3. Address HACS naming (issue #1) and re-release.
4. Push the `fix/at2plus-undocumented-acks` branch and open the clean upstream
   PR to nathanvdh (core fix only), with the protocol doc as evidence.
