# STS2 Data Collector — Client

A lightweight background service that detects [Slay the Spire 2](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) completed runs and uploads them to a collection server for analytics.

## What it does

1. **Startup scan** — walks the STS2 save tree (`%APPDATA%/SlayTheSpire2/steam/<steam_id>/<profile>/saves/history/`) and finds every `.run` file that hasn't been uploaded yet.
2. **Live watching** — uses filesystem notifications to detect new `.run` files as they appear after each completed run.
3. **Deduplication** — tracks which runs have already been uploaded in a local `uploaded_runs.txt` file so nothing is sent twice, even across restarts.
4. **Upload** — *(not yet implemented)* sends each new run record to the collection server.

The client is intentionally simple: it discovers files, reads metadata, and ships records. All analytics and storage happen server-side.

## Building

Requires [Rust](https://rustup.rs/) (edition 2024).

```sh
cd client
cargo build --release
```

The compiled binary will be at `target/release/client.exe` (Windows) or `target/release/client` (Linux/macOS).

## Running

```sh
./client
```

On first launch the client will:

- Locate the STS2 save directory (auto-detected on Windows via `%APPDATA%`)
- Scan for any existing `.run` files and report how many are new
- Begin watching for new runs in the background

The process runs until killed (Ctrl+C).

### Environment variables

| Variable | Description |
|---|---|
| `STS2_BASE_DIR` | Override the auto-detected STS2 save directory. Useful for testing or non-standard installs. |

## Testing

```sh
cargo test
```

Tests use temporary directories and don't touch your real save files.

## Project structure

```
src/
  main.rs        — service entrypoint: startup scan → watcher loop
  discovery.rs   — filesystem walking: find Steam IDs, profiles, and .run files
  record.rs      — RunFileRecord type, path parsing
  state.rs       — local dedup state (uploaded_runs.txt)
  watcher.rs     — notify-based filesystem watchers
  upload.rs      — HTTP upload (TODO)
  tests/
    mod.rs       — unit and integration tests
```

## How run files are identified

Each run is assigned a composite ID:

```
<steam_id>:<profile>:<filename>
```

For example: `76561198012345678:Profile1:run_2026-03-31.run`

This ID is used for deduplication both locally and server-side.

## Privacy

The client transmits the raw Steam ID alongside run data. **Steam ID hashing is performed server-side**, not in the client. The client does not collect or transmit any data beyond what is contained in the `.run` files and the directory structure STS2 already creates.
