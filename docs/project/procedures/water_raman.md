# Use-case: Water Raman (LS 55 bringup)

Objective: [OBJ-1](../objectives.md#obj-1). Ladder position: [project status](../README.md).

Water O–H Raman band as the wavelength / SNR loop: operator-gated connect → setup → scan → accept, with a thin accept/reject rule. Method locked in spectrometer-lab [`docs/experiments/water-raman.md`](https://github.com/fractalclockwork/spectrometer-lab/blob/main/docs/experiments/water-raman.md) (standalone IOP — SDL does not edit that repo). Distilled series `20261103-1629` is the wavelength / fixture reference; the live SDL comparison series uses **tap water** and is recorded under [`runs/tap_water_raman_20261113-214920/`](../../../runs/tap_water_raman_20261113-214920/REPORT.md). Tap-water artifacts stay in this repo’s `runs/`. The distilled calibration set stays in spectrometer-lab.

[Tonic dilution / IFE](tonic_dilution.md) ([OBJ-2](../objectives.md#obj-2)) is the adaptive dilution ladder. This use-case is one chemistry and one accept/reject rule.

## Science / engineering question

With Ex **350 nm** and Em **380–420 nm** (`10 nm` slits), does blank-subtracted water show a local max near the **397 nm** guide (|Δ| ≤ 5 nm) with finite RMS SNR and no clip/overload — enough to trust lamp, monochromators, and PMT on this fixture? Tap vs distilled intensity/SNR differences are chemistry comparison, not a seating or calibration update.

Series [`20261113-214920`](../../../runs/tap_water_raman_20261113-214920/REPORT.md) took a matched freepath blank and one tap-water sanity scan, then stopped (annotated peak 390 nm, |Δ| = 7 nm, continuum-dominated). That result is evidence. The accept rule below is unchanged. Whether the stage is open is the [scoreboard](../README.md).

## Hardware / chemistry

- Instrument: PerkinElmer LS 55 via spectrometer-lab IOP (HTTP preferred; CLI invoke temporary until `WaterRamanSOP` lands)
- Physical attach (Pi bench): LS 55 RS-232 via **cede-gateway** Prolific USB–RS232 by-id (CEDE Phase 7)
- Sample (first live SDL series): **tap water** in 4-window UV quartz cuvette; distilled remains the instrument-repo baseline
- Blank: matched **freepath** (empty compartment, same Ex/slits/speed/step; Em covers 380–420)
- Settings: Ex **350 nm**, Em **380–420 nm**, slits **10 nm**, **120 nm/min**, step **2 nm**, guide **397 nm**, SNR noise band **410–420 nm**
- **Gate D** seating still open for factory-qualified claims; DIY fixture baselines are allowed (no hard `500:1` factory gate)

## Loop behavior (target)

| Observation | Action |
| --- | --- |
| Not connected / gates unset | Operator arm → **connect** (`gate_a_pass`, compartment closed) → **setup** |
| No freepath blank | Propose **freepath blank** scan; persist blank id |
| Water loaded, blank ready | Propose **Em scan** (water-raman) |
| Peak \|Δ\| > 5 nm from 397 nm, clip, or overload | **Reject** — diagnose seat/fill/blank; remeasure |
| Peak OK, finite SNR, no clip | **Accept** point; optional technical / reseat series |
| Sanity + series complete (or step budget) | **Stop** |

Normalized observations: `peak_nm`, `peak_delta_nm`, `snr`, `clipped`, `overload`, `blank_id` (reuse existing `MeasurementResult` fields where they fit).

## Operator role

1. Acquire / select matched freepath blank (cuvette out, door closed).
2. Load water cuvette (tap for the first live comparison; distilled for wavelength redo); seat; close compartment.
3. Acknowledge prompts for setup / scan; shutter-off before opening the door.
4. Abort remains on the instrument console / `/api/abort`.

## Run (when SOP exists)

```bash
# Dry-run — TBD WaterRamanSOP + fixture
# uv run python examples/run_water_raman_campaign.py --mode fixture

# Live — spectrometer-lab on :8055 — TBD
# uv run python examples/run_water_raman_campaign.py --mode http --interactive
```

Until the SDL SOP lands, invoke spectrometer-lab CLI from a sibling checkout (`SPECTROMETER_LAB_ROOT`, unchanged scripts) and copy or summarize campaign artifacts into `runs/`; do not publish tap-water into the distilled calibration set. SDL adapters already speak HTTP for the Stage 3 path.

## Mapping to SDL dossier

| Dossier key | Role here |
| --- | --- |
| `integration` | Existing `LS55Client` / HTTP + fixture (extend fixture for Raman peak ~397 if needed) |
| `analytical_metrology` | spectrometer-lab water-raman scout/scan/review (peak, SNR, clip) |
| `sample_prep` | Load water / freepath blank — no dilution ladder |
| `ai_ml_decision` | Thin accept/reject on peak Δ and clip; **not** `ClipSNRDilutionPolicy` |
| `orchestration` | Future `WaterRamanSOP` + `CampaignRunner` + `OperatorGate` |
| `physical_control_plane` | CEDE cede-gateway serial attach |

## Relation to tonic dilution

Water Raman is the optical-path loop with one chemistry. [Tonic dilution / IFE](tonic_dilution.md) ([OBJ-2](../objectives.md#obj-2)) reuses the same adapter and adds dilution proposals, IFE stop logic, and denser operator prep.
