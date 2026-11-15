# This lab's evidence

The device and toolchain parts of [the framework](framework.md) were built and checked on this lab's hardware, in two projects. This page states what was checked. Their designs stay in their own repositories.

Choosing the next experiment, and running an orchestrator, were not validated here. Those remain the tools on the framework page.

## CEDE

[CEDE](https://github.com/fractalclockwork/cede) is the system that runs. A toolchain container on the dev host builds the firmware. A Raspberry Pi gateway is the USB anchor. The firmware is flashed through that gateway, and a check says whether it arrived and whether the target is present. The targets that validation covers are the Pico and the Uno.

An offline check (`make validate`, with hardware tests excluded) shows that the environment is intact. It is not a claim that a board is attached. When a board is missing, the hardware test is skipped. A skip is not a pass.

## lab-fabric

[lab-fabric](~/src/lab-fabric/) is the method that generalizes the same questions — where the device is, whether it is ready, and what it is running — from one gateway up to the whole lab, from the router through a subnode. The checkout is the sibling directory `~/src/lab-fabric/`, and it has no remote yet. The repository itself does not run yet.

What has been checked is the one-gateway case, on gateway `cede-pi.local`, reported by `tools/instrument_hil_bringup.py` in the run `hil_e2e_20261113T191730Z`:

- The gantry controller answered. Marlin 1.1.9 replied to a read-only identity query.
- The webcam returned a frame. A Logitech C310 on the gateway captured one image.
- The spectrometer was reached as far as its adapter. The Prolific USB-to-RS-232 adapter was present on the gateway. spectrometer-lab was not listening, so the instrument check did not pass.

The wider fabric is the design written from that evidence: a lab network, power strips as the control for pumps and lamps that have no other interface, and firmware passed from a parent node to its children.

## What was tried in this repository

The loop under `legacy/src/sdl/` put the LS 55 fields into the shared state of every run: `dilution_ratio`, `guide_nm`, and `peak_nm`, with campaign identifiers defaulting to the tonic method. The actions were connect, blank, scout, scan, dilute, concentrate, remeasure, accept, and stop. The gantry and the camera lived outside that loop.

That made the loop the [LS 55 workflow](workflow.md#worked-example-the-ls-55-workflow) wearing the shape of a framework. The framework this lab uses is the one on [the framework page](framework.md). The device side of it is what CEDE runs and what lab-fabric is generalizing.

## Where the previous tree goes

Paths are relative to `legacy/`. The files stay where they are until a later step moves them. The previous tree is also at commit [`4f685c6`](https://github.com/fractalclockwork/self-driving-lab/tree/4f685c64b64b6143128ee5900e895d8493299f8d).

### LS 55 defined workflow

The spectrometer method, its client, and the hand-written rule that chose the next dilution. This is one defined workflow. The contract is on [the workflow page](workflow.md).

| Path | What it is |
| --- | --- |
| `docs/project/procedures/water_raman.md` | Water Raman method and accept rule |
| `docs/project/procedures/tonic_dilution.md` | Tonic dilution method |
| `src/sdl/integration/ls55_client.py` | The spectrometer client that loop called |
| `src/sdl/decision/` | A hand-written rule that chose the next dilution |
| `examples/run_tonic_campaign.py` | The tonic campaign entry point |
| `tests/test_policy.py` | Dilution rule test |

### Prep-area defined workflow

The gantry and camera method, and the measurement of a captured frame on the host. This is a second defined workflow.

| Path | What it is |
| --- | --- |
| `docs/project/procedures/prep_area_dimensional.md` | Prep-area measurement method |
| `src/sdl/calibration/` | Measurement from a captured frame, done on the host |
| `tools/prep_area_charuco_card.py` | The printable calibration card |
| `tests/test_charuco_card.py` | Calibration card test |
| `docs/project/calibration/` | The printed card and its description |

### Local attempt at a framework

The campaign loop. Its shared state carries the LS 55 fields, so it is that workflow in the shape of a framework. It is not adopted. The general framework is the prior art on [the framework page](framework.md).

| Path | What it is |
| --- | --- |
| `src/sdl/orchestration/` | A campaign loop and the tonic dilution procedure |
| `src/sdl/data/` | A run record store |
| `src/sdl/models.py` | The campaign state that loop used |
| `tests/test_campaign_fixture.py` | Campaign loop test |
| `tests/test_store.py` | Run record test |

### Moves to lab-fabric

This is how a device is reached.

| Path | What it is |
| --- | --- |
| `src/sdl/hil/` | Device checks: present, answering, status |
| `tools/gateway_serial_bridge.py` | A serial port on the gateway, reached from the host |
| `tools/instrument_hil_bringup.py` | The check that ran against the spectrometer, gantry, and camera |
| `tools/lab_status.py` | A status snapshot of those devices |
| `tests/test_instrument_hil_bringup.py` | Device-check test |
| `tests/test_lab_status.py` | Status snapshot test |
| `docs/project/procedures/lab_network_gateway.md` | The lab network proposal |
| `docs/project/procedures/instrument_hil_bringup.md` | How the device check was run |
| `docs/project/procedures/instrument_bringup.md` | How a device was brought onto the bench |
| `docs/project/procedures/marlin_c310_bringup.md` | How the gantry and camera were brought up |

### Stays in history

These process pages are not revived in either project. They remain at commit `4f685c6` and under `legacy/docs/project/`.

- `charter.md`
- `objectives.md`
- `risks.md`
- `backlog.md`
- `research.md`
- `architecture.md`
- `procedures/automated_academic_research.md`
- `README.md`

`pyproject.toml` and `uv.lock` are not sorted. Each repository gets its own when it has code.
