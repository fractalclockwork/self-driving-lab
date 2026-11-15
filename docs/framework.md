# The framework

The framework is general. It has no dilution ratio, no peak wavelength, and no gantry pose. Those belong to a [defined workflow](workflow.md).

A self-driving lab chooses the next experiment from measurements it already has, runs that experiment, and updates what it believes. A high-throughput screen runs a list fixed in advance. The difference is where the next step comes from. That distinction is the one recorded in the vendor survey at commit [`81f54ac`](https://github.com/fractalclockwork/self-driving-lab/blob/81f54acdcc091ef58b1343a9531262ea96606522/docs/vendor/landscape.md): a fixed grid on one side, and a sequential loop of predict, select, experiment, and update on the other.

Five parts follow. Each states the rule and who already carries it out. The decision tools and orchestrators are examples of the practice. None of them is installed here. This repository documents them. It does not implement them.

## Choose

A decision tool proposes the next step from the data so far, and it names a stop condition. A workflow whose sequence is fixed in advance does not use one. It uses the accept rule under [Rules that hold for every workflow](#rules-that-hold-for-every-workflow).

Tools that do this job: [BayBE](https://github.com/emdgroup/baybe), [Gryffin](https://github.com/aspuru-guzik-group/gryffin), and [Ax](https://github.com/facebook/Ax). They cover Bayesian optimization and active learning over mixed variables.

## Approve

A person who can see the bench approves any physical step. The orchestrator asks and waits. This is this lab's requirement. The same behavior is already present in [AlabOS](https://github.com/CederGroupHub/alabos) when a device asks a person to intervene.

## Run

An orchestrator orders the steps, tracks the sample, and stores the result. What that store must hold is [the run record](run-record.md).

Tools that do this job: [AlabOS](https://github.com/CederGroupHub/alabos), [ChemOS](https://github.com/malcolmsimgithub/ChemOS2.0), and [IvoryOS](https://gitlab.com/heingroup/ivoryos).

## Measure

The instrument's own software performs the measurement. The framework calls it. The framework does not contain the instrument's protocol.

[spectrometer-lab](https://github.com/fractalclockwork/spectrometer-lab) is the LS 55 instance of that practice. It is the software for one instrument, not the measurement layer of the framework.

## Find the device, and know what it is running

Before a live step, something answers where the device is, whether it is ready, and what firmware it is running. The orchestrators above do not do this. AlabOS is given a port name and trusts that the port exists, the device is powered, and the address is still right.

This lab's development and validation of that part is [this lab's evidence](evidence.md). [CEDE](https://github.com/fractalclockwork/cede) is the system that runs. [lab-fabric](~/src/lab-fabric/) is the method that generalizes it. The lab-fabric checkout is the sibling directory `~/src/lab-fabric/`, and it has no remote yet.

## Rules that hold for every workflow

- The accept rule is numbers, written before the run, and it is not widened to turn a rejection into an acceptance. The rule itself belongs to the [workflow contract](workflow.md).
- A simulated run shows that the workflow runs. It is not permission to energize or move hardware.
- The instrument's own stop is the abort. An outlet is never the way a device is stopped.
- Liquid handling, when a workflow needs it, goes through an existing interface. [PyLabRobot](https://github.com/PyLabRobot/pylabrobot) is that interface for existing liquid handlers.
