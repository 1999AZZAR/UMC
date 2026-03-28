# UMC Remaining TODO

This backlog contains only unresolved work after the recent bridge, clipboard, cleanup, and runtime-error-reporting fixes.

## P1 - High Risk / Likely User-Facing Bugs

- [ ] Track and clean up all scrcpy sessions, not just app-launch sessions.
  - `backend/scrcpy_handler.py` only stores processes created by `launch_app()`.
  - `mirror()` and `create_display()` start detached processes but never add them to `_processes`.
  - Risk: `bridge.cleanup()` cannot stop mirrored/virtual-display windows, leaving orphaned scrcpy sessions behind.

- [ ] Harden ADB setter methods against missing binaries and subprocess failures.
  - `set_volume`, `set_brightness`, `set_rotation_lock`, `set_airplane_mode`, `set_wifi_enabled`, and `set_bluetooth_enabled` still call `subprocess.run(...)` directly.
  - Risk: `adb` missing or command execution errors can raise exceptions out of worker slots and produce inconsistent UI state.

- [ ] Stop reporting fake success for airplane-mode changes.
  - `backend/adb_handler.py` currently returns `True` from `set_airplane_mode()` regardless of command results.
  - Risk: the UI reports success even when the device rejected the operation.

## P2 - Important Reliability / Robustness

- [ ] Prevent polling backlog in the worker thread.
  - `backend/bridge.py` emits `requestDevices` every 3 seconds and then emits one `requestDeviceStatus` per device on each refresh.
  - With slow ADB calls or multiple devices, requests can queue faster than the single worker thread can drain them.
  - Risk: stale device status, delayed controls, and steadily growing latency under load.

- [ ] Decouple expensive package discovery from time-sensitive device polling.
  - `backend/worker.py::fetch_packages()` runs a blocking launcher query in the same worker thread used for device status, screenshots, toggles, and file operations.
  - Risk: selecting a device can stall every other backend operation until package discovery finishes.

- [ ] Reduce clipboard polling overhead when sync is enabled.
  - `backend/bridge.py::_on_device_status_ready()` requests clipboard contents on every status refresh for synced devices.
  - Risk: unnecessary ADB traffic every poll cycle and extra queue pressure in the worker thread.

- [ ] Finish replacing broad low-level exception fallbacks in `backend/adb_handler.py` and `backend/scrcpy_handler.py`.
  - Remaining broad handlers still hide command/setup failures in device status reads, pairing, TCP/IP enable, and process launch edge cases.

- [ ] Standardize subprocess execution behind shared helpers.
  - Centralize timeout, `check`, stderr capture, and `last_error` handling for both `adb` and `scrcpy`.
  - Reduce duplicated command boilerplate and inconsistent failure reporting.

- [ ] Surface low-level `adb_handler.last_error` on failed file transfers and screenshots.
  - Current UI shows generic completion/failure states but does not include the actual root cause.

- [ ] Fix misleading file-transfer progress reporting.
  - The worker emits progress `0` and then completion, but never reports real intermediate progress.
  - Risk: the UI appears to support progress tracking while providing inaccurate information.

- [ ] Improve package discovery quality in `backend/worker.py`.
  - Use `get_app_label()` or a fallback pipeline instead of package-name guessing only.
  - Filter or classify launcher entries more carefully to avoid noisy/incorrect app names.

- [ ] Expand the new keyevent control path into a configurable command layer.
  - The generic `send_keyevent(serial, code)` path now exists, but the UI only exposes a small hardcoded quick-action set.
  - Add a reusable keyevent catalog / command palette so navigation, media, and TV-style controls do not require one-off UI wiring each time.

- [ ] Rework clipboard sync dependency handling.
  - Detect when the target device lacks the required clipboard command/broadcast support.
  - Show an actionable unsupported/error state instead of silent no-op behavior.

- [ ] Finish device update efficiency work.
  - One full-list re-emit path was reduced, but updates are still per-device and poll-driven.
  - Batch updates or granular model notifications would further reduce redraw churn.

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
