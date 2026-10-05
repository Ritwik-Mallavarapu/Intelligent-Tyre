# Sources, assumptions and training provenance

Checked 5 October 2026. This file separates cited evidence from engineering choices. No author-provided measured dataset was downloaded or used for training. All 12,000 training/validation/test windows were generated locally by signal_core.h. Do not describe this model as trained on measured research data.

## Primary sources

1. Arduino Nano 33 BLE Sense Rev2 datasheet and pinout:
   https://docs.arduino.cc/resources/datasheets/ABX00069-datasheet.pdf
   https://docs.arduino.cc/resources/pinouts/ABX00069-full-pinout.pdf
   Grounds sensor identities, 16 g/2000 dps measurement limits, pressure measurement range, memory, voltage and pin roles.

2. Arduino BMI270 library source, version 1.2.4 (also downloaded and compiled for this check):
   https://github.com/arduino-libraries/Arduino_BMI270_BMM150/blob/1.2.4/src/BMI270.cpp
   Grounds raw-to-g scaling and default 4 g/2000 dps settings. ACC_RANGE is changed and read back in the firmware.

3. Intelligent Tire Sensor-Based Real-Time Road Surface Classification Using an Artificial Neural Network. Sensors 21(9), 3233 (2021), DOI 10.3390/s21093233.
   https://www.mdpi.com/1424-8220/21/9/3233
   https://pmc.ncbi.nlm.nih.gov/articles/PMC8125707/
   Demonstrates road-classification research using tyre accelerometry. Its surfaces, acquisition rate and trained system differ from this Nano demo; its reported accuracy is not evidence for our model.

4. Low-Cost Road-Surface Classification System Based on Self-Organizing Maps. Sensors 20(21), 6009 (2020), DOI 10.3390/s20216009.
   https://www.mdpi.com/1424-8220/20/21/6009
   https://pmc.ncbi.nlm.nih.gov/articles/PMC7660168/
   Motivates time-domain and spectral features of rolling vibration. Our spectrum parameters and four surface distributions are assumptions, not numerical fits to this paper.

5. Diagnosis of the Pneumatic Wheel Condition Based on Vibration Analysis of the Sprung Mass in the Vehicle Self-Diagnostics System. Sensors 23(4), 2326 (2023), DOI 10.3390/s23042326.
   https://www.mdpi.com/1424-8220/23/4/2326
   https://pubmed.ncbi.nlm.nih.gov/36850924/
   Supports rotation-linked harmonic features and dependence on imbalance/speed. Sprung-mass sensing is different from our rim mount. We do not copy its measured amplitude-to-mass relationship.

6. User-supplied synthetic Creta atlas: 5 normal and 28 abnormal scenarios. Used to define the scope and identify sensor incompatibilities. It contains 1 Hz processed acceleration/envelope values, not raw training waveforms. Its pressure curves require tyre-pressure sensing unavailable on this board; high radial accelerations exceed the Nano's measurement range. PDF traces were not digitized into purported raw training data.

Some publisher full-text fetches were rate limited; source evidence was accessed through indexed paper excerpts and official documents. Parameter assumptions below are deliberately explicit rather than attributed to those papers.

## Generated signals (all assumed values)

99.84 Hz, 256 samples per window (~2.56 s), 78–162 RPM. Z is axle direction; Y tangential; X radial inward. This differs from the atlas's label convention where Y is axial and Z radial.

Gravity creates a rotating 1 g in-plane component. X also includes centripetal acceleration for an assumed 0.22 m sensor radius. This is separate from the display tyre diameter 0.6729 m (205/65 R16); actual Creta sizes vary.

Surface excitation: sixteen random-phase tones in bands 4–8, 9–16, 17–29 and 30–43 Hz. Assumed amplitude profiles (g per tone): smooth asphalt [.030,.014,.006,.003]; rough asphalt [.045,.060,.040,.017]; concrete [.025,.012,.005,.003] with joints; gravel [.025,.030,.060,.058] plus random small impulses. Concrete joints use assumed 3.6 m spacing with variation. These profiles purposely allow some asphalt/concrete overlap but do not establish their real signatures.

Normal axial rotation leakage is randomized 0.005–0.025 g; axial sensor noise nominal 0.004 g. A randomized rig gain 0.75–1.30 scales responses. Imbalance-like signal adds a 1x axial sinusoid with assumed amplitude gain*(strength/50)*0.16*(rotation_hz/2)^2 g. This is a demonstration response, not a calibrated suspension model. Other periodic abnormality adds 1x/2x/3x components. Impact uses randomized timing/amplitude and a decaying 18 Hz pulse. Road excitation leaks into axial measurements. Different run seeds randomize phase, noise, spectral frequencies and impacts.

Training fault strengths: 30–90; normal 0. All four faults are crossed with all four surfaces AND an airborne low-excitation condition. There are 200 independently parameterized synthetic rig groups, 60 windows/group. Groups 0–139 train (8400), 140–169 validate (1800), 170–199 test (1800). Road model excludes airborne windows, leaving 6720/1440/1440. Adjacent windows from one group do not cross train/test boundaries. Splits are from one simulator family; this does not test transfer to real rigs or another physical model.

## Features and models

Condition features: log axial RMS, crest factor, kurtosis, first-difference RMS, 1x/2x/3x amplitudes and observed rotation frequency. No selected issue/surface metadata is an input.

Road features: observed frequency, gravity-removed tangential RMS/crest/kurtosis/difference RMS, coarse spectral-band energies/fractions, low-frequency energy and original tangential RMS. Projection at the 1x rotation frequency removes most of the gravity component. Finite-window leakage remains.

Two StandardScaler -> 16 ReLU neurons -> 4 softmax outputs networks. Weights, scaling and thresholds exported as namespaced C++ arrays. Condition classifier avoids road-feature inputs; the road classifier is trained across fault combinations. Threshold is selected on validation only; a fixed 0.15 top-two margin also causes uncertainty. Unfamiliar axial standardized values beyond 7 cause rejection in firmware (heuristic). Scores are not calibrated using real data.

Synthetic performance is in training_report.json with confusion matrices, per-class metrics, coverage and definite-decision success. Very high fault scores reflect simulator separability. External real data, especially negative examples and unfamiliar surfaces, are needed before claiming real performance.
