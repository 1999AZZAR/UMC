# UMC Improvement TODO

This TODO is prioritized by impact on correctness, user-facing reliability, and engineering maintainability.

## P1 - Critical (Implement First)

- [x] Implement missing bridge slots used by QML to prevent runtime action failures.
  - [x] Add `@Slot(str, int, result="QVariantMap") def enable_tcpip_mode(...)` in `backend/bridge.py`.
  - [x] Add `@Slot(str, list) def launch_app_on_multiple_devices(...)` in `backend/bridge.py`.
  - [x] Validate these are callable from `ui/components/DeviceSidebar.qml` and `ui/components/AppGrid.qml`.
  - Why: UI currently calls methods that do not exist, causing broken workflows at runtime.

- [x] Wire file-transfer signals to worker handlers.
  - [x] Connect `requestPushFile -> self._worker.push_file` in `BackendBridge.__init__`.
  - [x] Connect `requestPullFile -> self._worker.pull_file` in `BackendBridge.__init__`.
  - Why: file transfer UI paths emit signals, but worker connections are missing, so push/pull cannot execute.

- [x] Fix cross-thread unsafe direct calls from UI thread to worker internals.
  - [x] Replace direct calls to `self._worker.adb_handler.pair_device(...)` and `disconnect_device(...)` with queued worker-slot requests + response signals.
  - [x] Keep all ADB operations in worker thread only.
  - Why: current pattern bypasses thread boundary guarantees and can cause race issues or UI stalls.

- [x] Correct rotation lock state semantics.
  - [x] Align `accelerometer_rotation` mapping with UI label (`Rotate Lock`) and ADB meaning.
  - [x] Ensure getter/setter names and values represent lock state consistently (`locked=True` should disable auto-rotate).
  - Why: current mapping likely inverts behavior and misleads users.

- [x] Fix broken/incorrect domain API in `backend/device.py` or remove file if unused.
  - [x] `Device.connect()` uses non-existent `ADBHandler.connect`.
  - [x] `Device.disconnect()` uses non-existent `ADBHandler.disconnect`.
  - [x] `Device.record()` calls non-existent `ScrcpyHandler.record`.
  - Why: dead/broken API is a future regression trap and confuses maintenance.

## P2 - Important (Stability and Reliability)

- [ ] Replace broad `except: pass` with targeted exceptions and user-facing/logged error context.
  - Scope: especially `backend/bridge.py`, `backend/adb_handler.py`, `backend/scrcpy_handler.py`, `backend/worker.py`.
  - Why: silent failures hide defects and make production debugging very hard.

- [ ] Standardize subprocess execution and failure handling.
  - [ ] Add a shared helper (timeout, return-code checks, stderr capture, optional retries).
  - [ ] Guard all methods against missing binaries (`adb`, `scrcpy`) with explicit status messages.
  - Why: current command handling is inconsistent and can fail silently.

- [ ] Improve device status update efficiency.
  - [ ] Avoid full `devicesChanged` emissions for every single device status tick.
  - [ ] Emit granular updates or batch status updates per poll cycle.
  - Why: frequent full list updates can cause unnecessary QML redraw/rebinding overhead.

- [ ] Make background polling configurable and adaptive.
  - [ ] Add polling interval setting in `QSettings` (default 3s).
  - [ ] Slow down when idle / no devices, speed up on active sessions.
  - Why: reduces unnecessary ADB load and improves responsiveness under different usage patterns.

- [ ] Harden cleanup/shutdown lifecycle.
  - [ ] Add `aboutToQuit` hook in `main.py` to ensure cleanup always runs.
  - [ ] Avoid `QThread.terminate()` fallback where possible; prefer cooperative shutdown with bounded wait + diagnostics.
  - Why: safer process/thread cleanup and fewer zombie operations.

- [ ] Improve app metadata quality.
  - [ ] Use `ADBHandler.get_app_label` fallback pipeline to avoid low-quality guessed labels.
  - [ ] Normalize icon extraction strategy (adaptive icon support where possible).
  - Why: improves UX and app discoverability.

## P3 - Nice-to-Have (Maintainability and Delivery Quality)

- [ ] Add automated tests for core parsing/logic.
  - [ ] Unit tests: device parsing, battery parsing, profile flag generation, display parameter selection.
  - [ ] Integration-smoke tests: bridge-worker signal flow with mocked subprocess.
  - Why: prevents regressions in critical command/parsing paths.

- [ ] Strengthen CI quality gates.
  - [ ] Add lint (`ruff`/`flake8`) and type checks (`mypy` or pyright baseline).
  - [ ] Add test job before packaging/release jobs.
  - Why: catch breakages before release artifact generation.

- [ ] Align docs with actual capabilities.
  - [ ] Update README claims (latency, telemetry completeness, architecture wording) to match implemented behavior.
  - [ ] Add troubleshooting section for missing `adb`/`scrcpy` binaries and permissions.
  - Why: reduces user confusion and support overhead.

- [ ] Introduce structured logging.
  - [ ] Replace `print()` with Python `logging` (levels + module logger names).
  - [ ] Optionally expose debug toggle in UI or env var.
  - Why: operational visibility during field debugging.

- [ ] Configuration and constants cleanup.
  - [ ] Centralize hardcoded values (timeouts, display defaults, history limits) into config constants.
  - [ ] Add per-profile/per-mode override support via settings.
  - Why: easier tuning and less duplication.

- [ ] Repository hygiene.
  - [ ] Ignore transient artifacts (`memory.db`, `__pycache__`, runtime caches) consistently.
  - [ ] Review generated Debian metadata files that should not be committed.
  - Why: cleaner diffs and fewer accidental commits.
