# A defined workflow

A method runs on [the framework](framework.md) when it states a contract:

- the question
- the instrument
- the settings
- the actions
- the observations
- the accept rule
- the stop

The framework stores that contract and runs it. The contract itself belongs to the workflow. The rules that hold for every workflow — an accept rule fixed in numbers beforehand, a simulated run that is not permission to move hardware, the instrument's own stop as the abort — are on [the framework page](framework.md#rules-that-hold-for-every-workflow).

Two workflows follow. Both are instances. Neither is the framework. What a run of either one must leave behind is [the run record](run-record.md).

## Worked example: the LS 55 workflow

One instrument, the PerkinElmer LS 55, through [spectrometer-lab](https://github.com/fractalclockwork/spectrometer-lab). Two methods share it.

**Water Raman** is the fixed case. The sequence is written in advance, so no decision tool is required.

| Contract | This method |
| --- | --- |
| Question | Does the water peak fall on the guide, closely enough to trust the lamp, the monochromators, and the detector? |
| Instrument | LS 55, through spectrometer-lab |
| Settings | Excitation 350 nm. Emission 380–420 nm. Slits 10 nm |
| Actions | Connect, take a matched blank, scan |
| Observations | Peak wavelength, its distance from the guide, signal-to-noise, clip, overload |
| Accept rule | The peak is within 5 nm of 397 nm, with finite signal-to-noise and no clip or overload |
| Stop | The scan is judged, or the step budget is spent |

The live tap-water series (`tap_water_raman_20261113-214920`) read the peak at 390 nm, 7 nm from the guide. The rule rejected it. The xenon lamp was left off. The distilled series `20261103-1629` in spectrometer-lab remains the wavelength reference. The rejection was kept, and the accept rule was left as written.

**Tonic dilution** is the same instrument with the next dilution chosen from earlier measurements. The question is where fluorescence stops scaling with concentration. It ran against a simulated spectrometer. That run shows the workflow can choose a next step. It is not a live measurement.

The method notes are `docs/project/procedures/water_raman.md` and `docs/project/procedures/tonic_dilution.md` under `legacy/`, and in git history at [`4f685c6`](https://github.com/fractalclockwork/self-driving-lab/tree/4f685c64b64b6143128ee5900e895d8493299f8d).

## Second example: the prep area

The gantry and the camera, so the contract is visibly not a spectrometer.

| Contract | This method |
| --- | --- |
| Question | Can a frame from a named pose be measured in millimetres on the host after capture? |
| Instrument | Marlin gantry and Logitech C310 |
| Settings | Named poses over the prep area, and the printed calibration card |
| Actions | Move to a pose, capture a frame |
| Observations | The pose, the frame, and, once measured, lengths in millimetres |
| Accept rule | The frame is captured at the commanded pose, with the stepper counts checked |
| Stop | The poses in the run have a frame each |

The run `gantry_charuco_20261113T194915Z` visited five positions and captured a frame at each, with the stepper counts checked. The origin of that run was an unhomed mark at the start pose. Measuring the frames is the host's job, after the frames have been copied there. That measurement was the next step of the method.

The method note is `docs/project/procedures/prep_area_dimensional.md` under `legacy/`, at the same commit.
