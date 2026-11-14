# Objectives

Stage-gate targets for the current baseline. Status of each track is the [scoreboard](README.md). Vocabulary is the existing Stage 0–5 ladder and the [dual-loop permission](charter.md#dual-loop-permission). Accept rules are copied from the use-cases; this page does not change them.

## OBJ-1

**Water Raman, LS 55 Stage 3.**

Specific: an operator-gated water-Raman campaign in this repo, using the existing `CampaignRunner` and `LS55Client`, with the accept rule already stated in the [water Raman use-case](procedures/water_raman.md).

Measurable: `WaterRamanSOP` exists; a fixture campaign runs; the rule stays \|Δ\| ≤ 5 nm from 397 nm, finite RMS SNR, and no clip or overload.

Baseline: Stage 2 is done (`LS55HttpClient`, `FixtureLS55Client`). Live series [`20261113-214920`](../../runs/tap_water_raman_20261113-214920/REPORT.md) took a matched freepath blank and one tap-water sanity scan, then stopped. Annotated peak 390 nm, \|Δ\| 7 nm, continuum-dominated. `WaterRamanSOP` is unwritten.

Target: Stage 3 software path (propose → `OperatorGate` → execute → persist) for this chemistry. Science close of the optical path is a later live series judged under the same rule.

Owner: this repo. Method and IOP stay in spectrometer-lab.

Dependencies: spectrometer-lab water-Raman method and HTTP `:8055` for a live run; CEDE Prolific attach for a live run; an operator for any physical step. See [risks](risks.md).

Evidence: the use-case, the tap-water `REPORT.md`, and (when it exists) the SOP plus a fixture run under `runs/`.

Done when:

- `WaterRamanSOP` is in this repo and the fixture campaign command runs.
- The accept rule and the optical settings are the ones in the use-case.
- Any live judgment has a `runs/<id>/REPORT.md`.

Still open when:

- The only live evidence is series `20261113-214920`.
- A fixture pass is treated as permission to energize the lamp or as a science accept.
- Slit, emission window, or \|Δ\| is widened to manufacture a pass.

## OBJ-2

**Tonic dilution / IFE, LS 55 Stage 4.**

Specific: keep the tonic closed loop as the Stage 4 reference until OBJ-1 has a closing live series or the [scoreboard](README.md) records an explicit waiver.

Measurable: `TonicDilutionSOP` and `ClipSNRDilutionPolicy` remain the fixture reference; a live tonic campaign waits on that OBJ-1 close or waiver.

Baseline: the SOP, the policy, and `examples/run_tonic_campaign.py --mode fixture` already exist. Science question and stop conditions are in the [tonic use-case](procedures/tonic_dilution.md).

Target: tonic becomes the authorized next LS 55 loop only after OBJ-1 closes or is waived.

Owner: this repo.

Dependencies: OBJ-1. Same LS 55 adapter. Operator remains the sample-prep actuator.

Evidence: tonic use-case; fixture campaign artifacts under `runs/<campaign_id>/`.

Done when: the scoreboard shows OBJ-1 closed or waived, and tonic is named there as the next LS 55 loop.

Still open when: OBJ-1 is open, or a live tonic run is used in place of the water-Raman accept rule.

## OBJ-3

**Prep-area dimensional metrology, Marlin + C310.**

Specific: finish Stage 0 exit evidence, then add a Stage 2 fixture client. The next slice stops there.

Measurable: an operator record of the 100 mm bar check, workspace limits, and the estop / soft-stop story; then a fixture motion/capture client that returns Dev-Host paths.

Baseline: printable ChArUco card (`sdl-prep-charuco-v1`) and the cohort HIL path exist. Print/ruler-check, workspace limits, and estop notes are open. Stages 1–5 are open. Science question is the [prep-area use-case](procedures/prep_area_dimensional.md). Checklist: [marlin_c310_bringup.md](procedures/marlin_c310_bringup.md).

Target for this slice: Stage 0 remainder recorded, then a Stage 2 fixture. ChArUco detection and a Stage 3 SOP stay later.

Owner: this repo for the campaign record and Dev-Host metrology. CEDE for USB attach. Motion IOP, when it exists, stays outside this repo.

Dependencies: CEDE Mega CDC and C310 UVC identity; operator-recorded workspace and estop before any live `G0` or home. Software does not invent travel limits.

Evidence: calibration manifest under `docs/project/calibration/`; HIL frames under `runs/hil_<utc>/`; the bring-up note once the operator checklist is filled.

Done when (this slice): the Stage 0 checklist items 1 and 4 in the Marlin bring-up note are recorded, and a fixture client returns Dev-Host frame paths.

Still open when: a HIL fixture pass is counted as Stage 0 complete; a motion client lands before workspace and estop are recorded; travel limits are invented in code.

## OBJ-4

**Campaign record.**

Specific: every live judgment carries a run directory a later student can read, with campaign sample identity and a method citation.

Measurable: `runs/<id>/` holds the artifacts and a `REPORT.md`; the campaign label names the chemistry; the method citation points at the instrument procedure; tap-water results stay out of the distilled published set.

Baseline: series `20261113-214920` meets this for that series. The IOP sidecar on that run still says distilled water. Store layout is `state.json`, `events.jsonl`, and `runs/catalog.json` on the Dev-Host.

Target: the same bar for the next live judgment (water Raman, gantry, or tonic).

Owner: this repo.

Dependencies: `CampaignStore`; the operator’s `REPORT.md` for physical-loop assent.

Evidence: [tap-water report](../../runs/tap_water_raman_20261113-214920/REPORT.md).

Done when: a live campaign’s directory contains the judgment, the campaign sample label, the method citation, and the instrument settings, and tap-water data remains in this repo’s `runs/`.

Still open when: a live scan has no `REPORT.md`, the IOP sidecar string is used as the chemistry label, or tap water is copied into spectrometer-lab `data/published/water-raman/`.

## OBJ-5

**Boundary.**

Specific: work stays inside the [charter scope](charter.md#scope-baseline). A change that crosses the boundary edits the charter first.

Measurable: campaign code and SOPs call adapters; they do not gain a wire parser, G-code emitter, V4L capture path, MCU flash, SiLA or OPC UA stack, ChemOS/AlabOS/IvoryOS/ROS adoption, Gate D qualification, or Stage 5 robotics.

Baseline: the split with spectrometer-lab and CEDE holds in the current tree. Gate D is open. Stage 5 is deferred.

Target: the split still holds after OBJ-1 and the OBJ-3 slice.

Owner: this repo for the campaign side. spectrometer-lab and CEDE keep their own definitions of done.

Dependencies: none. This objective constrains OBJ-1 … OBJ-4.

Evidence: charter scope lists; review of any SOP or adapter added for OBJ-1 or OBJ-3.

Done when: each new campaign path has an adapter or fixture boundary, and scope changes show up in the charter before they show up in code.

Still open when: a patch vendors instrument protocol into this repo, edits spectrometer-lab or CEDE from a session in this repo, or starts Stage 5 without a charter change.
