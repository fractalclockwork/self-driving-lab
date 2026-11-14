# Prior art

Decision record for the physical plane and the science loop. Peer products are context. What this lab adopts is the [charter](charter.md) boundary and the [architecture](architecture.md) layer map.

## What this lab uses

| Need | Choice |
| --- | --- |
| Campaign chemistry, SOPs, policy, `runs/` | This repo |
| LS 55 instrument IOP | [spectrometer-lab](https://github.com/fractalclockwork/spectrometer-lab) |
| Build, deploy, validate, and by-id serial / UVC attach | [CEDE](https://github.com/fractalclockwork/cede) Dev-Host + cede-gateway |

Continuous instrument development here means four steps: a reproducible toolchain produces an artifact, that artifact is flashed or synced onto lab hardware, the running image is attested, and serial / UVC / USB nodes stay discoverable so an external IOP and an SDL adapter can talk. The default bench path is the gateway, and the campaign store stays on the Dev-Host.

Orchestrators and device standards assume some physical plane. They rarely specify that build → deploy → validate loop, which is why `physical_control_plane` is CEDE. See CEDE [DEV_OP Phase 7](https://github.com/fractalclockwork/cede/blob/main/docs/DEV_OP.md) and [DS-7 / DS-17](https://github.com/fractalclockwork/cede/blob/main/docs/DESIGN_SPECIFICATION.md).

## Peer families

| Peer | Pattern | Overlap | Why it stays context |
| --- | --- | --- | --- |
| [Lager](https://www.lagerdata.com/) | Self-hosted box; flash, instruments, CI | Networked bench, flash/test, scriptable attach | Broader instrument control; oriented to DUT HIL |
| [labgrid](https://github.com/labgrid-project/labgrid) | Python board control, remote exporter, pytest | Serial, power, USB, flash | Embedded-board focus; no toolchain matrix like CEDE target types |
| [Linaro LAA](https://hub.linaro.com/laa) + LAVA | One appliance per device, CI worker | Gateway, power, USB, serial | Fleet lab-management stack; heavier than the Pi gateway |
| SiLA 2 gateways ([SLAS 2025 gateway module](https://www.slas-technology.org/article/S2472-6303(25)00139-6/fulltext), Tecan / QPillars driver kits) | SBC USB/RS-232 exposed as SiLA containers | Gateway as physical attach | The standard is SiLA 2. CEDE stays attach-only and leaves the IOP in the instrument repo |
| ChemOS, AlabOS, IvoryOS, PyLabRobot; vendor measurement APIs such as [Rigaku LabLinc](https://rigaku.com/products/lablinc-studio) | SOP/IOP orchestration, sandbox or digital twin | Science loop, or a closed-loop measurement API | No continuous embedded plane. This repo already talks HTTP to an IOP |
| [Mender](https://mender.io/), [balenaCloud](https://www.balena.io/) | OTA OS and app fleets | Future flash method | Parked with CEDE DS-17. Outside Phase 7 |

BenchPod, Cuica, and similar CI-to-DUT bridges sit in the same hardware-CI family as Lager and labgrid.

## Outside this lab

The [charter](charter.md#outside-this-baseline) is the list that governs changes. From this survey, the same choice shows up as:

- ChemOS, AlabOS, IvoryOS, and PyLabRobot stay external names.
- SiLA 2 and OPC UA stay external names. CEDE Phase 7 keeps attach, `lab.yaml` identity, and `dialout` / `video`, and does not take the spectrometer or Marlin protocol.
- Lager, labgrid, Linaro LAA, BenchPod, and Cuica stay peers. They are not replacements, and this repo does not add a CI runner for them.
- Fleet OTA stays parked.
- Gate D qualification and Stage 5 unattended robotics stay outside the current baseline.

## Parked

- BayBE as another `DecisionEngine`. See the [backlog](backlog.md).
- Lab network gateway implementation. The requirements note is [lab_network_gateway.md](procedures/lab_network_gateway.md).
