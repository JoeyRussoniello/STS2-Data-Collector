# STS2 Data Collector

Automatically upload your [Slay the Spire 2](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) run data to help build community analytics. The collector runs quietly in the background and uploads completed runs as you play.

## Installation

1. Go to the [Releases](../../releases/latest) page
2. Download the file for your platform:
   - **Windows:** `sts2-collector-windows-x64.exe`
   - **macOS (Apple Silicon):** `sts2-collector-macos-arm64`
   - **Linux:** `sts2-collector-linux-x64`
3. Place it anywhere convenient (e.g. your Desktop or a `tools/` folder)

**macOS / Linux only:** make the file executable first:

```sh
chmod +x sts2-collector-*
```

## Usage

Double-click the executable (or run it from a terminal). That's it.

The collector will:

- Automatically find your STS2 save directory
- Upload any completed runs it hasn't seen before
- Watch for new runs and upload them as you play
- Retry failed uploads automatically

To stop, press `q` + Enter in the terminal window.

### Troubleshooting

If the collector can't find your save directory, you can point it manually:

```sh
# Windows (PowerShell)
$env:STS2_BASE_DIR = "C:\path\to\SteamLibrary\steamapps\common\Slay the Spire 2"
.\sts2-collector-windows-x64.exe

# macOS / Linux
STS2_BASE_DIR="/path/to/Slay the Spire 2" ./sts2-collector-linux-x64
```

## Privacy

- Your Steam ID is hashed before storage — it is never stored in plain text
- Only `.run` file data is uploaded (game results, not personal information)
- Uploads are deduplicated so the same run is never sent twice
