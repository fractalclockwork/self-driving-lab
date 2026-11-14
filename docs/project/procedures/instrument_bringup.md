# Instrument bringup roadmap

Scope, status, and permission: [project record](../README.md). This page is the stage ladder and its exit criteria. If it disagrees with the [charter](../charter.md) on scope or permission, the charter wins.

Canonical ladder for bringing lab instruments into this lab. This repo owns orchestration, decision, and data; instrument operating procedures (IOPs) stay in a dedicated service when possible (spectrometer-lab for the LS 55). **Physical attach and continuous embedded lifecycle** (build → deploy → validate, by-id serial/UVC) live in [CEDE](https://github.com/fractalclockwork/cede) — gateway as **attach** host (Phase 7), with the campaign and vision host on the Dev-Host. Durable artifacts and all image processing live on the **Dev-Host** (`runs/`). Every new device climbs the same stages; the LS 55 is the gold-standard science example; LS 55 + Marlin gantry + Logitech C310 are the first cohort that bridges CEDE attach to this repo.

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

| Stage | Name | Read next | Exit criteria (generic) |
| --- | --- | --- | --- |
| 0 | Inventory & safety | Cohort HIL: [`instrument_hil_bringup`](instrument_hil_bringup.md). Marlin remainder: [`marlin_c310_bringup`](marlin_c310_bringup.md), [OBJ-3](../objectives.md#obj-3). | Physical I/O known via CEDE gateway inventory; hazards and abort path named; HIL tool PASS on LS 55 RS-232 identity + Marlin M115 + C310 capture. For IP devices, outlets, and health layers, see [`lab_network_gateway`](lab_network_gateway.md) (proposal). |
| 1 | IOP owned elsewhere or stubbed | spectrometer-lab FastAPI on `:8055` | Device mechanics behind a stable API; this repo never parses the wire protocol |
| 2 | Integration adapter | [`src/sdl/integration/ls55_client.py`](../../../src/sdl/integration/ls55_client.py) — `LS55Client`, HTTP + fixture | Protocol + live client + offline fixture; normalized result types |
| 3 | Operator-gated SOP | [OBJ-1](../objectives.md#obj-1), [water Raman](water_raman.md). Loop types: `CampaignRunner`, `OperatorGate`. | Propose → `OperatorGate` → execute → persist |
| 4 | Closed-loop policy | [OBJ-2](../objectives.md#obj-2), [tonic dilution / IFE](tonic_dilution.md) | Adaptive next-action from measurements; explicit stop conditions |
| 5 | Robotics / unattended | [Outside the current baseline](../charter.md#outside-this-baseline) | Sample prep / transport no longer human-actuated |

Stage 0 for bench instruments should cite the **CEDE first-cohort** device identity (USB by-id / V4L) from [CEDE DEV_OP Phase 7](https://github.com/fractalclockwork/cede/blob/main/docs/DEV_OP.md) and stubs in [`config/lab.example.yaml`](https://github.com/fractalclockwork/cede/blob/main/config/lab.example.yaml). CEDE does not absorb IOP protocol: LS 55 campaign loops still depend on spectrometer-lab.

### Safety invariants (all stages)

- Named **abort** (or motion-safe stop) reachable by the operator.
- Documented **idle-safe** posture (e.g. Xe shutter off, axes stopped).
- **Operator arming** before live actions that can energize lamps, move axes, or open compartments (`gate_a_pass`-style where applicable).
- Agents do not assert compartment closed, Gate A, or Xe-on. Those are human claims. A fixture pass does not authorize a live scan or a move.
- Fixture / dry-run mode must not require factory seating (Gate D) or live hardware.
- CEDE supplies stable attach and OS groups (`dialout` / `video`) only; abort and idle-safe stay on the IOP.

## Current position

Ladder position for each instrument is the [project status scoreboard](../README.md).

### LS 55 order

1. Stage 3 — [OBJ-1](../objectives.md#obj-1), use-case [water Raman](water_raman.md).
2. Stage 4 — [OBJ-2](../objectives.md#obj-2), use-case [tonic dilution / IFE](tonic_dilution.md). Same `LS55Client`.
3. Stage 5 — [outside the current baseline](../charter.md#outside-this-baseline).

### North star (gantry + C310)

1. **First use-case:** [prep-area imaging / dimensional metrology](prep_area_dimensional.md) ([OBJ-3](../objectives.md#obj-3)) — move to prep waypoint, capture with C310, recover mm scale from the committed **ChArUco** card on the Dev-Host, report feature lengths.
2. **Camera positioning** — home, named waypoints, pose report; frames for provenance.
3. **Lighting / exposure control** — repeatable illumination and capture settings tied to waypoints or SOP steps.
4. **Sample prep assist → automate** — reduce operator prompts in later LS 55 campaigns (water load, then tonic dilution). Stage 5 stays [outside the current baseline](../charter.md#outside-this-baseline).

## Shared adapter contract

For **spectrometers** (LS 55 today; modern spectrometers later), mirror the HTTP IOP pattern:

- **Protocol surface** with at least `connect`, `state`, and `abort` (or motion-safe idle / estop).
- **Live client** talking only to the IOP API — SOPs never emit G-code, RS-232, USB, or V4L calls.
- **Offline fixture** double for CI and dry-run campaigns.
- **Normalized observations** written into the campaign store (`runs/<id>/` on the Dev-Host), not raw wire dumps as the SOP’s primary result type.
- Optional device-specific setup (optics, home, exposure) stays on the adapter, not in the policy.
- **Physical attach** via CEDE cede-gateway (by-id serial / UVC); IOP opens those nodes, not Dev-Host USB by default.

For **Marlin + C310** prep-area vision, do **not** copy the spectrometer HTTP IOP shape for detection. Capture may use HIL/`scp` or a thin helper against gateway nodes; ChArUco / mm metrology is campaign code on the Dev-Host after the frame is in `runs/`. See [`marlin_c310_bringup.md`](marlin_c310_bringup.md).

## Suggested sequence: Marlin gantry + Logitech C310

1. **Stage 0** — Inventory from CEDE first cohort: Marlin on Arduino Mega CDC (`/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_*`, confirm `M115` before locking `lab.yaml`); Logitech C310 UVC (`046d:081b`, typically `/dev/video0` or `/dev/v4l/by-id/*`); print/ruler-check [`docs/project/calibration/`](../calibration/) ChArUco; workspace limits; estop / soft-stop story. Run [`instrument_hil_bringup`](instrument_hil_bringup.md) from the Dev-Host (`--ssh-gateway`). Details: [`marlin_c310_bringup.md`](marlin_c310_bringup.md). Do not wire stubs into Hello Lab Uno resolvers (`usb-Arduino_*` also matches Mega).
2. **Stage 1** — Minimal Marlin IOP (home, move XYZ, report position) if/when needed; frame grab remains temporary on the gateway. Keep G-code and durable V4L storage out of gateway-side services.
3. **Stage 2** — Campaign motion/capture clients + fixtures that return Dev-Host paths / fake frames. ChArUco detection stays a Dev-Host step, and the capture client is a fixture or a thin helper rather than an HTTP vision IOP.
4. **Stage 3** — Operator-gated prep-area SOP (home → `prep_overview` → capture → Dev-Host persist) via `CampaignRunner`; see [prep-area dimensional use-case](prep_area_dimensional.md).
5. **Stage 4** — Policy on card detect / scale residual / accept measurements (mm) on the Dev-Host; later load-verify or LS 55 prep assist can reuse motion+capture adapters.
6. **Stage 5** — Unattended prep / transport that can stand in for today’s human sample-prep actuator.

## Scope

Project scope is the [charter](../charter.md). Work order is the [backlog](../backlog.md).

## Related docs

- Project record: [`docs/project/README.md`](../README.md)
- Architecture: [`docs/project/architecture.md`](../architecture.md)
- Academic lifecycle and dual loop: [`automated_academic_research.md`](automated_academic_research.md)
- Lab network gateway proposal (OpenWRT + cede-gateways + PDU/health): [`lab_network_gateway.md`](lab_network_gateway.md)
- Stage 0 HIL bring-up (LS 55 + Marlin + C310): [`docs/project/procedures/instrument_hil_bringup.md`](instrument_hil_bringup.md)
- Lab status display stretch (CRT VTTY): [`tools/lab_status.py`](../../../tools/lab_status.py) + crt-drive `vtty_host_lab` (see [`lab_network_gateway.md`](lab_network_gateway.md))
- Marlin + C310 bring-up + ChArUco card: [`docs/project/procedures/marlin_c310_bringup.md`](marlin_c310_bringup.md)
- Use-case (LS 55 Stage 3, [OBJ-1](../objectives.md#obj-1)): [`docs/project/procedures/water_raman.md`](water_raman.md)
- Use-case (LS 55 Stage 4, [OBJ-2](../objectives.md#obj-2)): [`docs/project/procedures/tonic_dilution.md`](tonic_dilution.md)
- Use-case (gantry + C310 first loop): [`docs/project/procedures/prep_area_dimensional.md`](prep_area_dimensional.md)
- Prior art: [`research.md`](../research.md)
- CEDE physical layer: [DEV_OP Phase 7](https://github.com/fractalclockwork/cede/blob/main/docs/DEV_OP.md), [lab.example.yaml stubs](https://github.com/fractalclockwork/cede/blob/main/config/lab.example.yaml)
