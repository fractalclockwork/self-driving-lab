# Automated academic research (this lab)

Scope, status, and permission: [project record](../README.md). This page maps a seven-phase academic lifecycle onto the repos we already have. Purpose and the repo split: [charter](../charter.md). If this page disagrees with the charter on scope or permission, the charter wins.

## Dual loop

Permission, including the tap-water worked case: [charter](../charter.md#dual-loop-permission).

## Phase map

| Phase | Academic intent | This lab now | Later |
| --- | --- | --- | --- |
| **1 — Design** | Bounding box and a versioned SOP | Use-cases: [water Raman](water_raman.md) ([OBJ-1](../objectives.md#obj-1)), [tonic](tonic_dilution.md) ([OBJ-2](../objectives.md#obj-2)), [prep-area dimensional](prep_area_dimensional.md) ([OBJ-3](../objectives.md#obj-3)). Live LS 55 box: Ex 350 nm, Em 380–420 nm, 10 nm slits, sample identity owned here (tap vs distilled). | Machine-readable SOP when `WaterRamanSOP` lands in this repo |
| **2 — Modular development** | Hardware and orchestration can move independently | **Repo separation:** spectrometer-lab IOP, CEDE attach, SDL orchestration + `FixtureLS55Client`. Mock endpoint is the fixture client. Contract is HTTP `:8055`. CLI invoke is temporary and is not a second protocol. | Containers per instrument: [charter](../charter.md#outside-this-baseline) |
| **3 — Integration** | Orchestrator calls nodes; humans can pause a shared instrument | `CampaignRunner` + `OperatorGate`. The operator loads the sample. Shared-instrument pause is that gate. | Gantries and unattended transfer: [charter](../charter.md#outside-this-baseline) |
| **4 — Telemetry** | Failures are visible before the next physical step | Campaign `runs/` plus a human `REPORT.md` beside every live judgment (tap water, gantry ChArUco). Watchdog is IOP idle-safe (Xe OFF, axes stopped) and abort. | Grafana and a lab-wide sensor bus: [charter](../charter.md#outside-this-baseline) |
| **5 — Data** | Context survives the student who took the data | Raw spectra and plots stay with the run. Decisions use normalized fields (`peak_nm`, `snr`, `clipped`). Tag the run with the IOP git commit when the sidecar has one, the SDL sample label (the IOP sidecar may still say “distilled water”), and the method settings. | Cold storage and a database |
| **6 — Iteration** | The hypothesis can change without tearing down the stack | The next campaign and the docs change. Tonic / BayBE: [OBJ-2](../objectives.md#obj-2) and the [backlog](../backlog.md). Slit and emission window stay as written in the water-Raman use-case. | An agent rewriting a live SOP: [charter](../charter.md#outside-this-baseline) |
| **7 — Publication** | The environment and the judgment travel with the result | Run directory plus the method citation: spectrometer-lab water-Raman procedure; distilled series `20261103-1629` remains the wavelength reference. | Notebooks and FAIR export after a series that passes its accept rule |

## Scope

Project scope is the [charter](../charter.md).

## Related

- Project record: [`docs/project/README.md`](../README.md)
- Architecture (layer map): [`docs/project/architecture.md`](../architecture.md)
- Instrument ladder: [`instrument_bringup.md`](instrument_bringup.md)
- First live comparison: [`runs/tap_water_raman_20261113-214920/REPORT.md`](../../../runs/tap_water_raman_20261113-214920/REPORT.md)
