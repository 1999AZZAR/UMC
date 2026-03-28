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

- [ ] Decouple expensive package discovery from time-sensitive device polling.
  - `backend/worker.py::fetch_packages()` runs a blocking launcher query in the same worker thread used for device status, screenshots, toggles, and file operations.
  - Risk: selecting a device can stall every other backend operation until package discovery finishes.

- [ ] Finish replacing broad low-level exception fallbacks in `backend/adb_handler.py` and `backend/scrcpy_handler.py`.
  - Remaining broad handlers still hide command/setup failures in device status reads, pairing, TCP/IP enable, and process launch edge cases.

- [ ] Standardize subprocess execution behind shared helpers.
  - Centralize timeout, `check`, stderr capture, and `last_error` handling for both `adb` and `scrcpy`.
  - Reduce duplicated command boilerplate and inconsistent failure reporting.

- [ ] Fix misleading file-transfer progress reporting.
  - The worker now emits `0` and `100`, but those are still synthetic milestones rather than real transfer progress.
  - Either implement determinate progress from actual byte counts or switch the UI to an honest busy/complete state.

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
