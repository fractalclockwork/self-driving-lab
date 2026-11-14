# Backlog

Sequenced refactor. Status and acceptance live in the [scoreboard](README.md) and the [objectives](objectives.md). Application code is unchanged by the documentation pass that added this directory.

## Docs

Landed with this directory (2026-11-14):

1. Charter, objectives, risks, backlog, and the status scoreboard, taken from the existing roadmaps, use-cases, and series `20261113-214920`. Accept rules and stage numbers are unchanged.
2. Repository README, architecture, the academic lifecycle, the instrument ladder, and the three use-cases point here for scope, status, and permission.
3. Docs tree collapsed into this directory: procedures, the layer map, the ChArUco card, and one prior-art page. The vendor survey essays are retired.

## Code

Not started. Order is the order to pick them up.

1. **OBJ-1.** Add `WaterRamanSOP` and a fixture example. Reuse `CampaignRunner`, `OperatorGate`, and `LS55Client`. Mirror the water-Raman loop table (freepath blank → water scan → accept or reject). Command shape already sketched in the use-case: `examples/run_water_raman_campaign.py --mode fixture`.
2. **OBJ-1, after that fixture is green.** Decide the Raman fields. `MeasurementResult` already has `peak_nm`, `snr`, `clipped`, and `overload`. `CampaignState` already has `blank_ref` and `guide_nm`. `peak_delta_nm` is not a field. Either compute \|Δ\| from `peak_nm` and the 397 nm guide, or extend the model. Do this only after the fixture exists, so the decision follows a running SOP.
3. **OBJ-3, Stage 0 remainder before any motion client.** Operator records the 100 mm bar check, workspace limits, and estop / soft-stop in the Marlin bring-up note or a run report. Then add a Stage 2 fixture client that returns Dev-Host paths. Capture stays HIL or a thin helper. ChArUco detection stays campaign code on the Dev-Host. This loop does not become an HTTP vision IOP.
4. **Parked** until the scoreboard says otherwise:
   - Further tonic policy work and any live tonic campaign (OBJ-2).
   - BayBE as a `DecisionEngine`.
   - Lab network gateway implementation (the proposal stays a document).
   - Stage 5 unattended robotics.
   - ChArUco measurement SOP beyond the OBJ-3 fixture slice.
