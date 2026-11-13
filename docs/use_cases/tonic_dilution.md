# Use-case: Tonic dilution / IFE onset

Closed-loop version of spectrometer-lab **Experiment 1** (tonic-water emission spectrum & dilution series).

**Later-stage LS 55 project:** prefer [water Raman bringup](water_raman.md) as the first SDL↔LS 55 loop (Stage 3). This use-case is **Stage 4** — adaptive dilution / IFE — after water-Raman SOP and accept criteria are in place. Existing `TonicDilutionSOP` / fixture CI remain as the advanced reference implementation.

## Science question

Where does blank-subtracted fluorescence intensity deviate from linear concentration scaling (inner-filter effect onset)?

## Hardware / chemistry

- Instrument: PerkinElmer LS 55 via spectrometer-lab
- Physical attach (Pi bench): LS 55 RS-232 via **cede-gateway** Prolific USB–RS232 by-id (CEDE Phase 7); IOP opens the serial node, not Dev-Host USB
- Fluorophore: commercial tonic water (quinine), aqueous dilutions
- Settings: Ex **350 nm**, Em **400–550 nm**, **5 nm** slits, guide ~**447 nm**
- Usefulness gate from DIY baseline: unclipped near ~**1:450** on this mixer
- **Gate D** seating still open for factory-qualified claims; fixture mode does not need it

## Loop behavior

| Observation | Policy action |
| --- | --- |
| Scout clipped / `0107` | Propose **dilute 2×** and reload |
| Scout too weak | Propose **concentrate 2×** (stronger sample) |
| Scout OK | Propose full **Em scan** |
| Scan accepted | Append surrogate point; propose next ladder dilution |
| ≥3 points with high-c under-linear vs low-c fit | **Stop** — IFE onset |
| Step budget exhausted | **Stop** — `max_steps` |

## Operator role

Until Stage 5 robotics (see [instrument bringup roadmap](../roadmap/instrument_bringup.md)), the human is the sample-prep actuator:

1. Prepare the requested dilution (`1:N` tonic-to-total).
2. Load cuvette, close compartment.
3. Acknowledge the prompt so the SOP may scout or scan.

## Run

```bash
# Dry-run
uv run python examples/run_tonic_campaign.py --mode fixture

# Bench (spectrometer-lab dashboard on :8055)
uv run python examples/run_tonic_campaign.py --mode http --interactive \
  --start-dilution 80
```

Artifacts: `runs/<campaign_id>/state.json`, `events.jsonl`, and catalog entry with stop reason (`ife_onset`, etc.).

## Mapping to SDL dossier

This is an **exploration** loop (adaptive next experiment), not a fixed HTS grid. Adaptive quality (clip → dilute/remeasure) mirrors the dossier’s Rigaku-style instrument correction idea, applied here to **sample concentration** as well as (later) slits/`$PV`.
