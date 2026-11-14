# Assumptions, dependencies, risks

Tied to the [objectives](objectives.md). Mitigations are rules already stated in the [charter](charter.md) or the use-cases.

## Assumptions

- The water-Raman accept rule and optical settings stay as written in the use-case.
- Distilled series `20261103-1629` remains the wavelength reference. Tap-water intensity and SNR differences are chemistry comparison.
- CEDE Phase 7 is the physical attach plane for the first cohort (LS 55 Prolific, Marlin Mega CDC, Logitech C310).
- The operator loads samples through Stage 4.
- Durable artifacts and all image processing stay on the Dev-Host.
- A green fixture run authorizes nothing on the bench.

## Dependencies

| Dependency | Used by | If missing |
| --- | --- | --- |
| spectrometer-lab water-Raman method and HTTP `:8055` | OBJ-1 live path | Fixture work can proceed; live scans wait |
| `SPECTROMETER_LAB_ROOT` CLI invoke | HIL identity dump, and live scans until the Stage 3 SOP is on HTTP | Temporary. A second protocol splits the contract |
| CEDE cede-gateway by-id nodes | Live OBJ-1 and OBJ-3 | Dev-Host USB is not the default bench path |
| Operator who can see the bench | Any physical-loop step | The autonomous loop stops at fixture and offline analysis |
| Printed ChArUco card, ruler-checked | OBJ-3 Stage 0 close | Card PDFs alone leave Stage 0 open |
| External Marlin IOP (later) | OBJ-3 after the fixture slice | G-code stays out of SDL SOPs |

## Risks

| ID | Risk | Affects | Response already in force |
| --- | --- | --- | --- |
| R1 | Widening slits, the emission window, or \|Δ\| to force a water-Raman pass | OBJ-1 | Accept rule is frozen in the use-case and OBJ-1. A fail stays a fail. |
| R2 | Reading the tap-water continuum as a seating-only fault and collecting technical/reseat scans under that theory | OBJ-1 | Series `20261113-214920` stopped at sanity. Distilled redo is a separate question, recorded in that report. |
| R3 | Trusting the IOP sidecar string `distilled water` as the campaign chemistry | OBJ-4 | SDL sample label is authoritative. Tap water stays out of the published distilled set. |
| R4 | Treating a fixture pass as Xe-on, gantry motion, or Gate A | OBJ-1, OBJ-3, dual loop | Physical loop requires operator acknowledgment and a `REPORT.md`. |
| R5 | Claiming factory seating while Gate D is open | OBJ-1, OBJ-5 | DIY fixture baselines are the allowed claim level. |
| R6 | Inventing Marlin travel limits in software before workspace and estop are recorded | OBJ-3 | Stage 0 checklist item 4 is operator-recorded. No live `G0` / home before that. |
| R7 | Binding the Mega to a Hello Lab Uno resolver (`usb-Arduino_*` matches both) | OBJ-3 | Mega identity stays the `0042` by-id path in the HIL note. |
| R8 | An SDL session patching spectrometer-lab or CEDE, or vendoring the IOP | OBJ-5 | Those repos stay black boxes. Campaign chemistry stays in `runs/`. |
| R9 | Describing the lab network gateway proposal as built Stage 0 inventory | OBJ-3, OBJ-5 | The proposal is requirements and topology only. USB cohort inventory is the current Stage 0. |
| R10 | Starting BayBE, a live tonic loop, or Stage 5 ahead of the scoreboard order | OBJ-2, OBJ-5 | [Backlog](backlog.md) parks them behind OBJ-1 and the charter. |
