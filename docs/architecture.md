# Architecture

Level-4 custom control (dossier / Rigaku tier language): this repo owns orchestration, decision, and Python logic; spectrometer-lab owns the LS 55 instrument IOP.

## Layers

```
+-----------------------------------------------------------------+
| Data Backbone — runs/<id>/state.json + events.jsonl + catalog   |
+-----------------------------------------------------------------+
| Orchestration — CampaignRunner + TonicDilutionSOP               |
+-----------------------------------------------------------------+
| Integration — LS55HttpClient / FixtureLS55Client                |
+----------+-----------------+---------------+----------+---------+
| Decision | Sample prep     | (future)      | (future) | Metrology
| Policy   | Operator prompt | Synthesis     | Robotics | LS 55 API
+----------+-----------------+---------------+----------+---------+
```

| Dossier key | Implementation |
| --- | --- |
| `integration` | `sdl.integration.ls55_client` — HTTP to `/api/connect|setup|single-read|scan|review/recompute|state|abort|shutter/off` |
| `analytical_metrology` | spectrometer-lab `LS55Service` (scout `$RD`, scan `$SC`, review peak/SNR/clip) |
| `sample_prep` | OperatorGate prompts (“dilute N× and load”); no liquid handler in v1 |
| `ai_ml_decision` | `DecisionEngine` protocol; `ClipSNRDilutionPolicy` rules; BayBE can implement the same protocol later |
| `orchestration` | `CampaignRunner` loop: propose → gate → execute → persist |
| `data_backbone` | `CampaignStore` filesystem provenance |
| `robotics_handling` / `synthesis_prep` | Deferred (**Stage 5** / out of scope); see [`docs/roadmap/instrument_bringup.md`](roadmap/instrument_bringup.md) |

## Loop

1. **Predict / Select** — policy emits `ExperimentProposal` from `CampaignState` + last `MeasurementResult`.
2. **Operator gate** — human ack (or `AutoAckGate` in fixture mode).
3. **Experiment** — SOP calls the LS 55 client; metrics are normalized (`peak_nm`, `peak_intensity`, `snr`, `clipped`, `overload`).
4. **Update** — accepted scans append surrogate points; store writes JSONL + state snapshot.

## Integration contract

SOPs never parse RS-232. The adapter normalizes spectrometer-lab JSON into `MeasurementResult`. Offline CI uses `FixtureLS55Client` (synthetic linear + IFE + clip response). Live runs point `LS55HttpClient` at `http://127.0.0.1:8055`.

## Safety

Connect requires `gate_a_pass` and `compartment_closed`. Campaign shutdown calls shutter-off. Abort remains available on the instrument console / `/api/abort`.
