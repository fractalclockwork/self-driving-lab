# self-driving-lab

This repository documents how an open-source self-driving lab is put together. It records the practice and the tools that already carry it out. It does not implement a framework, an orchestrator, or a decision tool. Nothing in this repository runs.

A self-driving lab chooses the next experiment from measurements it already has, runs that experiment, and updates what it believes. A high-throughput screen runs a list fixed in advance. The difference is where the next step comes from. That distinction is the one recorded in the vendor survey at commit [`81f54ac`](https://github.com/fractalclockwork/self-driving-lab/blob/81f54acdcc091ef58b1343a9531262ea96606522/docs/vendor/landscape.md).

## The practice

- [The framework](docs/framework.md). The general method: choose, approve, run, measure, and find the device, and the rules that hold for every workflow.
- [A defined workflow](docs/workflow.md). The contract a method states before it can run, with the LS 55 and the prep area as worked examples.
- [The run record](docs/run-record.md). What a later reader needs in order to reconstruct a run.
- [This lab's evidence](docs/evidence.md). What CEDE and lab-fabric have checked, what was tried in this repository, and where the previous tree goes.

## Status

**Documentation of the practice. Nothing in this repository runs.**

The previous tree is at commit [`4f685c6`](https://github.com/fractalclockwork/self-driving-lab/tree/4f685c64b64b6143128ee5900e895d8493299f8d) and, on this machine, under `legacy/`. The sort of that tree is on [the evidence page](docs/evidence.md). The files stay where they are until a later step moves them.

The charter, the objectives, and the scoreboard are not brought back.

## License

MIT. The license file is part of the previous tree and has not been restored at the repository root.
