# The run record

A later reader has to be able to reconstruct a run without asking anyone. This is this lab's requirement. The orchestrator stores it. The tools that do that job are named on [the framework page](framework.md#run).

The record holds:

- the workflow, and the accept rule it was run under
- every step, and the time it ran
- the devices, and whether they were ready
- the sample, named by the person who loaded it
- the software versions
- the judgment

A rejection is kept with the same care as an acceptance. The accept rule is the one written in the [workflow contract](workflow.md) before the run, and it is not widened afterward to turn a rejection into an acceptance.

The tap-water series `tap_water_raman_20261113-214920` is the illustration. The report records the method, the sample the person named, and the rejection, and the rejection stands. The wavelengths and the accept rule are on [the LS 55 workflow](workflow.md#worked-example-the-ls-55-workflow).

A simulated run is recorded the same way, and it is marked as simulated. It shows that the workflow runs. It is not permission to energize or move hardware.
