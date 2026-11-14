# self-driving-lab

Academic campaign host around standalone instrument IOPs: orchestration, decision, and a reproducible `runs/` record. Instrument ownership stays in [`spectrometer-lab`](https://github.com/fractalclockwork/spectrometer-lab); physical attach stays in [`cede`](https://github.com/fractalclockwork/cede).

Goals, scope, status, and permission: [`docs/project/README.md`](docs/project/README.md).

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

Layer map: [`docs/project/architecture.md`](docs/project/architecture.md). Prior art: [`docs/project/research.md`](docs/project/research.md). Procedures: [`docs/project/procedures/`](docs/project/procedures/).

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
