# Entra Innovations — Intelligent Tyre

Intelligent Tyre is a prototype for local wheel-motion analysis, selectable synthetic demonstrations and wireless sensor monitoring. The TPMS sensor module calculates features and neural-network scores. A local web dashboard displays telemetry, sends settings and records received data.

**This is a demonstration system. Training data is entirely synthetic; real-world fault and road-classification accuracy has not been established.** The current pressure measurement is ambient absolute pressure, not tyre inflation pressure.

## Features

- Condition scores: Normal, Imbalance-like periodic vibration, Other periodic abnormality and Impact.
- Surface scores: Smooth asphalt, Rough asphalt, Concrete and Gravel.
- Uncertain decisions when the scores are insufficiently clear.
- Live physical sensing and sensor-generated simulation, selectable without changing firmware.
- Rotation speed, acceleration, local temperature, ambient pressure and data-quality status.
- Entra branding and locally bundled logo; normal operation requires no cloud service.
- CSV recording, reconnect handling, stale-data suppression and isolated Bluetooth processing.

## Requirements

| Item | Requirement |
|---|---|
| Sensor | Compatible module running this package's protocol-2 firmware and matching model |
| Computer | Windows or Linux, with a Bluetooth Low Energy adapter |
| Python | 3.11 or 3.12, including virtual-environment support |
| Python dependency | Bleak 0.22.3; installed by the launcher |
| Browser | A modern browser; Chrome or Edge is convenient on Windows |
| Linux Bluetooth | BlueZ service, enabled adapter and appropriate user access |
| Internet | Needed for first-time dependency installation or repair |

Both Live and Simulation require the physical module to be powered and connected. Simulation runs on the module, not on the laptop.

The `.bat` and `.sh` files are application launchers. This package does not contain standalone Windows or Linux executables.

## Folder structure

```text
TyreLab_Expanded/
├── RUN_DASHBOARD.bat             Windows entry point
├── RUN_DASHBOARD.sh              Linux entry point
├── README.md
├── BRANDING.md
├── SOURCES_AND_SIMULATION.md
├── TEST_RESULTS.md
├── 01_Arduino_Upload/
│   ├── UPLOAD_AND_TEST.md
│   ├── TyreLabExpanded/
│   │   ├── TyreLabExpanded.ino
│   │   ├── signal_core.h
│   │   └── model.h
│   └── Compiled_Firmware/
├── 02_Friend_Demo/
│   ├── START_DEMO.bat
│   ├── START_DEMO.sh
│   ├── SETUP_WINDOWS.bat
│   ├── OPEN_DASHBOARD.bat
│   ├── RUN_DIAGNOSTICS.bat
│   ├── launcher.py
│   ├── app.py
│   ├── ble_transport.py
│   ├── protocol.py
│   ├── diagnostics.py
│   ├── CHECK_INSTALLATION.py
│   ├── requirements.txt
│   ├── model_manifest.json
│   └── static/
│       ├── index.html
│       ├── style.css
│       ├── app.js
│       └── entra-logo.png
├── 03_Training_Verification/
└── 04_Backup/
```

`.venv`, `logs` and `dashboard_url.txt` are generated during operation.

## Firmware preparation

Use the firmware, model header and laptop manifest from the same package. Follow [UPLOAD_AND_TEST.md](01_Arduino_Upload/UPLOAD_AND_TEST.md) for the tested build dependencies and upload procedure.

The BLE advertisement name remains **TyreLabExpanded** for compatibility. Entra branding and the TPMS terminology are presentation changes; they do not rename the BLE service or alter its protocol.

Dashboard wording, chart and launcher updates do not require a firmware upload. Firmware predating protocol 2 requires an update.

## Archive layout

The supplied archive contains an outer `TyreLab_Expanded_Final` folder and an inner `TyreLab_Expanded` application folder. The application root is the folder containing `RUN_DASHBOARD.bat` and `RUN_DASHBOARD.sh`. Place this README there. The chart-clipping correction, TPMS wording and both operating-system launchers are already included.

The supplied archive also contains a virtual environment and runtime logs from an earlier installation. They are not required source files. The launcher checks the environment before using it; create a fresh environment when moving between computers or operating systems. For a clean redistribution, exclude `.venv`, `logs`, `__pycache__` and `dashboard_url.txt`.

## Windows quick start

1. Extract the entire application into a writable folder using **Extract All**. Do not launch it inside the ZIP viewer.
2. Power the module and enable laptop Bluetooth. Close other applications connected to the module.
3. Double-click **RUN_DASHBOARD.bat** in the top-level folder.
4. Allow first-time dependency installation. If Python cannot be found, install Python 3.11 or 3.12 with its launcher.
5. Keep the console open. Wait for **SERVER READY** and use the exact URL printed there.
6. Wait for **Connected**, **Receiving data**, **Matches package** and **Sensor acknowledged settings**.

The server normally uses `http://127.0.0.1:8000`. If that port is unavailable, it can select another port. Do not reopen an old bookmarked address without checking the current console.

`02_Friend_Demo/OPEN_DASHBOARD.bat` starts or reopens the application. `SETUP_WINDOWS.bat` is available for manual dependency setup.

## Linux quick start

1. Transfer the complete application folder, excluding `.venv`, `logs` and `dashboard_url.txt`.
2. Install Python 3.11 or 3.12 with virtual-environment support.
3. Ensure BlueZ is installed, Bluetooth is enabled and your user can access the adapter.
4. Open a terminal in the top-level application folder and run:

```bash
bash RUN_DASHBOARD.sh
```

The launcher creates a Linux virtual environment and installs dependencies on first use. Keep the terminal open and use the printed server address.

On systems using systemd, inspect the Bluetooth service with:

```bash
systemctl status bluetooth
```

If environment creation fails, install the virtual-environment package matching the Python version selected by the launcher. Package names and availability depend on your Linux distribution.

**Do not copy a Windows virtual environment to Linux.** Linux Bluetooth uses BlueZ through D-Bus; Windows uses its native Bluetooth APIs through WinRT. Physical Linux Bluetooth operation must be checked on the target computer.

## Simulation mode

1. Select **Sensor simulation**.
2. Choose a surface and condition.
3. Set strength and simulation RPM.
4. Click **Apply & restart window**.
5. Wait for settings acknowledgement, then approximately three seconds for a complete inference window.

For an initial demonstration, use **120 RPM** and **50 g** for imbalance-like vibration, or **50%** for another abnormality. **New random run** changes the simulator seed.

| Control | Meaning |
|---|---|
| Imbalance strength | Assumed added mass, 0–100 g; not a measured mass estimate |
| Other abnormality / impact strength | Synthetic intensity, 0–100% |
| Normal | Adds no selected fault; surface excitation remains |
| RPM | Supported simulation range: 78–162 |

Fault training used strengths 30–90. Values outside that interval are exploratory and may produce Normal or Uncertain. Selecting a scenario modifies the input waveform; it does not force the classifier's output.

Pressure and temperature are simulated in this mode. The impact scenario produces repeated demonstration events across windows.

## Live mode

Select **Live sensors** to use physical measurements. Simulation sliders disappear.

The live configuration is intended for a freely spinning, airborne wheel rig. It therefore displays **Road surface unavailable**. There is no tyre–road contact signal to classify.

A stationary module should report **Too slow**. Classification requires suitable mounting, sufficiently steady rotation and valid sensor data. The supported range is 78–162 RPM.

The intended axes are X radial inward, Y tangential and Z along the axle. Follow [UPLOAD_AND_TEST.md](01_Arduino_Upload/UPLOAD_AND_TEST.md) for mounting and physical test checks. Stop the rig before making mechanical changes; use the established guarded test setup.

The pressure sensor measures ambient absolute pressure. Its range is unsuitable for normal inflated-tyre pressure. Local temperature is not tyre-core temperature. These measurements are not inputs to the current motion classifiers.

## How the system works

1. Digital sensors communicate with the microcontroller over I²C, or the firmware generates synthetic motion.
2. The firmware collects 256 samples at a nominal 99.84 Hz: approximately 2.56 seconds per non-overlapping window.
3. C++ feature extraction calculates 22 statistics and frequency features. Condition inference uses 8 features; surface inference uses 15, with rotation frequency shared.
4. Two neural networks calculate four class scores each. Their standardisation constants, weights and biases are embedded in `model.h`.
5. Binary BLE GATT packets carry motion, environment and scores to the laptop. Commands travel back through a writable characteristic.
6. Python validates packets, records telemetry and serves the local dashboard through HTTP/JSON.
7. JavaScript polls the state endpoint and draws charts using Canvas.

Each model is a **standardised input → 16 ReLU neurons → 4 softmax outputs** network. Training uses scikit-learn; deployed inference uses direct C++ calculations rather than TensorFlow Lite.

**Processing boundary:** feature extraction, neural-network scores and sensor-quality checks run on the module. The Python backend applies the score threshold and margin to select the displayed class or Uncertain, and adds freshness checks. It does not evaluate either neural network.

### Communication

| Link | Protocol |
|---|---|
| Physical sensors → microcontroller | I²C |
| Module ↔ laptop | BLE GATT, little-endian binary packets |
| Bluetooth worker ↔ server | JSON over local subprocess pipes |
| Server ↔ browser | HTTP with JSON |
| Recording | CSV |

The custom service is `8c220001-89ab-4cde-9012-34567890abcd`. Motion, environment and scores use 20-byte Read/Notify characteristics. Control uses a 14-byte Write characteristic. See `protocol.py` for exact formats and scaling.

Motion telemetry is approximately 25 Hz. New inference scores are calculated once per completed window; environmental/status heartbeats are approximately 1 Hz. Browser polling is approximately four times per second.

## Scores and data quality

Scores are **uncalibrated model outputs**, not verified real-world probabilities.

A displayed class requires a valid, fresh result, a top score of at least 65% and a lead of at least 15 percentage points over the second-highest score. Otherwise the dashboard can show Uncertain.

The firmware rejects unsuitable windows for clipping, invalid speed, irregular sampling, mounting problems, missing motion readings, unstable rotation or unfamiliar condition features. These are quality/status decisions, not additional trained fault categories.

The application checks the model ID, operating mode, command request ID, packet sequence and advancing inference-window sequence. Stale results are hidden. Identical command retries acknowledge settings without repeatedly restarting the inference window.

Bluetooth runs in a separate process so that a native Bluetooth-worker crash can be reported and retried without terminating the HTTP server.

## Recordings

Logs are written to `02_Friend_Demo/logs/`.

| File | Purpose |
|---|---|
| `expanded_*.csv` | Received motion, environment, scores and metadata |
| `startup.log` | Server output captured by the launcher |
| `diagnostics.log` | Application and Bluetooth error details |
| `bluetooth_worker.log` | Bluetooth operations and native-crash diagnostics |

Use **Download session CSV** to export the current recording. In Live mode, a run ID and known-condition label annotate the recording; they do not change predictions.

**The CSV contains received motion telemetry at approximately 25 Hz, not the full internal 100 Hz sample stream.** Full-rate raw capture or feature export is needed for a subsequent full-resolution training campaign.

## Troubleshooting

| Symptom | Action |
|---|---|
| Connection refused / backend unavailable | Check that the launcher console is still running. Use its current SERVER READY URL. |
| Missing Python or environment setup failed | Install Python 3.11/3.12 with venv support; inspect the console installation error. |
| Sensor found but no connection | Close competing BLE applications, power-cycle the sensor and inspect the Bluetooth logs. |
| OLD_FIRMWARE or MODEL_MISMATCH | Use matching protocol-2 firmware and laptop files from the same package. |
| Stationary live module says Too slow | Expected; a rotating-wheel classification requires suitable rotation. |
| Clipping, mounting or speed warning | Correct the physical acquisition problem; do not interpret suppressed scores as a fault diagnosis. |
| Road unavailable in Live | Expected for the airborne rig. |
| Linux cannot access Bluetooth | Check BlueZ, adapter power, user access and the worker log. |
| Native worker exits with 0xC0000005 | Preserve the worker/diagnostic logs. The isolated server should remain available while Bluetooth retries. |
| Chart traces overlap axis text | This archive already includes the clipping fix. Refresh using Ctrl+F5 and verify that the running server uses this application folder. |

On Windows, run `02_Friend_Demo/RUN_DIAGNOSTICS.bat`. On Linux, from `02_Friend_Demo`, run:

```bash
.venv/bin/python diagnostics.py
```

When requesting help, send the full diagnostic output and relevant logs. A successful advertisement scan confirms discovery, not successful GATT connection or telemetry.

## Training and verification

The dataset contains **12,000 entirely synthetic windows**, generated from 200 independently parameterised rig groups. Whole groups are separated into training, validation and test sets. Research informed mechanisms and features; measured author datasets were not used.

| Model | Held-out windows | Highest-score accuracy |
|---|---:|---:|
| Condition | 1,800 | 100.00% |
| Road surface | 1,440 | 97.43% |

Road success is 96.11% when uncertain decisions count as unsuccessful. These figures measure performance within the engineered simulator family, not real-road accuracy.

Checks include model-export agreement, packet validation, mock BLE operation, all 16 default surface/condition combinations, injected Bluetooth-worker crashes, server startup/recovery, and desktop/mobile chart rendering. Physical sensor response, target-adapter operation and real classification require independent validation.

See [TEST_RESULTS.md](TEST_RESULTS.md), [SOURCES_AND_SIMULATION.md](SOURCES_AND_SIMULATION.md) and the scripts in `03_Training_Verification/` for evidence and reproducibility.

## Scope and next steps

The prototype does not currently establish puncture detection, inflation-pressure monitoring, tyre wear estimation, exact imbalance mass or universal diagnosis of mechanical faults.

Next development steps are labelled full-rate physical recordings, evaluation across independent runs and mounting configurations, model retraining and calibration, a suitable inflation-pressure sensor, and validation in the intended environment.

Entra's original logo is bundled locally. Asset source and colour details are documented in [BRANDING.md](BRANDING.md).
