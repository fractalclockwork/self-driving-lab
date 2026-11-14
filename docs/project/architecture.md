# Architecture

This repo owns campaign chemistry, SOPs, policy, and `runs/`. spectrometer-lab owns the LS 55 instrument IOP. **CEDE** owns continuous embedded development and the gateway physical attach plane. The same split in Rigaku tier language is [prior art](research.md).

Scope, status, and permission: [project record](README.md). This page is the layer map. If it disagrees with the [charter](charter.md) on scope or permission, the charter wins.

## Layers

```
+-----------------------------------------------------------------+
| Data Backbone — runs/<id>/state.json + events.jsonl + catalog   |
+-----------------------------------------------------------------+
| Orchestration — CampaignRunner (SOP per the project objectives) |
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
| `physical_control_plane` | **[CEDE](https://github.com/fractalclockwork/cede)** Dev-Host + cede-gateway — toolchains, flash/sync, stable USB/serial/V4L attach, discovery; DS-7 lifecycle `build` / `deploy` / `validate` / `debug`. See CEDE [DEV_OP Phase 7](https://github.com/fractalclockwork/cede/blob/main/docs/DEV_OP.md), [DS-7 / DS-17](https://github.com/fractalclockwork/cede/blob/main/docs/DESIGN_SPECIFICATION.md), and peer landscape [`research.md`](research.md). **Lab LAN (proposal):** OpenWRT = L2/L3 instrument network; cede-gateway = non-IP attach; IP PDUs + Dev-Host health rollup = gated ops plane — [`procedures/lab_network_gateway.md`](procedures/lab_network_gateway.md). |
| `sample_prep` | OperatorGate prompts (“dilute N× and load”). Liquid handling is [outside the current baseline](charter.md#outside-this-baseline). |
| `ai_ml_decision` | `DecisionEngine` protocol; `ClipSNRDilutionPolicy` rules; BayBE can implement the same protocol later |
| `orchestration` | `CampaignRunner` loop: propose → gate → execute → persist |
| `data_backbone` | `CampaignStore` filesystem provenance |
| `robotics_handling` / `synthesis_prep` | Stage 5, [outside the current baseline](charter.md#outside-this-baseline) |

### Boundary

| Layer | Owns | Does not own |
| --- | --- | --- |
| **self-driving-lab** | SOPs, policy, campaign chemistry (e.g. tap vs distilled), `runs/` provenance, HTTP adapters | Wire protocols, G-code, V4L capture, MCU flash; instrument-repo source edits |
| **Instrument repos** | IOP, abort / idle-safe, acquisition, published instrument baselines | Campaign policy; gateway OS / by-id contracts; the campaign store |
| **CEDE** | Toolchains, flash/sync, by-id serial & UVC nodes, access groups (`dialout` / `video`) | Spectrometer protocol, Marlin G-code, campaign policy |

**Reuse without merging:** spectrometer-lab (and later instrument repos) are **standalone black-box services**. This repo consumes their published contract — preferred: HTTP (`LS55HttpClient` → `:8055`); temporary until Stage 3 SOP/HTTP is live: invoke sibling-checkout CLIs via `SPECTROMETER_LAB_ROOT` the same way HIL does. Do **not** patch instrument repos from a session in this repo, vendor `ls55` into this tree, or write campaign chemistry into instrument published calibration sets. Sample identity and accept/reject live in campaign state / `runs/`.

**Evidence-gated loops.** Permission: [charter](charter.md#dual-loop-permission). Phase map: [`procedures/automated_academic_research.md`](procedures/automated_academic_research.md).

**Live path (spectrometer):** adapter → IOP service → **cede-gateway device node** (not Dev-Host USB by default). **Data plane:** campaign store and all image processing stay on the **Dev-Host** (`runs/`); the gateway may hold only a temporary capture file. First bridge cohort: **LS 55** (Prolific USB–RS232; [water Raman](procedures/water_raman.md), [OBJ-1](objectives.md#obj-1); [tonic dilution / IFE](procedures/tonic_dilution.md), [OBJ-2](objectives.md#obj-2)) and **Marlin gantry + Logitech C310** (Mega CDC + UVC; [prep-area dimensional](procedures/prep_area_dimensional.md), [OBJ-3](objectives.md#obj-3); ChArUco + Dev-Host vision — [bring-up](procedures/marlin_c310_bringup.md)). Spectrometer-style HTTP IOP is for spectrometers; prep-area ChArUco metrology is campaign code on the Dev-Host after capture.

**Lab network (proposal):** a future OpenWRT **lab network gateway** unifies Ethernet/WiFi instruments and IP smart PDUs on one LAN; **cede-gateway(s)** remain the USB/serial/GPIO/UVC attach plane. Dev-Host owns health aggregation and operator-armed outlet actions. Requirements and topology: [`procedures/lab_network_gateway.md`](procedures/lab_network_gateway.md). **Stretch:** [`tools/lab_status.py`](../../tools/lab_status.py) emits attach-vs-IOP JSON for the cohort; [crt-drive](https://github.com/fractalclockwork/crt-drive) VTTY (`APP=vtty`, `vtty_host_lab`) can show it on the Link MC5 — display only, not a campaign gate.

## Loop

1. **Predict / Select** — policy emits `ExperimentProposal` from `CampaignState` + last `MeasurementResult`.
2. **Operator gate** — human ack (or `AutoAckGate` in fixture mode).
3. **Experiment** — SOP calls the LS 55 client; metrics are normalized (`peak_nm`, `peak_intensity`, `snr`, `clipped`, `overload`).
4. **Update** — accepted scans append surrogate points; store writes JSONL + state snapshot.

## Integration contract

SOPs never parse RS-232. The adapter normalizes spectrometer-lab JSON into `MeasurementResult`. Offline CI uses `FixtureLS55Client` (synthetic linear + IFE + clip response). Live runs point `LS55HttpClient` at `http://127.0.0.1:8055`; the IOP opens the instrument serial path on the gateway when running on the Pi bench.

## Safety

Connect requires `gate_a_pass` and `compartment_closed`. Campaign shutdown calls shutter-off. Abort remains available on the instrument console / `/api/abort`. CEDE guarantees stable attach and OS access groups only; arming, idle-safe, and abort semantics stay on the IOP / campaign side.
