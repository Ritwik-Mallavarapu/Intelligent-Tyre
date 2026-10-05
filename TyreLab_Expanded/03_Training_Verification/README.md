# Optional training and verification (not needed on friend's laptop)

Training and model tests use Python 3.11+ with NumPy and scikit-learn plus g++ (Linux/Google Colab is convenient). Install requirements-training.txt. On Linux run python train.py, then python test_system.py and python test_firmware_runtime.py. Generator and feature extraction are compiled from the SAME signal_core.h used by the Nano. train.py replaces BOTH Arduino model.h and the friend's model_manifest.json; reupload and redistribute matching files after retraining. Running test_system.py also recomputes the firmware novelty guard's held-out success metric in the report/manifest.

train.py regenerates 12,000 labelled synthetic windows, trains scalers on training groups only, chooses rejection thresholds from validation, exports 2 compact networks and model identity. Raw author datasets are not included or used. The provided synthetic_features.csv columns are group, road (4=airborne), condition, strength, RPM, then 22 features. It is generated data, not measured tyre data.

model_check.cpp evaluates the actual C++ feature/model routines. test_system.py compares all held-out feature rows with Python-exported weights, checks selected scenarios/zero strength, packet codecs, stale/mismatch guards, HTTP, CSV and real BLE worker using a mocked adapter. test_firmware_runtime.py executes the actual .ino under mocked hardware and checks control ACK, mode reset, inference and quality states. check_firmware.py is a host syntax harness, not the full core compile.

The package was ALSO fully compiled using Arduino Mbed OS Nano Boards 4.6.0, ArduinoBLE 2.1.0 and Arduino_BMI270_BMM150 1.2.4. To repeat with Arduino CLI: arduino-cli compile --fqbn arduino:mbed_nano:nano33ble ../01_Arduino_Upload/TyreLabExpanded . Install the matching core/libraries first.

ui_fixture.py serves UI-only MOCK telemetry on port 8004. It never goes into the friend's application. test_browser.cjs exercises the actual dashboard in Chromium against that fixture. Set TYRELAB_BROWSER to your headless Chromium executable and CODEX_PRIMARY_RUNTIME_NODE_MODULES to a folder containing playwright-core. The fixture server and browser must run in the same network environment. Mock UI scores are NOT model-accuracy evidence.

No test here establishes physical sensor readings, Windows adapter behaviour or real-world condition/surface accuracy. Collect full-rate, labelled real recordings before retraining for physical deployment; current dashboard CSV is decimated telemetry.
