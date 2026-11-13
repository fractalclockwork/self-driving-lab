# Instrument bringup roadmap

Canonical ladder for bringing lab instruments into this PoC. This repo owns orchestration, decision, and data; instrument operating procedures (IOPs) stay in a dedicated service when possible (spectrometer-lab for the LS 55). **Physical attach and continuous embedded lifecycle** (build → deploy → validate, by-id serial/UVC) live in [CEDE](https://github.com/fractalclockwork/cede) — gateway as SDL instrument host (Phase 7). Every new device climbs the same stages; the LS 55 is the gold-standard science example; LS 55 + Marlin gantry + Logitech C310 are the first CEDE↔SDL bridge cohort.

**Terminology:** Ladder **stages** (0–5) are maturity levels in this document. Spectrometer-lab **Gate A / Gate D** are hardware safety and seating qualifications — not ladder stages. Older docs that said “Stage 4+ robotics” mean **Stage 5** here.

```mermaid
flowchart LR
  inv[Stage0_Inventory] --> iop[Stage1_IOP]
  iop --> adapter[Stage2_Adapter]
  adapter --> sop[Stage3_SOP]
  sop --> policy[Stage4_Policy]
  policy --> robot[Stage5_Robotics]
```

## Bringup ladder

| Stage | Name | LS 55 evidence today | Exit criteria (generic) |
| --- | --- | --- | --- |
| 0 | Inventory & safety | Serial/port on cede-pi (Prolific PL2303 by-id); Xe/shutter, Gate A/D language in spectrometer-lab | Physical I/O known via CEDE gateway inventory; hazards and abort path named |
| 1 | IOP owned elsewhere or stubbed | spectrometer-lab FastAPI on `:8055` | Device mechanics behind a stable API; SDL never parses the wire protocol |
| 2 | Integration adapter | [`src/sdl/integration/ls55_client.py`](../../src/sdl/integration/ls55_client.py) — `LS55Client`, HTTP + fixture | Protocol + live client + offline fixture; normalized result types |
| 3 | Operator-gated SOP | **Next:** water-Raman SOP ([use-case](../use_cases/water_raman.md)); `CampaignRunner` + `OperatorGate` already exist. Tonic SOP is later-stage reference code. | Propose → `OperatorGate` → execute → persist |
| 4 | Closed-loop policy | **Later:** [tonic dilution / IFE](../use_cases/tonic_dilution.md) (`ClipSNRDilutionPolicy` + `TonicDilutionSOP` already implemented) | Adaptive next-action from measurements; explicit stop conditions |
| 5 | Robotics / unattended | Deferred | Sample prep / transport no longer human-actuated |

Stage 0 for bench instruments should cite the **CEDE first-cohort** device identity (USB by-id / V4L) from [CEDE DEV_OP Phase 7](https://github.com/fractalclockwork/cede/blob/main/docs/DEV_OP.md) and stubs in [`config/lab.example.yaml`](https://github.com/fractalclockwork/cede/blob/main/config/lab.example.yaml). CEDE does not absorb IOP protocol: SDL LS 55 loops still depend on spectrometer-lab.

### Safety invariants (all stages)

- Named **abort** (or motion-safe stop) reachable by the operator.
- Documented **idle-safe** posture (e.g. Xe shutter off, axes stopped).
- **Operator arming** before live actions that can energize lamps, move axes, or open compartments (`gate_a_pass`-style where applicable).
- Fixture / dry-run mode must not require factory seating (Gate D) or live hardware.
- CEDE supplies stable attach and OS groups (`dialout` / `video`) only; abort and idle-safe stay on the IOP.

## Instrument scoreboard

| Instrument | Ladder status | Notes |
| --- | --- | --- |
| **PerkinElmer LS 55** | **Stage 2 done**; **Stage 3 next** = [water Raman](../use_cases/water_raman.md) | Adapter + fixture CI exist. First SDL bringup loop: distilled-water Raman (peak ~397 nm / SNR). [Tonic / IFE](../use_cases/tonic_dilution.md) is **later Stage 4** (SOP/policy already coded as advanced reference). Gate D seating still open for factory-qualified claims. Stage 5 out of scope for v1. |
| **Marlin gantry + Logitech C310** | **Stage 0–1 next**; Stages 2–5 open | Mega CDC by-id + C310 UVC on cede-pi (CEDE Phase 7). First science loop: [prep-area dimensional metrology](../use_cases/prep_area_dimensional.md) (printed calibration cards). |

### LS 55 sequence

1. **Stage 3 (next):** [Water Raman](../use_cases/water_raman.md) — freepath blank → load water → Em scan → accept on peak Δ / SNR / no clip.
2. **Stage 4 (later):** [Tonic dilution / IFE](../use_cases/tonic_dilution.md) — adaptive dilute/remeasure ladder; reuses the same `LS55Client`.
3. **Stage 5:** Unattended prep / transport (gantry assist) — deferred.

### North star (gantry + C310)

1. **First use-case (locked):** [prep-area imaging / dimensional metrology](../use_cases/prep_area_dimensional.md) — move to prep waypoint, capture with C310, recover mm scale from **printed camera calibration cards**, report feature lengths.
2. **Camera positioning** — home, named waypoints, pose report; frames for provenance.
3. **Lighting / exposure control** — repeatable illumination and capture settings tied to waypoints or SOP steps.
4. **Sample prep assist → automate** — eventually replace or reduce operator prompts in later LS 55 campaigns (water load, then tonic dilution).

## Shared adapter contract

Mirror the LS 55 pattern for every instrument:

- **Protocol surface** with at least `connect`, `state`, and `abort` (or motion-safe idle / estop).
- **Live client** talking only to the IOP API — SOPs never emit G-code, RS-232, USB, or V4L calls.
- **Offline fixture** double for CI and dry-run campaigns.
- **Normalized observations** written into the campaign store (`runs/<id>/`), not raw wire dumps as the SOP’s primary result type.
- Optional device-specific setup (optics, home, exposure) stays on the adapter, not in the policy.
- **Physical attach** via CEDE cede-gateway (by-id serial / UVC); IOP opens those nodes, not Dev-Host USB by default.

## Suggested sequence: Marlin gantry + Logitech C310

Planning only — no clients in this change.

1. **Stage 0** — Inventory from CEDE first cohort: Marlin on Arduino Mega CDC (`/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_*`, confirm `M115` before locking `lab.yaml`); Logitech C310 UVC (`046d:081b`, typically `/dev/video0` or `/dev/v4l/by-id/*`); workspace limits; estop / soft-stop story. Do not wire stubs into Hello Lab Uno resolvers (`usb-Arduino_*` also matches Mega).
2. **Stage 1** — Minimal Marlin IOP: home, move XYZ, report position; separate or co-located frame-grab endpoint for the C310. Keep G-code and V4L IO out of this repo.
3. **Stage 2** — SDL `GantryClient` / `CameraClient` (or one combined motion+vision protocol) + HTTP (or equivalent) live clients + fixtures that return fake poses / frames.
4. **Stage 3** — Operator-gated prep-area SOP (home → `prep_overview` → capture → persist) via `CampaignRunner`; see [prep-area dimensional use-case](../use_cases/prep_area_dimensional.md).
5. **Stage 4** — Policy on card detect / scale residual / accept measurements (mm); later load-verify or LS 55 prep assist can reuse the same motion+vision adapters.
6. **Stage 5** — Unattended prep / transport that can stand in for today’s human sample-prep actuator.

## Out of scope (this document)

- Implementing gantry/camera Python clients or IOPs.
- Implementing `WaterRamanSOP` (tracked by the water-Raman use-case; not this ladder doc).
- ChemOS / AlabOS / IvoryOS, SiLA 2 / OPC UA.
- Completing LS 55 Gate D hardware qualification.
- Printing / CAD for calibration cards (operator supplies known-pitch cards for the exercise).
- CEDE discovery helpers, OTA, or wiring instrument stubs into Hello Lab resolvers.

## Related docs

- Architecture: [`docs/architecture.md`](../architecture.md)
- Use-case (LS 55 Stage 3 bringup): [`docs/use_cases/water_raman.md`](../use_cases/water_raman.md)
- Use-case (LS 55 Stage 4 later): [`docs/use_cases/tonic_dilution.md`](../use_cases/tonic_dilution.md)
- Use-case (gantry + C310 first loop): [`docs/use_cases/prep_area_dimensional.md`](../use_cases/prep_area_dimensional.md)
- Industry stack context: [`docs/vendor/landscape.md`](../vendor/landscape.md)
- CEDE physical layer: [DEV_OP Phase 7](https://github.com/fractalclockwork/cede/blob/main/docs/DEV_OP.md), [lab.example.yaml stubs](https://github.com/fractalclockwork/cede/blob/main/config/lab.example.yaml)
- Continuous instrument / embedded peers (Lager, labgrid, SiLA gateways, OTA): [`docs/vendor/continuous_instrument_development.md`](../vendor/continuous_instrument_development.md)
