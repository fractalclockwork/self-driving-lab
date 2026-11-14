# Instrument HIL bring-up (LS 55 + Marlin + C310)

Stage **0** attach attestation for the first CEDE cohort used by this repo. Probes the LS 55 over **RS-232** via spectrometer-lab’s read-only identity dump, pings Marlin with **M115**, and **activates** the Logitech C310 with a one-shot capture. No Xe energize, no gantry motion, no campaign SOP. The spectrometer-lab **GUI / dashboard** (FastAPI `:8055`) is Stage 1 unsigned / on hold — HIL does **not** use `GET /api/state`.

Implementation: [`tools/instrument_hil_bringup.py`](../../../tools/instrument_hil_bringup.py) → [`src/sdl/hil/bringup.py`](../../../src/sdl/hil/bringup.py).

## Inventory (CEDE Phase 7)

| Device | Typical path | Probe |
| --- | --- | --- |
| LS 55 | `/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller*` on cede-pi | `dump_instrument_identity.py` (9600; Xe OFF; model/revision e.g. `55.F1`) |
| Marlin (Mega) | `/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_*` | `M115` |
| Logitech C310 | `/dev/v4l/by-id/*` preferred, else `/dev/video0` | one JPEG/raw frame |

CEDE owns gateway attach contracts; this tool does **not** live in CEDE (Phase 7: no instrument protocol / `hw-smoke` unchanged). Requires a spectrometer-lab checkout with `uv` on the host that opens the Prolific port (`SPECTROMETER_LAB_ROOT`, default `~/src/spectrometer-lab`).

**Canonical runner is the Dev-Host.** Durable C310 frames land under `runs/hil_<utc>/c310.jpg`. With `--ssh-gateway`, capture is written to gateway `/tmp`, copied to that Dev-Host path, then deleted on the gateway. Pi-local HIL is attach smoke only — not the campaign store. Image processing stays on the Dev-Host (see [`marlin_c310_bringup.md`](marlin_c310_bringup.md)).

## Run

```bash
uv sync --extra hil --extra dev

# CI / no hardware
uv run python tools/instrument_hil_bringup.py --fixture

# Dev-Host (preferred): all three probes on gateway
uv run python tools/instrument_hil_bringup.py \
  --ssh-gateway pi@cede-pi.local \
  --spectrometer-lab-root ~/src/spectrometer-lab

# On cede-pi only for attach smoke (USB nodes + spectrometer-lab local; not durable store)
uv run python tools/instrument_hil_bringup.py

# Skip a check
uv run python tools/instrument_hil_bringup.py --fixture --skip marlin
```

Overrides: `LS55_PORT`, `MARLIN_PORT`, `VIDEO_DEVICE`, `SPECTROMETER_LAB_ROOT`, `--ls55-port`, `--marlin-port`, `--video-device`, `--camera-out` (default `runs/hil_<utc>/c310.jpg`), `--marlin-baud` (default 250000).

Exit `0` if all enabled checks PASS/SKIP; otherwise `1` with a `[PASS|FAIL|SKIP]` summary. LS 55 PASS detail includes `firmware=<model>.<revision>`.

## Safety

- LS 55: spectrometer-lab **identity dump only** (`--gate-a-pass --compartment-closed`; forces Xe OFF; no `$RD`/`$SC`).
- Marlin: **M115 only** (no `G0` / home).
- Camera: single frame via `fswebcam` or `v4l2-ctl` (must be on PATH on the capture host); gateway file is temporary.

## Related

- Ladder: [`instrument_bringup.md`](instrument_bringup.md)
- Marlin + C310 + ChArUco: [`marlin_c310_bringup.md`](marlin_c310_bringup.md)
- spectrometer-lab identity CLI: `scripts/dump_instrument_identity.py`
- CEDE inventory: [DEV_OP Phase 7](https://github.com/fractalclockwork/cede/blob/main/docs/DEV_OP.md)
