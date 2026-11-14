# Use-case: Prep-area imaging / dimensional metrology

Objective: [OBJ-3](../objectives.md#obj-3). Ladder position: [project status](../README.md).

First **Marlin gantry + Logitech C310** science loop: image the sample-preparation area and recover **dimensional measurements** (mm) using the committed **ChArUco** calibration card (`sdl-prep-charuco-v1`).

Bring-up procedure: [instrument ladder](instrument_bringup.md), [Marlin + C310](marlin_c310_bringup.md).

## Science / engineering question

From a named gantry pose over the prep area, can the C310 recover metric scale from the printed ChArUco card and report feature sizes (and later clearances / placement checks) with provenance in the campaign store on the **Dev-Host**?

## Hardware

- **Motion:** Marlin on Arduino Mega — home, move XYZ, report pose (IOP external when present; G-code stays out of campaign SOPs)
- **Vision capture:** Logitech C310 UVC on **cede-gateway** (`046d:081b`; `/dev/video0` or `/dev/v4l/by-id/*`); gateway holds only a temporary capture file
- **Calibration target:** [`docs/project/calibration/`](../calibration/) ChArUco PDFs — `DICT_4X4_50`, 5×7, square 24.0 mm, marker 18.0 mm; ruler-check the 100 mm bar
- **Physical attach:** CEDE Phase 7 first cohort (Mega CDC by-id + C310); open gateway nodes, not Dev-Host USB by default
- **Metrology:** ChArUco detect / scale / mm lengths run on the **Dev-Host** (this repo), after the frame is copied into `runs/`. Not a spectrometer-style HTTP vision IOP

## Loop behavior (target)

| Observation | Policy / SOP action |
| --- | --- |
| Not homed / pose unknown | Propose **home**, then move to `prep_overview` waypoint |
| At waypoint, no card / card not detected | Propose **reposition** or operator place/fix card; re-capture |
| Card detected, scale OK | Propose **measure** named features (bbox / segment lengths in mm) |
| Scale residual above threshold | Propose **re-calibrate** (re-capture or nudge Z / exposure) |
| Measurements accepted | Persist frame + pose + scale + mm results on Dev-Host; **stop** or next waypoint |
| Estop / soft-stop | Idle-safe axes; abort reachable by operator |

Normalized observations (not raw V4L dumps as the SOP primary type): e.g. `pose_mm`, `frame_id`, `scale_mm_per_px`, `feature_lengths_mm`, `calibration_rms`.

## Operator role

Until automation is trusted:

1. Clear the prep area; place the printed ChArUco card flat in the field of view (100 mm bar verified).
2. Arm motion (operator gate) before home / moves.
3. Acknowledge capture steps; abort remains available on the motion console / IOP.
4. Run capture from the Dev-Host so durable frames land under `runs/`.

## Run (when clients exist)

```bash
# Dry-run (fixture poses + synthetic card frames) — TBD
# uv run python examples/run_prep_area_campaign.py --mode fixture

# Live — motion/capture against gateway nodes; store + vision on Dev-Host — TBD
# uv run python examples/run_prep_area_campaign.py --mode live --interactive
```

Artifacts (target): Dev-Host `runs/<campaign_id>/` with state, events, and linked frame provenance; catalog stop reason (`measurements_ok`, `calibration_failed`, etc.). Gateway `/tmp` frames are deleted after copy.

## Mapping to campaign layers

| Dossier key | Role here |
| --- | --- |
| `integration` | Future motion/capture clients + fixtures (paths/bytes to Dev-Host; not an HTTP vision IOP) |
| `analytical_metrology` | Dev-Host campaign ChArUco / dimensional metrology (scale from printed card; lengths in mm) |
| `sample_prep` | Images the prep area; precursor to load-verify / assist on tonic dilution |
| `ai_ml_decision` | Simple rules first (detect card → measure → stop); BayBE later if needed |
| `orchestration` | `CampaignRunner` + operator-gated waypoint SOP |
| `physical_control_plane` | CEDE cede-gateway attach for Mega + C310 (attach host, not campaign host) |
| `data_backbone` | Dev-Host `runs/` only |
| `robotics_handling` | Unattended prep is [outside the current baseline](../charter.md#outside-this-baseline). This loop is [OBJ-3](../objectives.md#obj-3). |

This is a **vision metrology** loop (calibrate → measure → accept), not fluorescence. Spectrometer HTTP IOP shape remains for LS 55 / modern spectrometers; prep-area vision stays local on the Dev-Host after capture.
