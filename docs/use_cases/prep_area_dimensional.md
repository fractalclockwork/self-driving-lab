# Use-case: Prep-area imaging / dimensional metrology

First **Marlin gantry + Logitech C310** science loop: image the sample-preparation area and recover **dimensional measurements** (mm) using **printed camera calibration cards**.

Planning / design only until Stage 2–3 clients exist — see [instrument bringup](../roadmap/instrument_bringup.md).

## Science / engineering question

From a named gantry pose over the prep area, can the C310 recover metric scale from a printed calibration card and report feature sizes (and later clearances / placement checks) with provenance in the campaign store?

## Hardware

- **Motion:** Marlin on Arduino Mega — home, move XYZ, report pose (IOP external; G-code stays out of SDL)
- **Vision:** Logitech C310 UVC on **cede-gateway** (`046d:081b`; `/dev/video0` or `/dev/v4l/by-id/*`)
- **Calibration target:** printed camera calibration card(s) (checkerboard / ChArUco / similar) placed in the prep area for the exercise; known square/marker pitch in mm is the ground-truth scale
- **Physical attach:** CEDE Phase 7 first cohort (Mega CDC by-id + C310); IOP opens gateway nodes, not Dev-Host USB by default

## Loop behavior (target)

| Observation | Policy / SOP action |
| --- | --- |
| Not homed / pose unknown | Propose **home**, then move to `prep_overview` waypoint |
| At waypoint, no card / card not detected | Propose **reposition** or operator place/fix card; re-capture |
| Card detected, scale OK | Propose **measure** named features (bbox / segment lengths in mm) |
| Scale residual above threshold | Propose **re-calibrate** (re-capture or nudge Z / exposure) |
| Measurements accepted | Persist frame + pose + scale + mm results; **stop** or next waypoint |
| Estop / soft-stop | Idle-safe axes; abort reachable by operator |

Normalized observations (not raw V4L dumps as the SOP primary type): e.g. `pose_mm`, `frame_id`, `scale_mm_per_px`, `feature_lengths_mm`, `calibration_rms`.

## Operator role

Until automation is trusted:

1. Clear the prep area; place the printed calibration card flat in the field of view.
2. Arm motion (operator gate) before home / moves.
3. Acknowledge capture steps; abort remains available on the motion console / IOP.

## Run (when clients exist)

```bash
# Dry-run (fixture poses + synthetic card frames) — TBD
# uv run python examples/run_prep_area_campaign.py --mode fixture

# Live — Marlin + C310 IOPs on gateway — TBD
# uv run python examples/run_prep_area_campaign.py --mode http --interactive
```

Artifacts (target): `runs/<campaign_id>/` with state, events, and linked frame provenance; catalog stop reason (`measurements_ok`, `calibration_failed`, etc.).

## Mapping to SDL dossier

| Dossier key | Role here |
| --- | --- |
| `integration` | Future `GantryClient` / `CameraClient` (or combined motion+vision) + fixtures |
| `analytical_metrology` | Vision dimensional metrology (scale from printed card; lengths in mm) |
| `sample_prep` | Images the prep area; precursor to load-verify / assist on tonic dilution |
| `ai_ml_decision` | Simple rules first (detect card → measure → stop); BayBE later if needed |
| `orchestration` | `CampaignRunner` + operator-gated waypoint SOP |
| `physical_control_plane` | CEDE cede-gateway attach for Mega + C310 |
| `robotics_handling` | Stage 5 later — unattended prep; this use-case stays Stage 3–4 first |

This is a **vision metrology** loop (calibrate → measure → accept), not fluorescence. It shares the same adapter contract as the LS 55: SOP talks HTTP to IOP; CEDE owns attach only.
