# self-driving-lab

## What this is

This repository runs **reproducible academic campaigns**. It automates the next-step proposal, the operator gate, execution, and the stored result as far as the bench allows. The researcher still reconfigures the lab: a new instrument, a new workflow, and a new campaign are ordinary work.

A later reader should be able to reconstruct a campaign from `runs/<id>/`, the accept/reject judgment, and a citation of the instrument method. The full boundary is the [charter](docs/project/charter.md). Which campaign is open is the [scoreboard](docs/project/README.md).

## What you can change

| Change | Where it lives |
| --- | --- |
| Add or swap an instrument | An instrument operating procedure in its own repo, plus an adapter here. The LS 55 IOP is [spectrometer-lab](https://github.com/fractalclockwork/spectrometer-lab). Physical attach is [CEDE](https://github.com/fractalclockwork/cede). Wire protocols stay out of campaign SOPs. |
| Add a workflow | An SOP under [`src/sdl/orchestration/`](src/sdl/orchestration/). SOPs call adapters. |
| Collect a result | `runs/<id>/` (`state.json`, `events.jsonl`) and `runs/catalog.json` on the Dev-Host. A live judgment also has `runs/<id>/REPORT.md`. |

## What a campaign does

The loop in the [layer map](docs/project/architecture.md) is propose, operator gate, execute, persist. Fixture mode is the offline path and needs no live hardware. A live step needs a person who can see the bench.

## Campaigns in this tree

- [Water Raman](docs/project/procedures/water_raman.md) — first LS 55 loop. The first live record is the tap-water series [`20261113-214920`](runs/tap_water_raman_20261113-214920/REPORT.md).
- [Tonic dilution / IFE](docs/project/procedures/tonic_dilution.md) — adaptive dilution reference already in the tree.
- [Prep-area dimensional](docs/project/procedures/prep_area_dimensional.md) — Marlin gantry and Logitech C310. The printable card is under [`docs/project/calibration/`](docs/project/calibration/).

## Stack map

| Dossier layer | Module |
| --- | --- |
| Integration | [`src/sdl/integration/ls55_client.py`](src/sdl/integration/ls55_client.py) |
| Analytical metrology | spectrometer-lab FastAPI (`/api/*`) |
| Physical / continuous embedded | [CEDE](https://github.com/fractalclockwork/cede) Dev-Host + cede-gateway (Phase 7); lab LAN proposal: [`docs/project/procedures/lab_network_gateway.md`](docs/project/procedures/lab_network_gateway.md) |
| Sample prep | Operator prompts ([charter](docs/project/charter.md) for robotics) |
| AI/ML decision | [`src/sdl/decision/policy.py`](src/sdl/decision/policy.py) (`ClipSNRDilutionPolicy`; BayBE is [parked](docs/project/backlog.md)) |
| Orchestration | [`src/sdl/orchestration/`](src/sdl/orchestration/) |
| Data backbone | [`src/sdl/data/store.py`](src/sdl/data/store.py) → `runs/` |

## Quick start

```bash
uv sync --all-extras
uv run pytest -q

# Stage 0 HIL attach (fixture / no hardware)
uv run python tools/instrument_hil_bringup.py --fixture

# Printable prep-area ChArUco (Dev-Host; optional --extra calibration to regenerate)
# docs/project/calibration/prep_area_charuco_{letter,a4}.pdf

# Offline closed loop (no instrument)
uv run python examples/run_tonic_campaign.py --mode fixture

# Live / spectrometer-lab console (start dashboard first on :8055)
uv run python examples/run_tonic_campaign.py --mode http --interactive
```

Cohort HIL (LS 55 identity + Marlin M115 + C310 capture): [`docs/project/procedures/instrument_hil_bringup.md`](docs/project/procedures/instrument_hil_bringup.md) (`uv sync --extra hil`). Run from the Dev-Host; C310 frames default to `runs/hil_<utc>/c310.jpg` (gateway `/tmp` is temporary only).

Campaign artifacts land under `runs/<campaign_id>/` (`state.json`, `events.jsonl`) and `runs/catalog.json` on the Dev-Host.

## Operator-first safety

Same gates as spectrometer-lab: `gate_a_pass`, compartment closed, Xe OFF idle, abort. Those flags are human claims about the bench. A green fixture run is not permission to energize the lamp or move an axis. Scripts may drive the HTTP API; the operator retains arming and abort authority. Live judgments get a `runs/<id>/REPORT.md`. Permission detail: [`docs/project/charter.md`](docs/project/charter.md).

## Read next

- [Project record](docs/project/README.md) — status scoreboard
- [Charter](docs/project/charter.md) — purpose, scope, permission
- [Architecture](docs/project/architecture.md) — layer map
- [Prior art](docs/project/research.md)
- [Procedures](docs/project/procedures/)
