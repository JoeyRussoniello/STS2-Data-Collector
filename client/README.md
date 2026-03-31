# STS2 Data Collector

A tool for collecting [Slay the Spire 2](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) run data for analytics and machine learning. A Rust client watches for completed runs and uploads them to a FastAPI + PostgreSQL backend.

## Architecture

```
client/  (Rust)     — background service: discovers .run files, watches for new ones, uploads via HTTP
backend/ (Python)   — FastAPI server: receives uploads, hashes Steam IDs, stores runs as JSONB in PostgreSQL
```

---

## Quick Start

### Prerequisites

- [Rust](https://rustup.rs/) (edition 2024)
- [Python 3.13+](https://www.python.org/) with [uv](https://docs.astral.sh/uv/)
- PostgreSQL (local install or cloud — see Deployment below)

### 1. Set up the database

**Local PostgreSQL:**

Open pgAdmin or SQL Shell (psql) and run:

```sql
CREATE DATABASE sts2;
```

**Cloud (Neon free tier):**

Sign up at [neon.tech](https://neon.tech), create a project, and copy the connection string.

### 2. Configure the backend

```sh
cd backend
```

Create a `.env` file (this is gitignored):

```env
STS2_DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME?ssl=require
STS2_STEAM_ID_SALT=pick-a-random-secret-string
```

For local PostgreSQL without SSL:

```env
STS2_DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/sts2
STS2_STEAM_ID_SALT=change-me-in-production
```

### 3. Run the migration

```sh
cd backend
uv run alembic upgrade head
```

This creates the `runs` table. The migration file already exists at `alembic/versions/558d2f005730_initial.py` — you do **not** need to generate it.

### 4. Start the backend

```sh
cd backend
uv run python main.py
```

The API is now live at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 5. Start the client

In a separate terminal:

```sh
cd client
cargo run
```

The client will scan for existing `.run` files, upload any new ones, then watch for new runs in real time.

---

## Client

### What it does

1. **Startup scan** — walks `<STS2_DIR>/steam/<steam_id>/<profile>/saves/history/` and finds every `.run` file not yet uploaded.
2. **Live watching** — uses filesystem notifications (`notify` crate) to detect new `.run` files as they appear after each completed run.
3. **Deduplication** — tracks uploaded run IDs in a local `uploaded_runs.txt` file. Survives restarts.
4. **Upload** — reads `.run` files (which are JSON), parses them, and PUTs them to the backend API.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `STS2_BASE_DIR` | Auto-detected via `%APPDATA%` | Override the STS2 save directory |
| `STS2_SERVER_URL` | `http://localhost:8000` | Backend API URL |

### Building

```sh
cd client
cargo build --release
```

Binary: `target/release/client.exe` (Windows) or `target/release/client` (Linux/macOS).

### Testing

```sh
cargo test
```

Tests use temporary directories — no real save files are touched.

### Module layout

```
src/
  main.rs        — service orchestrator: startup scan → watcher event loop
  discovery.rs   — filesystem walking: Steam IDs, profiles, .run files, save dirs
  record.rs      — RunFileRecord, file_name_string, parse_run_path
  state.rs       — ClientState: local dedup via uploaded_runs.txt
  upload.rs      — Uploader: HTTP PUT to backend API
  watcher.rs     — notify-based filesystem watchers, RunEvent channel
  tests/
    mod.rs       — unit and integration tests
```

### Run ID format

```
<steam_id>:<profile>:<run_name>
```

Example: `76561198012345678:Profile1:1711871234` (`.run` extension is stripped).

---

## Backend

### API endpoints

| Method | Path | Description |
|---|---|---|
| `PUT` | `/runs/{run_id}` | Upload or update a run (idempotent) |
| `GET` | `/runs/{run_id}` | Fetch a single run |
| `GET` | `/runs/by-player/{steam_id}` | List runs for a player (`?limit=&offset=`) |
| `GET` | `/health` | Readiness check |

### Ports & adapters layout

```
app/
  config.py                  — pydantic-settings (reads .env)
  domain/
    models.py                — RunRecord dataclass, hash_steam_id (HMAC-SHA256)
    ports.py                 — RunRepository ABC
    services.py              — RunService (business logic, no framework deps)
  adapters/
    postgres/
      database.py            — async SQLAlchemy engine + session
      models.py              — RunRow ORM model (JSONB data column)
      repository.py          — PostgresRunRepository
  api/
    schemas.py               — Pydantic request/response DTOs
    dependencies.py          — DI wiring: session → repo → service
    routes/
      runs.py                — FastAPI route handlers
      health.py              — health check
```

### Testing the API manually

```sh
# Health check
curl http://localhost:8000/health

# Upload a run
curl -X PUT http://localhost:8000/runs/12345:profile1:run001 \
  -H "Content-Type: application/json" \
  -d '{"steam_id":"76561198012345678","profile":"profile1","file_name":"run001","file_size":2048,"data":{"character":"Ironclad","victory":true}}'

# Fetch it
curl http://localhost:8000/runs/12345:profile1:run001

# List runs by player
curl http://localhost:8000/runs/by-player/76561198012345678
```

---

## Deployment

### Cloud PostgreSQL (Neon)

1. Sign up at [neon.tech](https://neon.tech) (free tier: 0.5 GB)
2. Create a project, copy the connection string
3. Adjust the driver prefix: `postgresql+asyncpg://...` and use `?ssl=require` (drop `channel_binding=require` if present — asyncpg doesn't support it)
4. Put it in `backend/.env` as `STS2_DATABASE_URL`
5. Run `uv run alembic upgrade head` from the backend directory

### Backend hosting (Railway / Render / Fly.io)

A Dockerfile is included at `backend/Dockerfile`. To deploy on Railway:

1. Push the repo to GitHub
2. [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Set root directory to `backend`
4. Set environment variables: `STS2_DATABASE_URL`, `STS2_STEAM_ID_SALT`
5. Railway will build from the Dockerfile and give you a public URL

Then set `STS2_SERVER_URL` in the client to point at the production URL.

### Distributing the client

The Rust client compiles to a single `.exe` with no runtime dependencies. Distribute via GitHub Releases as a `.zip` containing the binary.

Users run it, it auto-detects the STS2 save directory, and uploads begin.

---

## Privacy

The client transmits the raw Steam ID alongside run data. **Steam ID hashing (HMAC-SHA256 with a secret salt) is performed server-side**, not in the client. The raw Steam ID is never stored in the database. The client does not collect or transmit any data beyond what is in the `.run` files and the directory structure STS2 already creates.
