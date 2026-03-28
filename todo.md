# UMC Remaining TODO

This backlog contains only unresolved work after the recent bridge, clipboard, cleanup, and runtime-error-reporting fixes.

## P1 - High Risk / Likely User-Facing Bugs

- [ ] Replace `QThread.terminate()` fallback in `backend/bridge.py`.
  - Current cleanup still terminates the worker thread forcibly if `wait(1000)` times out.
  - Risk: torn-down worker state, leaked subprocesses, and undefined shutdown behavior.

- [ ] Correct device status reporting for WiFi and Bluetooth in `backend/adb_handler.py`.
  - `wifi_enabled` and `bluetooth_enabled` are initialized with defaults but never read from the device.
  - Risk: sidebar switches can display false state and encourage incorrect user actions.

- [ ] Fix airplane-mode broadcast argument handling in `backend/adb_handler.py`.
  - The `am broadcast ... --ez state` path currently passes `"1"` / `"0"` instead of explicit boolean values.
  - Risk: broadcast may not apply correctly on some Android versions even if the setting value changes.

- [ ] Harden icon extraction temp-file lifecycle in `backend/adb_handler.py`.
  - Validate `adb pull` success before opening the APK.
  - Ensure temp APK cleanup also happens on failure paths.
  - Risk: stale temp files, misleading cache misses, and BadZip-style failures from partial pulls.

## P2 - Important Reliability / Robustness

- [ ] Finish replacing broad low-level exception fallbacks in `backend/adb_handler.py` and `backend/scrcpy_handler.py`.
  - Remaining broad handlers still hide command/setup failures in device status reads, pairing, TCP/IP enable, and process launch edge cases.

- [ ] Standardize subprocess execution behind shared helpers.
  - Centralize timeout, `check`, stderr capture, and `last_error` handling for both `adb` and `scrcpy`.
  - Reduce duplicated command boilerplate and inconsistent failure reporting.

- [ ] Surface low-level `adb_handler.last_error` on failed file transfers and screenshots.
  - Current UI shows generic completion/failure states but does not include the actual root cause.

- [ ] Improve package discovery quality in `backend/worker.py`.
  - Use `get_app_label()` or a fallback pipeline instead of package-name guessing only.
  - Filter or classify launcher entries more carefully to avoid noisy/incorrect app names.

- [ ] Rework clipboard sync dependency handling.
  - Detect when the target device lacks the required clipboard command/broadcast support.
  - Show an actionable unsupported/error state instead of silent no-op behavior.

- [ ] Finish device update efficiency work.
  - One full-list re-emit path was reduced, but updates are still per-device and poll-driven.
  - Batch updates or granular model notifications would further reduce redraw churn.

- [ ] Make polling configurable and adaptive.
  - Add a stored poll interval and reduce background polling when idle / no devices are active.

## P3 - Maintainability / Delivery

- [ ] Add automated tests for parsing and bridge-worker flows.
  - Focus: battery parsing, rotation semantics, package parsing, and signal-driven control flows with mocked subprocess calls.

- [ ] Add CI quality gates before packaging.
  - Lint, type-check baseline, and tests should run before release artifact creation.

- [ ] Replace remaining `print()` diagnostics with structured logging.
  - Especially worker/device status and launch/process error paths.

- [ ] Align README claims with actual implementation.
  - Document clipboard limitations, dependency requirements, and supported control behavior more precisely.

- [ ] Review packaging/repo hygiene.
  - Confirm generated Debian artifacts and runtime caches are consistently excluded from commits and releases.
