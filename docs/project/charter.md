# Charter

Purpose, scope, permission, and repo boundary for this lab. Status is the [scoreboard](README.md). Numbered targets are the [objectives](objectives.md).

## Purpose

A reproducible academic campaign record a later student can read: the run directory, the accept/reject judgment, and a citation of the instrument method. An unattended self-driving lab is later work, outside the current baseline.

This repo owns campaign chemistry, SOPs, policy, and `runs/`. Instrument code stays in [spectrometer-lab](https://github.com/fractalclockwork/spectrometer-lab). Attach stays in [CEDE](https://github.com/fractalclockwork/cede).

## Success

A later reader can reconstruct what was asked, what ran, and why it was accepted or rejected from `runs/<id>/` plus the method citation, without recovering intent from chat.

## Stakeholders

| Who | Responsibility |
| --- | --- |
| Operator at the bench | Arming, abort, compartment closed, Gate A, Xe on, sample load |
| This repo | SOPs, policy, campaign chemistry, HTTP adapters, `runs/` provenance |
| spectrometer-lab | LS 55 IOP, acquisition, idle-safe, published instrument baselines |
| CEDE | Toolchains, flash/sync, by-id serial and UVC attach, access groups |
| Later reader | Consumes the run directory and the method citation |

## Constraints

- Accept rule for water Raman stays \|Δ\| ≤ 5 nm from 397 nm, finite RMS SNR, and no clip or overload. Settings stay Ex 350 nm, Em 380–420 nm, 10 nm slits.
- Distilled series `20261103-1629` remains the wavelength reference.
- Tap-water campaign artifacts stay under `runs/` in this repo. The distilled calibration set in spectrometer-lab stays the published baseline.
- Sample identity is the SDL label. The IOP sidecar on the tap-water series still says distilled water; that string is an instrument-script constant.
- Fixture mode needs no Gate D seating and no live hardware. Gate D remains open for factory-qualified claims.
- The operator is the sample-prep actuator through Stage 4.
- Campaign store and image processing stay on the Dev-Host. The cede-gateway holds attach nodes and, at most, a temporary capture file.
- HTTP `:8055` is the LS 55 contract. CLI invoke via `SPECTROMETER_LAB_ROOT` is a temporary path until the Stage 3 SOP is live.
- Vendor notes are context. They are not adoption targets.

## Scope baseline

### In this baseline

- Orchestration, decision policy, campaign chemistry, and filesystem provenance under `runs/`.
- LS 55 HTTP adapter and fixture client already in tree; water-Raman Stage 3 SOP tracked as [OBJ-1](objectives.md#obj-1).
- Tonic dilution SOP and `ClipSNRDilutionPolicy` as the Stage 4 reference ([OBJ-2](objectives.md#obj-2)).
- Cohort HIL (LS 55 identity, Marlin `M115`, C310 capture) run from the Dev-Host.
- Prep-area ChArUco card, Dev-Host dimensional metrology, and the Stage 0 remainder ([OBJ-3](objectives.md#obj-3)).
- A `runs/<id>/REPORT.md` beside every live judgment ([OBJ-4](objectives.md#obj-4)).

### Parked

Recorded in the [backlog](backlog.md). Present in the tree or in a proposal, and outside the current slice:

- BayBE as another `DecisionEngine`.
- Lab network gateway implementation ([proposal](procedures/lab_network_gateway.md) only).
- Promoting tonic to the first live LS 55 loop before OBJ-1 closes or is waived on the scoreboard.
- Stage 5 unattended sample prep and transport.

### Outside this baseline

- Wire protocols, G-code, and V4L calls inside SOPs. SOPs call adapters.
- MCU flash, CEDE discovery helpers, OTA, and Hello Lab Uno resolver wiring. SDL HIL stays separate from CEDE `hw-smoke`.
- ChemOS, AlabOS, IvoryOS, ROS, SiLA 2, and OPC UA adoption.
- Gate D hardware qualification.
- Dockerizing the LS 55, containers per instrument, Grafana, and a lab-wide sensor bus.
- An agent rewriting a live SOP.
- Editing spectrometer-lab or CEDE from an SDL session, vendoring `ls55` into this tree, or writing campaign chemistry into an instrument published calibration set.

[OBJ-5](objectives.md#obj-5) is the standing check that a change stays inside this baseline or edits this charter first.

## Dual-loop permission

The loops share evidence. They do not share permission. This repo does not copy rad-lab role trees. The cyber-physical writeup lives outside this repo (`~/src/cyber-physical-systems/article.md`); the first case study is [rad-lab](https://github.com/fractalclockwork/rad-lab) `docs/methodology/`.

| Loop | May do | May not do |
| --- | --- | --- |
| **Autonomous** | Fixture campaigns, offline analysis of existing `runs/`, docs, tests | Energize the Xe lamp, move the gantry, claim the compartment is closed, set `gate_a_pass` |
| **Physical** | Serial bridge, scans, and motion after a human who can see the bench has acknowledged the step | Treat a green fixture run as permission to open the shutter; raise slit, scan range, or motion limits to force a pass |

`gate_a_pass`, `compartment_closed`, and “the door is closed” are human claims. Assent without a scannable `runs/<id>/REPORT.md` is an incomplete physical-loop gate.

Worked case: tap-water series [`20261113-214920`](../../runs/tap_water_raman_20261113-214920/REPORT.md). Matched blank and sanity produced evidence. Sanity failed \|Δ\| ≤ 5 nm from 397 nm. Technical and reseat scans were not run. Xe was left OFF.

## Repo boundary

File-level layer map: [`docs/project/architecture.md`](architecture.md).

| Layer | Owns |
| --- | --- |
| **self-driving-lab** | SOPs, policy, campaign chemistry (tap versus distilled), `runs/` provenance, HTTP adapters |
| **Instrument repos** | IOP, abort, idle-safe, acquisition, published instrument baselines |
| **CEDE** | Toolchains, flash/sync, by-id serial and UVC nodes, `dialout` / `video` |

## Change control

A status change or a scope change is an edit to this directory first. The scoreboard in [README.md](README.md) is the only status table. Roadmaps, the repository README, and use-cases link here instead of carrying a second copy.

When a roadmap safety invariant and this charter disagree on permission, this charter is the permission statement. Edit the roadmap to match. Stage exit criteria stay on the [instrument ladder](procedures/instrument_bringup.md).

## Context

Peer survey and the adoption choice: [`research.md`](research.md). That page is context. The scope lists above are the decision.
