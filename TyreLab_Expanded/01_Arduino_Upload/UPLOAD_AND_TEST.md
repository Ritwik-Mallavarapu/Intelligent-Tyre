# Upload and check the expanded firmware

1. Open Arduino IDE. Board package: Arduino Mbed OS Nano Boards 4.6.0. Select Arduino Nano 33 BLE and your board's USB port.
2. Library Manager: install ArduinoBLE 2.1.0 and Arduino_BMI270_BMM150 1.2.4, the versions tested here. Select those versions in the Library Manager version menu. Wire is included in the core.
3. Open TyreLabExpanded/TyreLabExpanded.ino. Keep model.h and signal_core.h in the SAME sketch folder. Do not combine these files with your old sketch/model.
4. Verify, then upload. If necessary double-tap reset and select the bootloader port. The firmware starts without waiting for USB.
5. Start the new friend dashboard. The BLE name is TyreLabExpanded. Close nRF Connect or other apps connected to the board; Windows pairing is not needed first.
6. Start Onboard simulation. Expect settings acknowledgement, then scores after about one full 256-sample window. Select imbalance on smooth asphalt, 50 g, 120 RPM and apply. Try zero grams: the selected label must not force an abnormal prediction. Try the other surfaces/issues. Smooth asphalt/concrete may give Uncertain.
7. Switch to Live sensors, while stationary. Too slow is correct. Actual temperature/pressure should appear in seconds. Check acceleration magnitude sqrt(X^2+Y^2+Z^2) is about 1 g while stationary. If it is about 4 g or 0.25 g, do not spin: check the installed BMI270 library/version.

## Sensor settings and power

The firmware sets accelerometer ACC_RANGE to 16 g and verifies the register. The tested official library converts raw acceleration assuming 4 g, so firmware multiplies reported acceleration by 4. Gyroscope range is 2000 degrees/s. These limits still restrict wheel speed and impacts.

LPS22HB and HS3003 are read directly over Wire1. No extra environment sensor libraries are needed. Temperature conversion is split across loop iterations to avoid a blocking conversion delay. IMU/sensor errors appear on the dashboard. A BLE-startup failure cannot report via BLE; it flashes LED and reports on USB Serial at 115200.

Disconnect external battery before uploading by USB. For rotation use a suitable onboard battery supply; e.g. protected 3.7 V battery through regulated 5 V boost to VIN/GND. Never put 3.7/4.2 V onto 3V3. Secure the battery, board, converter and wires to the wheel; avoid loose breadboard/jumpers.

## Outside mounting

Board face parallel to wheel face, components outward, Z along the axle. Long board dimension radial; USB toward wheel centre. Mount on a rigid insulated bracket fixed to metal rim near valve, not rubber or valve. The bracket/board rotates with the wheel. Include its complete mass and battery in the balanced baseline.

With motor off, turn by hand and confirm gyro Z dominates. Then use a guarded rig, start about 100–120 RPM, keep within 78–162 RPM, and wait 6 seconds at steady speed. Fully stop before changing test weights. Never loosen wheel nuts, axle supports or damage tyres to simulate dangerous faults. A freely spinning rigid rig may show little axial response to a 50–60 g imbalance.

Temperature/ambient barometer readings do not diagnose pressure leaks. Do not put the bare board/battery in an inflated tyre as a pressure-sensing substitute. Moving the board later changes sensor orientation/response and needs fresh validation.

## Physical validation

Live dashboard labels annotate the CSV and never change model output. Use a distinct run ID for each independent normal/weighted start and record its true condition. After steady speed wait 6 seconds, then collect at least 20 seconds. Aim for 10 baseline and 10 secured-weight runs in randomized order at matched speeds. Do not count packets/windows from one spin as independent experiments.

The CSV is decimated display telemetry (~25 Hz), not a complete ~100 Hz raw training recording. Supplying it later can help diagnose behaviour, but robust retraining needs full-rate labelled acceleration/gyro logs and independent runs; request a full-rate acquisition mode before the real-data campaign.

Compiled binaries are included in Compiled_Firmware for traceability. Arduino IDE upload of the .ino is the intended beginner route; do not replace a bootloader manually.
