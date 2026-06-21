# AirTouch 2+ project map

Orientation: where everything lives — what's running, what's being contributed
upstream, and how the pieces fit. Update this as things move.

## The two pieces of software

| | What it does | Original (upstream) | Your fork |
|---|---|---|---|
| **Library** (`airtouch2-python`) | Talks to the AirTouch 2+ over the network | `nathanvdh/airtouch2-python` | `aramshaw/airtouch2-python` |
| **Integration** (`homeassistant-airtouch2plus`) | Plugs the library into Home Assistant | `nathanvdh/homeassistant-airtouch2plus` | `aramshaw/homeassistant-airtouch2plus` |

The integration **bundles a copy of the library inside it**, so installing the
integration installs everything — there's no separate library install.

## 🟢 Running on Home Assistant right now

- **`v0.4.2`**, installed via **HACS** from **`aramshaw/homeassistant-airtouch2plus`**.
- Built from branch `feat/favourites-and-console-temp`, with the library bundled in.
- Contains **everything**: dropout fix (ACKs) + keep-alive poll + favourites + console (touchscreen) temperature.
- Status: daily driver — confirmed 3+ days with zero dropouts (from 2026-06-20).

## 🔵 Ready to contribute upstream (the Pull Request)

- Branch **`fix/at2plus-dropout`** in **`aramshaw/airtouch2-python`** (the library), based on `nathanvdh`'s `master`.
- Contains **only the dropout fix** — a clean 3-commit slice:
  1. nathanvdh's own ACK commit (kept, credited to him)
  2. `fix:` ACK address `0x80` → `0xC0` (with the spam-storm evidence)
  3. `feat:` keep-alive poll (the idle-timeout fix)
- Pushed to your fork; **PR #18 open** → https://github.com/nathanvdh/airtouch2-python/pull/18

## Mental model

> Home Assistant runs your **full fork** (everything, bundled). The PR is a
> **clean slice of just the fix**, offered back to the original author.
> Favourites + console temp stay in your fork and become **follow-up PRs** later.

## Roadmap

- [x] Diagnose the dropout (root cause: ~16-min controller idle timeout)
- [x] Fix it (keep-alive poll) and verify (3+ days, zero dropouts)
- [x] Curate the clean dropout-fix branch for upstream
- [x] Open the dropout-fix PR → https://github.com/nathanvdh/airtouch2-python/pull/18 (2026-06-22)
- [ ] Follow-up PRs: favourites (read/write), console temperature
- [ ] Integration-side PR(s) to nathanvdh's HA repo once the library lands

## Key facts worth remembering

- **The dropout was the controller, not our code** — the long-used old code drops the same way; the keep-alive poll prevents it.
- **The ACK must use `0xC0`** in the address byte (tested: `0x80` triggers a continuous broadcast spam storm).
- Deeper reference docs (this repo): `docs/airtouch2plus-protocol.md` (protocol), `docs/controller-investigation.md` (the full diagnosis).

## On disk (this machine)

- Library: `C:\Users\User\Repos\airtouch-take-2\airtouch2-python`
- Integration: `C:\Users\User\Repos\airtouch-take-2\homeassistant-airtouch2plus`
- Probe + tools: `C:\Users\User\Repos\airtouch-take-2\tools`
