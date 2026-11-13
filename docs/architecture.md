# Architecture

Level-4 custom control (dossier / Rigaku tier language): this repo owns orchestration, decision, and Python logic; spectrometer-lab owns the LS 55 instrument IOP; **CEDE** owns continuous embedded development and the gateway physical attach plane.

## Layers

```
+-----------------------------------------------------------------+
| Data Backbone — runs/<id>/state.json + events.jsonl + catalog   |
+-----------------------------------------------------------------+
| Orchestration — CampaignRunner (+ WaterRamanSOP next; tonic later) |
+-----------------------------------------------------------------+
| Integration — LS55HttpClient / FixtureLS55Client                |
+----------+-----------------+---------------+----------+---------+
| Decision | Sample prep     | (future)      | (future) | Metrology
| Policy   | Operator prompt | Synthesis     | Robotics | LS 55 API
+----------+-----------------+---------------+----------+---------+
| Physical / continuous embedded — CEDE Dev-Host + cede-gateway   |
|   build → deploy → validate; by-id serial / UVC attach          |
+-----------------------------------------------------------------+
```

| Dossier key | Implementation |
| --- | --- |
| `integration` | `sdl.integration.ls55_client` — HTTP to `/api/connect|setup|single-read|scan|review/recompute|state|abort|shutter/off` |
| `analytical_metrology` | spectrometer-lab `LS55Service` (scout `$RD`, scan `$SC`, review peak/SNR/clip) |
| `physical_control_plane` | **[CEDE](https://github.com/fractalclockwork/cede)** Dev-Host + cede-gateway — toolchains, flash/sync, stable USB/serial/V4L attach, discovery; DS-7 lifecycle `build` / `deploy` / `validate` / `debug`. See CEDE [DEV_OP Phase 7](https://github.com/fractalclockwork/cede/blob/main/docs/DEV_OP.md), [DS-7 / DS-17](https://github.com/fractalclockwork/cede/blob/main/docs/DESIGN_SPECIFICATION.md), and peer landscape [`docs/vendor/continuous_instrument_development.md`](vendor/continuous_instrument_development.md). |
| `sample_prep` | OperatorGate prompts (“dilute N× and load”); no liquid handler in v1 |
| `ai_ml_decision` | `DecisionEngine` protocol; `ClipSNRDilutionPolicy` rules; BayBE can implement the same protocol later |
| `orchestration` | `CampaignRunner` loop: propose → gate → execute → persist |
| `data_backbone` | `CampaignStore` filesystem provenance |
| `robotics_handling` / `synthesis_prep` | Deferred (**Stage 5** / out of scope); see [`docs/roadmap/instrument_bringup.md`](roadmap/instrument_bringup.md) |

### Boundary

| Layer | Owns | Does not own |
| --- | --- | --- |
| **self-driving-lab** | SOPs, policy, campaign state, HTTP adapters | Wire protocols, G-code, V4L capture, MCU flash |
| **Instrument repos** | IOP, abort / idle-safe, acquisition | Campaign policy; gateway OS / by-id contracts |
| **CEDE** | Toolchains, flash/sync, by-id serial & UVC nodes, access groups (`dialout` / `video`) | Spectrometer protocol, Marlin G-code, campaign policy |

**Live path:** adapter → IOP service → **cede-gateway device node** (not Dev-Host USB by default for bench instruments). First bridge cohort: **LS 55** (Prolific USB–RS232; bringup [water Raman](use_cases/water_raman.md), later [tonic dilution / IFE](use_cases/tonic_dilution.md)) and **Marlin gantry + Logitech C310** (Mega CDC + UVC; [prep-area dimensional metrology](use_cases/prep_area_dimensional.md)).

## Loop

1. **Predict / Select** — policy emits `ExperimentProposal` from `CampaignState` + last `MeasurementResult`.
2. **Operator gate** — human ack (or `AutoAckGate` in fixture mode).
3. **Experiment** — SOP calls the LS 55 client; metrics are normalized (`peak_nm`, `peak_intensity`, `snr`, `clipped`, `overload`).
4. **Update** — accepted scans append surrogate points; store writes JSONL + state snapshot.

## Integration contract

SOPs never parse RS-232. The adapter normalizes spectrometer-lab JSON into `MeasurementResult`. Offline CI uses `FixtureLS55Client` (synthetic linear + IFE + clip response). Live runs point `LS55HttpClient` at `http://127.0.0.1:8055`; the IOP opens the instrument serial path on the gateway when running on the Pi bench.

## Safety

Connect requires `gate_a_pass` and `compartment_closed`. Campaign shutdown calls shutter-off. Abort remains available on the instrument console / `/api/abort`. CEDE guarantees stable attach and OS access groups only; arming, idle-safe, and abort semantics stay on the IOP / SDL side.
