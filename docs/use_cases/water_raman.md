# Use-case: Water Raman (LS 55 bringup)

Simpler **first LS 55** SDL loop: distilled-water O–H Raman band as wavelength / SNR bringup. Method locked in spectrometer-lab [`docs/experiments/water-raman.md`](https://github.com/fractalclockwork/spectrometer-lab/blob/main/docs/experiments/water-raman.md).

[Tonic dilution / IFE](tonic_dilution.md) is a **later Stage 4** project (adaptive dilution ladder). This use-case targets **Stage 3** (operator-gated connect → setup → scan → accept) with a thin accept/reject rule — not a multi-dilution policy.

## Science / engineering question

With Ex **350 nm** and Em **380–420 nm** (`10 nm` slits), does blank-subtracted distilled water show a local max near the **397 nm** guide (|Δ| ≤ 5 nm) with finite RMS SNR and no clip/overload — enough to trust lamp, monochromators, and PMT on this fixture?

## Hardware / chemistry

- Instrument: PerkinElmer LS 55 via spectrometer-lab
- Physical attach (Pi bench): LS 55 RS-232 via **cede-gateway** Prolific USB–RS232 by-id (CEDE Phase 7)
- Sample: distilled water in 4-window UV quartz cuvette
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
2. Load distilled water cuvette; seat; close compartment.
3. Acknowledge prompts for setup / scan; shutter-off before opening the door.
4. Abort remains on the instrument console / `/api/abort`.

## Run (when SOP exists)

```bash
# Dry-run — TBD WaterRamanSOP + fixture
# uv run python examples/run_water_raman_campaign.py --mode fixture

# Live — spectrometer-lab on :8055 — TBD
# uv run python examples/run_water_raman_campaign.py --mode http --interactive
```

Until the SDL SOP lands, use spectrometer-lab CLI (`run_water_raman_serial.py` / `summarize_water_raman.py`) against the same IOP; SDL adapters already speak HTTP.

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

Water Raman proves the optical path and SDL Stage 3 pattern with one chemistry and no adaptive dilution. [Tonic dilution / IFE](tonic_dilution.md) reuses the same adapter and adds dilution proposals, IFE stop logic, and denser operator prep — schedule it **after** this bringup loop is real.
