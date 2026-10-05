# Final verification report

All listed software checks passed after the final code changes.

Full Arduino compile: Mbed Nano core 4.6.0; ArduinoBLE 2.1.0; BMI270/BMM150 library 1.2.4. Target arduino:mbed_nano:nano33ble. Firmware uses 373888 bytes flash (38%), 76240 bytes global RAM (29%). Compiled .hex/.bin included.

Executed actual firmware source under mocked hardware: all 16 default surface/fault simulations, inference and packet serialization; control acknowledgement; live reset/road-score suppression; slow, clipped, irregular and unstable guards; invalid-command rejection.

Model checks: all 1800 held-out condition windows checked with exported Python weights against compiled C++; maximum score difference 1.21e-6. All 16 default surface/fault combinations produce the correct condition; road is correct or abstains. Zero-severity fault selections do not force abnormal labels.

Packet/application checks: units and missing-value handling, model identity, source/request acknowledgement guards, stale motion/predictions, uncertainty, clipping, finite settings validation, CSV, HTTP/static routes, foreign-origin rejection. Actual BLE worker exercised with a mocked adapter for handshake and mode/scenario changes.

Chromium checks: actual HTML/CSS/JS rendered, mode switches, simulation sliders hidden in Live, live road unavailable, source/pressure labels, grams label, mobile viewport without horizontal overflow, no JS exceptions. Screenshots visually inspected. UI mock telemetry only; screenshots are not model evidence.

Held-out synthetic results:

| Head | Test windows | Top-label accuracy | Coverage | Accuracy among definite predictions | Success counting uncertain wrong |
|---|---:|---:|---:|---:|---:|
| condition | 1800 | 100.00% | 100.00% | 100.00% | 100.00% |
| road | 1440 | 97.43% | 97.57% | 98.51% | 96.11% |

The high scores reflect separability inside ONE engineered simulator family. All training data is synthetic and source-guided, not measured research data. No physical accuracy claim follows.

Not tested here: upload on the user's Nano, physical sensors, actual BLE radio/Windows adapter, spinning rig response, real roads or internal tyre installation. Source code compiles and software contracts pass; hardware validation still belongs to the user before the demo.

## Raw final check outputs

```text
Final integration/model checks
Firmware host syntax/Arduino symbol-collision check passed. Full Arduino core compile and hardware test remain required.
All 1800 test windows: compiled C++ / exported Python weights agree; max error 1.2023105446790083e-06
All 16 default surface/fault combinations and zero-severity non-forced predictions passed
Exact deployed condition success including novelty: 1.0
Packet units, ack/source guards, clipping, uncertainty, mismatch, stale data, settings validation, HTTP/static/CSV and origin checks passed
Actual BLE worker: handshake, acknowledged settings and live/synthetic switch passed using mocked adapter
ALL SOFTWARE CHECKS PASSED. Physical sensors/BLE/real classification require hardware checks.

```

```text
Actual firmware host execution
Actual firmware runtime: all 16 simulations, onboard predictions, settings ACK, live reset/road suppression, slow/clipped/irregular/unstable guards and invalid-control rejection passed.
Firmware host syntax/Arduino symbol-collision check passed. Full Arduino core compile and hardware test remain required.

```

```text
Full Arduino core compile
Sketch uses 373888 bytes (38%) of program storage space. Maximum is 983040 bytes.
Global variables use 76240 bytes (29%) of dynamic memory, leaving 185904 bytes for local variables. Maximum is 262144 bytes.

```

```text
Chromium desktop/mobile UI checks
Real Chromium UI: mode switches, hidden live slider, surface/issue controls, grams label, pressure meaning, mobile layout and no JS errors passed.

```

```text
Python syntax

```


## Reliability audit

Protocol 2 tags motion, environment and scores with the current command request. Old or out-of-order packets are rejected. Missing sensor values have explicit sentinels. Repeated command retries acknowledge without restarting inference. Predictions must advance through new windows, not merely repeat old notifications. Gyro freshness and mounting direction checks suppress unsuitable live data. Synthetic timing uses the logical simulator clock.

The server waits for a verified HTTP health response before opening the browser, chooses an available local port, and continues serving during BLE reconnects. Lost acknowledgements are recovered by characteristic reads; stalled notifications trigger reconnects. Older firmware is identified explicitly. CSV write failures do not halt telemetry. Windows Bluetooth and the physical Nano remain untested here.

Additional executed reliability checks: three real HTTP startup/restart cycles with port 8000 occupied, automatic port fallback, health/state responsiveness while no BLE adapter is available, explicit Apply restart and invalid restart rejection. All passed.

## Website launch repair after ERR_CONNECTION_REFUSED screenshot

Compared the previous working TyreLabRev2 launch path with the expanded application. Both serve localhost using Python. The screenshot establishes that the selected port was unreachable; it does not identify the exact Windows startup exception. The revised entry point checks runtime dependencies, repairs a missing environment, discovers this installation's existing healthy server and opens the actual live port. Missing BLE dependencies no longer block HTTP startup. OPEN_DASHBOARD starts a stopped server. A top-level RUN_DASHBOARD.bat removes ambiguity about which file to run. Child output is captured in startup.log.

No firmware or model changes in this launch repair. Windows batch scripts were inspected but cannot be executed on this Linux test host. Physical Windows adapter operation and the exact original startup failure remain unverified until the user's console/diagnostics are available.

Final launch checks passed: fresh virtual environment installation; dependency repair while the launcher is running from the environment; paths containing spaces; second-launch server reuse; rejection of unrelated server responses; three startup/restart cycles with port 8000 occupied; HTTP health and state during absent BLE; real launcher HTTP startup with an injected dependency-install failure. Full Arduino compile, 16 default simulation combinations, exported model consistency, packet/application mocks and Chromium UI checks passed again. Tests ran on Linux, not the user’s Windows computer.

## Native-crash repair (reported Windows exit 3221225477)

The exit code is 0xC0000005: a native access violation. The original log establishes successful HTTP startup followed by a process crash. It does not prove which native module caused it. BLE/WinRT is the leading suspect because BLE initialization follows HTTP startup.

Bluetooth now runs in a disposable subprocess. Windows COM setup and the asyncio BLE event loop execute on that process's main thread. The HTTP process does not import Bleak. Byte-preserving RPC carries discoveries, connections, GATT reads/writes and notifications. Native worker exits become explicit dashboard errors, suppress stale predictions and trigger replacement. Operation logs plus Python faulthandler output go to bluetooth_worker.log.

Executed tests: real subprocess RPC against a fake BLE implementation; exact byte read/write/notifications; unexpected worker termination and restart; actual HTTP server surviving a deliberately terminated Bluetooth worker; stale prediction suppression and failed-operation logging; server restart/port/dependency tests; protocol/application mock BLE tests; 1800 model consistency windows and all 16 default firmware simulations. Physical Windows BLE and underlying native crash cause remain unverified. The firmware/model and previously compiled binaries are unchanged.

References: https://learn.microsoft.com/en-us/shows/inside/c0000005 ; https://bleak.readthedocs.io/en/stable/troubleshooting.html#not-working-when-threading-model-is-sta

BLE connection comparison: the older working collector used BleakClient(device, timeout=15) with no Windows service-cache override. This repair restores those ordinary connection defaults in the native worker while retaining expanded protocol validation/control/inference. The high-resolution logo, company/project title, white layout and blue/orange palette are locally bundled. No external calls are required to render the dashboard.

Final branding/repair verification: real Chromium rendered the Entra logo at its original intrinsic width, company/project title, blue/orange light layout, live/simulation switching and mobile layout without horizontal overflow or JavaScript exceptions. Desktop and mobile screenshots visually inspected. UI fixture values are mock telemetry and are not evidence of physical connection. All native-crash containment, RPC bytes, model/application and default firmware scenario tests passed after the communication changes. Full Arduino compilation was previously completed; the firmware and compiled binaries are unchanged in this release. Actual Windows/Nano connection still requires user confirmation.
