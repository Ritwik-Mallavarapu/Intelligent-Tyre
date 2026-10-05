# Windows quick start

Extract All from the ZIP into a new folder, then double-click RUN_DASHBOARD.bat in the parent folder, or START_DEMO.bat here. First setup is automatic and needs Python 3.11 or 3.12 plus internet. SETUP_WINDOWS.bat remains available for manual dependency setup.

Keep the server console open. Wait for SERVER READY and use its exact URL. Do not manually open a remembered port 8000 address. OPEN_DASHBOARD.bat will now start the server if stopped, or reopen a healthy server from this folder. Missing Bluetooth dependencies should produce a dashboard status, rather than prevent the website from starting.

Power the Nano and enable Bluetooth. Use the protocol-2 TyreLabExpanded firmware from this ZIP. If you already uploaded the preceding audited protocol-2 firmware, it is unchanged. Close Serial Monitor and other Bluetooth apps. USB supplies power/programming; telemetry uses BLE.

Wait for Connected, Receiving data, Matches package and Board acknowledged settings. Apply a synthetic scenario and wait for a complete 2.56-second window. In Live, sliders disappear and the airborne rig shows Road surface unavailable.

If startup fails, send the console error or logs/startup.log. If the page opens but BLE fails, run RUN_DIAGNOSTICS.bat and send all output. No internet connection is needed for normal operation once dependencies are installed.

## Windows native-crash repair

The reported code 3221225477 (0xC0000005) means the earlier process crashed after starting HTTP. This package runs Bluetooth in a separate process, with Windows COM preparation on its main asyncio thread. A Bluetooth crash must not terminate HTTP; the dashboard reports it and retries. This is containment plus a threading correction, not proof that the underlying Windows driver/library issue is resolved. If readings still fail, send logs/bluetooth_worker.log and logs/diagnostics.log from 02_Friend_Demo. No Arduino firmware or model changes were made in this repair. Extract into a fresh folder and run RUN_DASHBOARD.bat.
