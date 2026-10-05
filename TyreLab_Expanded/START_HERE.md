# Entra Innovations · Intelligent Tyre

This is a separate upgrade. Your previously uploaded TyreLabRev2 firmware remains available as a backup in 04_Backup. The expanded website requires ONE new upload of TyreLabExpanded.ino. After that, all source/scenario changes happen on the website.

## Start in this order

1. Extract the entire ZIP using Windows Extract All into a fresh folder. Do not run files inside the ZIP viewer.
2. Double-click RUN_DASHBOARD.bat in the top-level TyreLab_Expanded folder. It finds Python, prepares or repairs dependencies, starts the server, then opens the correct address. Install Python 3.11 or 3.12 with its launcher if prompted. First-time Bluetooth setup needs internet.
3. KEEP the dashboard console open. Use the SERVER READY URL it prints. Do not manually type an old port 8000 address. The website must open even when no Nano is powered; the connection status will show the Bluetooth problem. RUN_DASHBOARD.bat also reopens a healthy server already running from this same folder.
4. Upload the complete protocol-2 TyreLabExpanded sketch if you have not already uploaded the preceding audited release. This launcher repair does not change the firmware. Firmware from before the protocol-2 release needs updating.
5. Power the Nano, enable laptop Bluetooth, close Arduino Serial Monitor and other BLE apps. Both modes require the Nano. Start with Onboard simulation and wait for Connected, Receiving data, Matches package and Board acknowledged settings.
6. Choose surface/issue/strength/RPM and Apply. Allow around 3 seconds after acknowledgement for a full window. Then check Live while stationary; Too slow is expected.
7. If the server cannot start, its console explains the error. App output is saved in 02_Friend_Demo/logs/startup.log; Bluetooth details are in diagnostics.log. Run RUN_DIAGNOSTICS.bat and send its output if connection still fails. OPEN_DASHBOARD.bat now starts or reopens the server too.

## What runs where

Nano: raw sensor sampling OR synthetic signal generation, feature extraction, both neural networks, quality checks and BLE telemetry.
Laptop: Bluetooth connection, settings commands, local HTML dashboard and CSV logging. It never evaluates a neural network.

Simulation selects a signal source, not an answer. Both networks receive features calculated from generated motion; neither receives selected class labels. The two prediction heads use separate compact networks so a fault and surface can coexist. They fit comfortably on the Nano. This is not an exact mechanical diagnosis or production TPMS.

## Classes and controls

Condition: Normal; Imbalance-like periodic vibration; Other periodic abnormality; Impact; Uncertain.
Surface: Smooth asphalt; Rough asphalt; Concrete; Gravel; Uncertain.

For imbalance, strength is synthetic added mass in grams, 0–100 g. Its vibration response is an assumption, not a calibrated mass measurement. Other abnormality/impact strength is a 0–100% simulation parameter. Normal adds no fault regardless of strength. Fault training uses strength 30–90. Low or very high settings are exploratory and may return Normal/Uncertain. Selected impact creates a repeated impact within each generated window, for visual demonstration; it is not a literal reconstruction of a pothole drive.

Live mode is deliberately configured for your AIRBORNE wheel rig. Road prediction is unavailable because the tyre does not contact a road. Moving the board into a tyre does not turn the freely spinning rig into road data. Real vehicle-road operation is outside this package's validated scope.

Environment values are simulated in Onboard simulation, measured in Live sensors. Live pressure is AMBIENT ABSOLUTE PSI; it is not tyre inflation pressure. The onboard LPS22HB's 260–1260 hPa range cannot measure normal inflated-tyre pressure. Local board temperature is not tyre-core temperature.

## Evidence and limits

Training data is ENTIRELY SYNTHETIC. Published studies motivate rotation harmonics and temporal/spectral features. Their measured datasets were not used, and their results are not transferred to this system. See SOURCES_AND_SIMULATION.md and 03_Training_Verification/training_report.json.

Very high synthetic accuracy means the model can recognize this simulator's patterns. It does not establish physical performance. Condition responses depend strongly on wheel support, mounting and the mass of the installed board/battery. Smooth asphalt and concrete can overlap even in simulation, and overlap more in real driving.

Scores are uncalibrated model outputs, not measured real-world probabilities. Uncertain is produced by a top score below 65%, a top-two score gap below 15 percentage points, or unsuitable/unfamiliar data. Invalid data suppresses scores rather than inventing percentages. The novelty check is a heuristic and cannot guarantee recognition of every out-of-distribution signal.

Read TEST_RESULTS.md for actual compile and software verification. Actual Nano sensor operation, real BLE and Windows Bluetooth adapter behaviour, physical mounting and accuracy still require your checks.

## Connection recovery in this audited release

This release uses telemetry protocol 2. Firmware from before the protocol-2 audit needs a new upload; the preceding audited protocol-2 sketch is unchanged. Use the Arduino and laptop files from this same ZIP. Extract to a fresh writable folder; close old demo consoles, Serial Monitor and phone Bluetooth apps. Power-cycle the Nano, then run START_DEMO.bat and keep its window open. Use Chrome or Edge with the printed SERVER READY URL. USB powers/programs the board; dashboard data uses Bluetooth.

If connection fails, keep START_DEMO running and double-click RUN_DIAGNOSTICS.bat. Copy its complete output and the last console error for troubleshooting. OLD_FIRMWARE means upload is required; NO_BOARD means the BLE advertisement was not found. Do not run competing Bluetooth apps while using the dashboard. HTTP now remains available while BLE retries; stopped telemetry is visibly marked stale, and scores are hidden.

## Windows native-crash repair

The reported code 3221225477 (0xC0000005) means the earlier process crashed after starting HTTP. This package runs Bluetooth in a separate process, with Windows COM preparation on its main asyncio thread. A Bluetooth crash must not terminate HTTP; the dashboard reports it and retries. This is containment plus a threading correction, not proof that the underlying Windows driver/library issue is resolved. If readings still fail, send logs/bluetooth_worker.log and logs/diagnostics.log from 02_Friend_Demo. No Arduino firmware or model changes were made in this repair. Extract into a fresh folder and run RUN_DASHBOARD.bat.
