# STS2 Data Collector

Automatically upload your [Slay the Spire 2](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) run data to help build community analytics. The collector runs quietly in the background and uploads completed runs as you play.

![alt text](binary_image.png)

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

- Your Steam ID is hashed before storage, it is never stored in plain text
- Only `.run` file data is uploaded (game results, not personal information)
- Uploads are deduplicated so the same run is never sent twice

## Public API

All collected run data is available through a free, read-only API. No authentication required.

**Base URL:** `https://sts2-data-collector-production.up.railway.app`

### List all runs

```
GET /api/runs?limit=50&offset=0
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Results per page (1–200) |
| `offset` | int | 0 | Number of results to skip |

**Response:**

```json
{
  "runs": [
    {
      "run_id": "abc123:Profile1:run_001",
      "steam_id_hash": "abc123...",
      "profile": "Profile1",
      "file_name": "run_001",
      "file_size": 4096,
      "data": { "win": true, "ascension": 5, "acts": [...], ... },
      "uploaded_at": "2026-03-31T12:00:00Z"
    }
  ],
  "total": 1542,
  "limit": 50,
  "offset": 0
}
```

### Get a single run

```
GET /api/runs/{run_id}
```

Returns a single run object, or `404` if not found. The `run_id` format is `steam_id_hash:profile:file_name`.

### Example usage

```python
import requests

# Fetch the latest 100 runs
resp = requests.get("https://sts2-data-collector-production.up.railway.app/api/runs", params={"limit": 100})
runs = resp.json()["runs"]

# Filter for wins
wins = [r for r in runs if r["data"]["win"]]
print(f"{len(wins)} wins out of {len(runs)} runs")
```

### Rate limits

Public endpoints are limited to **30 requests per minute** per IP address.
