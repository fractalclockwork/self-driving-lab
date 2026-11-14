# Project

This directory is the source of truth for purpose, scope, permission, and status. Procedures, the layer map, prior art, and the ChArUco card live here too. If another page disagrees with the charter or the status table on scope, permission, or status, the charter and this table win.

| Page | Owns |
| --- | --- |
| [charter.md](charter.md) | Purpose, success, scope baseline, dual-loop permission, repo boundary, change control |
| [objectives.md](objectives.md) | OBJ-1 … OBJ-5: baseline, target, owner, evidence, done / still open |
| [risks.md](risks.md) | Assumptions, dependencies, risks |
| [backlog.md](backlog.md) | Sequenced refactor (docs, then code) |
| [research.md](research.md) | Prior art. Context, not an adoption list |
| [architecture.md](architecture.md) | Layer map |

## Status

Baseline date **2026-11-14**. Evidence series: tap water [`20261113-214920`](../../runs/tap_water_raman_20261113-214920/REPORT.md). Wavelength reference remains distilled series `20261103-1629` in spectrometer-lab. Update this table first when a stage moves.

| Track | Stage | State | Evidence |
| --- | --- | --- | --- |
| LS 55 water Raman | 2 done; 3 open | Adapter and fixture exist. `WaterRamanSOP` is unwritten. Live tap-water series stopped at sanity (annotated peak 390 nm, \|Δ\| 7 nm from 397 nm). Accept rule unchanged. | [REPORT.md](../../runs/tap_water_raman_20261113-214920/REPORT.md), [OBJ-1](objectives.md#obj-1) |
| Tonic / IFE | 4 reference | `TonicDilutionSOP` and `ClipSNRDilutionPolicy` run in fixture mode. Held until OBJ-1 closes or the scoreboard records a waiver. | [tonic use-case](procedures/tonic_dilution.md), [OBJ-2](objectives.md#obj-2) |
| Marlin + C310 prep area | 0 partial | ChArUco card and cohort HIL path exist. Print/ruler-check, workspace limits, and estop / soft-stop notes are open. Stages 1–5 open. | [marlin_c310_bringup.md](procedures/marlin_c310_bringup.md), [OBJ-3](objectives.md#obj-3) |
| Campaign record | standing rule | The tap-water judgment has a `REPORT.md` and an SDL sample label. The IOP sidecar still says distilled water. | [OBJ-4](objectives.md#obj-4) |
| Boundary | held | Gate D seating is open. Stage 5 is deferred. The lab network gateway is a proposal. | [OBJ-5](objectives.md#obj-5), [charter](charter.md) |

## Detail records

These pages describe procedure and design. They take status from the table above.

- Prior art: [research.md](research.md)
- Academic lifecycle: [procedures/automated_academic_research.md](procedures/automated_academic_research.md)
- Instrument ladder: [procedures/instrument_bringup.md](procedures/instrument_bringup.md)
- Cohort HIL: [procedures/instrument_hil_bringup.md](procedures/instrument_hil_bringup.md)
- Marlin + C310: [procedures/marlin_c310_bringup.md](procedures/marlin_c310_bringup.md)
- Lab network proposal: [procedures/lab_network_gateway.md](procedures/lab_network_gateway.md)
- Use-cases: [water Raman](procedures/water_raman.md), [tonic dilution](procedures/tonic_dilution.md), [prep-area dimensional](procedures/prep_area_dimensional.md)
- ChArUco card: [calibration/](calibration/)
