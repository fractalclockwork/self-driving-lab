# self-driving-lab

Thin **Level-4** open-source self-driving laboratory (SDL) skeleton: orchestration, decision, data backbone, and an LS 55 integration adapter. Instrument ownership stays in [`spectrometer-lab`](https://github.com/fractalclockwork/spectrometer-lab); physical attach and continuous embedded lifecycle (`build` / `deploy` / `validate`) stay in [`cede`](https://github.com/fractalclockwork/cede); this repo closes the science loop around them.

**LS 55 bringup (next):** [water Raman](docs/use_cases/water_raman.md) — distilled-water O–H band (~397 nm) as a simple Stage 3 connect/setup/scan/accept loop.

**LS 55 later (Stage 4):** [tonic dilution / IFE](docs/use_cases/tonic_dilution.md) — adaptive dilute / remeasure / scan / stop (SOP + policy already exist as reference).

**Gantry (Stage 0):** **Marlin + Logitech C310** prep-area imaging — printable ChArUco card in [`docs/calibration/`](docs/calibration/); frames and vision on the Dev-Host ([bring-up](docs/roadmap/marlin_c310_bringup.md), [use-case](docs/use_cases/prep_area_dimensional.md)).

## Stack map

| Dossier layer | Module |
| --- | --- |
| Integration | [`src/sdl/integration/ls55_client.py`](src/sdl/integration/ls55_client.py) |
| Analytical metrology | spectrometer-lab FastAPI (`/api/*`) |
| Physical / continuous embedded | [CEDE](https://github.com/fractalclockwork/cede) Dev-Host + cede-gateway (Phase 7); lab LAN proposal: [`docs/roadmap/lab_network_gateway.md`](docs/roadmap/lab_network_gateway.md) |
| Sample prep | Operator prompts (no robotics in v1) |
| AI/ML decision | [`src/sdl/decision/policy.py`](src/sdl/decision/policy.py) (`ClipSNRDilutionPolicy`; BayBE later) |
| Orchestration | [`src/sdl/orchestration/`](src/sdl/orchestration/) |
| Data backbone | [`src/sdl/data/store.py`](src/sdl/data/store.py) → `runs/` |

Industry context: [`docs/vendor/landscape.md`](docs/vendor/landscape.md). Continuous instrument peers: [`docs/vendor/continuous_instrument_development.md`](docs/vendor/continuous_instrument_development.md). Architecture: [`docs/architecture.md`](docs/architecture.md). Use-cases: [`water Raman`](docs/use_cases/water_raman.md), [`tonic dilution`](docs/use_cases/tonic_dilution.md) (later), [`prep-area dimensional`](docs/use_cases/prep_area_dimensional.md). Instrument bringup: [`docs/roadmap/instrument_bringup.md`](docs/roadmap/instrument_bringup.md). Lab network gateway (proposal): [`docs/roadmap/lab_network_gateway.md`](docs/roadmap/lab_network_gateway.md). Marlin + C310: [`docs/roadmap/marlin_c310_bringup.md`](docs/roadmap/marlin_c310_bringup.md).

## Quick start

```bash
uv sync --all-extras
uv run pytest -q

# Stage 0 HIL attach (fixture / no hardware)
uv run python tools/instrument_hil_bringup.py --fixture

# Printable prep-area ChArUco (Dev-Host; optional --extra calibration to regenerate)
# docs/calibration/prep_area_charuco_{letter,a4}.pdf

# Offline closed loop (no instrument)
uv run python examples/run_tonic_campaign.py --mode fixture

# Live / spectrometer-lab console (start dashboard first on :8055)
uv run python examples/run_tonic_campaign.py --mode http --interactive
```

Cohort HIL (LS 55 identity + Marlin M115 + C310 capture): [`docs/roadmap/instrument_hil_bringup.md`](docs/roadmap/instrument_hil_bringup.md) (`uv sync --extra hil`). Run from the Dev-Host; C310 frames default to `runs/hil_<utc>/c310.jpg` (gateway `/tmp` is temporary only).

Campaign artifacts land under `runs/<campaign_id>/` (`state.json`, `events.jsonl`) and `runs/catalog.json` on the Dev-Host.

## Operator-first safety

Same gates as spectrometer-lab: `gate_a_pass`, compartment closed, Xe OFF idle, abort. Scripts may drive the HTTP API; the operator retains arming and abort authority.

## Out of scope (v1)

ChemOS/AlabOS/IvoryOS adoption, SiLA 2 / OPC UA, Gate D hardware qualification, and **Stage 5** unattended robotics (gantry/autosampler as sample-prep actuator). Fixture mode works without Gate D; bench claims wait on seating. Multi-instrument ladder and Marlin+C310 north star: [`docs/roadmap/instrument_bringup.md`](docs/roadmap/instrument_bringup.md).
