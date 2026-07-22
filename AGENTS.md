# AGENTS.md

## Cursor Cloud specific instructions

### Overview
The only runnable code in this repo is the Flutter app in `dating_app/` (currently the default Flutter counter scaffold). All other top-level files are planning/design docs (`.docx`/`.txt`/`.md`). The Node backend, database, Firebase, etc. described in the docs are NOT implemented and do not exist in the repo, so there is no backend/DB to run.

### Toolchain
- Flutter SDK is pre-installed at `/opt/flutter` (Flutter 3.44.x / Dart 3.12.x), which satisfies `pubspec.yaml` (`sdk: ^3.10.4`, Flutter `>=3.35.0`).
- `/opt/flutter/bin` is added to `PATH` via `~/.bashrc`. In non-login shells, run `export PATH="/opt/flutter/bin:$PATH"` first.
- Web is enabled and `CHROME_EXECUTABLE=/usr/local/bin/google-chrome` is used for the Chrome device.

### Common commands (run from `dating_app/`)
- Install deps: `flutter pub get`
- Lint: `flutter analyze`
- Test: `flutter test`
- Run (dev, headless-friendly): `flutter run -d web-server --web-port 8080 --web-hostname 0.0.0.0`, then open `http://localhost:8080` in Chrome.
- Run directly in Chrome: `flutter run -d chrome`.

### Notes
- `flutter run -d web-server` prints a note that debugging needs the Dart Debug Chrome extension; this is harmless for serving/manual testing.
- First `flutter` invocation after a fresh SDK download builds the flutter tool and can take longer; subsequent runs are fast.
