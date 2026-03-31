# STS2 Data Collector

[![Release](https://img.shields.io/github/v/release/JoeyRussoniello/STS2-Data-Collector?style=flat-square)](https://github.com/JoeyRussoniello/STS2-Data-Collector/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/JoeyRussoniello/STS2-Data-Collector/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/JoeyRussoniello/STS2-Data-Collector/actions/workflows/ci.yml)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-blue?style=flat-square&logo=swagger)](https://sts2-data-collector-production.up.railway.app/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

I’m a Slay the Spire data nerd, and to my knowledge there isn’t a public STS2 dataset yet :(

A while back, I worked on a project using ~126k human STS1 runs (from a dev dump) and modeled win chance over time. It was super fun, and it made me realize how much interesting stuff depends on just having enough public run data in the first place.

So I made this for STS2!

**Contributing to the dataset is super easy:**

1. [Download the latest release](https://github.com/JoeyRussoniello/STS2-Data-Collector/releases)
2. Run the executable on your machine

The collector will:

- Find your STS2 save folder automatically
- Upload new completed `.run` files to the shared database
- Hash Steam IDs before storage for your privacy!

![Running Executable Image](./binary_image.png)

**Why?**

The big idea is to help make a public STS2 dataset so people can build stats pages, visualizations, dashboards, or modeling projects on top of it. Maybe we can quantitatively see how ass the Regent is lol.

---

## Public API

I’ve also built a minimal, completely free, read-only API for analysis, so anybody can access this run data and do their own analysis. [API Docs here](https://sts2-data-collector-production.up.railway.app/docs#/public)

**Base URL:** `https://sts2-data-collector-production.up.railway.app`

### List all runs

```bash
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

```bash
GET /api/runs/{run_id}
```

Returns a single run object, or `404` if not found. The `run_id` format is `steam_id_hash:profile:file_name`.

> Full Public API Documentation: [Swagger Docs](https://sts2-data-collector-production.up.railway.app/docs#/public)
>
> **NOTE**: Only the `/api/runs` endpoints are open to the public. Other endpoints require an API key.

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

---

## Privacy

- Your Steam ID is hashed before storage (never stored in plain text)
- Only `.run` file data is uploaded (game results, not personal info)
- Uploads are deduplicated so the same run is never sent twice

---

## Feedback & Contributing

Would love feedback on:

- What stats people would actually care about (I’m looking to build a public analytics frontend too, so this would be helpful!)
- Whether this is something you’d use or contribute to

Open an issue or PR, or just reach out!

---

*Not affiliated with Mega Crit at all, just trying to help make STS2 data projects easier/possible!*
