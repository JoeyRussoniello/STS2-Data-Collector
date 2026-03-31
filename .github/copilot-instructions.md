# STS2 Data Collector

A tool for collecting Slay the Spire 2 run data from players for analytics and machine learning. Players run a background Rust client that watches for completed `.run` files and uploads them to a FastAPI + PostgreSQL backend.

## Architecture

Monorepo with two independent components:

```
client/   Rust (edition 2024) — background service, filesystem watcher, HTTP uploader
backend/  Python 3.13 (FastAPI + SQLAlchemy + asyncpg) — REST API, hexagonal architecture
```

### Client (`client/`)

- **Entry:** `src/main.rs` — orchestrator: load state → startup scan → watcher event loop
- **Modules:**
  - `discovery.rs` — filesystem walking: `get_sts2_base_dir`, `list_child_dirs`, `is_profile_dir`, `get_profile_dirs`, `get_run_files_for_profile`, `discover_save_dirs`, `discover_existing_run_records`
  - `record.rs` — `RunFileRecord`, `file_name_string`, `parse_run_path`
  - `state.rs` — `ClientState`: local dedup via `uploaded_runs.txt` (HashSet<String> backed by flat file)
  - `upload.rs` — `Uploader`: HTTP POST to backend API (reads `STS2_SERVER_URL` env var, defaults to `http://localhost:8000`)
  - `watcher.rs` — `notify` crate integration, `RunEvent::NewRunFile(PathBuf)`, `start_watchers()`
  - `tests/mod.rs` — all tests, uses `tempfile` crate for temp directories
- **Key design:** The client's local dedup ID is `profile:file_name` (no steam_id). The server generates the global ID.
- **STS2 save tree:** `<base>/steam/<steam_id>/<profile>/saves/history/*.run`
- **`.run` files are JSON** — parsed directly by the uploader, sent as the `data` field.
- **Env vars:** `STS2_BASE_DIR` (override auto-detect), `STS2_SERVER_URL` (backend URL)

### Backend (`backend/`)

Hexagonal / ports-and-adapters architecture. Business logic in `domain/`, no framework imports there.

```
app/
  config.py                  — pydantic-settings, reads .env (STS2_DATABASE_URL, STS2_STEAM_ID_SALT)
  domain/
    models.py                — RunRecord dataclass, hash_steam_id (HMAC-SHA256)
    ports.py                 — RunRepository ABC
    services.py              — RunService (business logic only)
  adapters/
    postgres/
      database.py            — async SQLAlchemy engine + session factory
      models.py              — RunRow ORM model (JSONB data column)
      repository.py          — PostgresRunRepository (implements port)
  api/
    schemas.py               — Pydantic request/response DTOs
    dependencies.py          — DI wiring: session → repo → service
    routes/
      runs.py                — POST /runs, GET /runs/{run_id}, GET /runs/by-player/{steam_id}
      health.py              — GET /health
```

- **POST /runs** — server generates `run_id = f"{steam_id_hash}:{profile}:{file_name}"`. Client never sees or sends the global ID.
- **Steam ID privacy:** Raw steam_id arrives in POST body, is HMAC-SHA256 hashed with `STS2_STEAM_ID_SALT` before storage. Never stored raw.
- **Upsert:** Uses unique constraint on `(steam_id_hash, profile, file_name)` — re-uploading same run updates it.
- **Run data:** Stored as JSONB in `data` column, unprocessed for now.

## Build and Test

```sh
# Client
cd client
cargo build --release
cargo test

# Backend
cd backend
uv sync
uv run alembic upgrade head       # apply migrations
uv run python main.py             # start server on :8000
```

## Database

- PostgreSQL (cloud: Neon free tier, local: standard install)
- Async via `asyncpg` driver — connection string uses `postgresql+asyncpg://` prefix
- Migrations via Alembic (async env.py)
- Config in `backend/.env` (gitignored)

## Conventions

- **Client IDs are local-only:** `profile:file_name` for dedup in `uploaded_runs.txt`. No steam_id in local state.
- **Server owns global IDs:** `{steam_id_hash}:{profile}:{file_name}`
- **`.run` extension is stripped** from file names and IDs via `file_stem()`.
- **Backend layers never cross:** routes import from schemas/services, services import from ports/models, adapters implement ports. Never import FastAPI in domain.
- **Tests:** Client uses `tempfile::TempDir`, sets `STS2_BASE_DIR` env var to temp dirs. Uses `unsafe` blocks for `env::set_var`/`env::remove_var` (Rust 2024 edition requirement).
- **Error handling:** Client uses `io::Result<T>` throughout. Upload failures log and `continue`, never crash the watcher loop.
- **Dockerfile exists** at `backend/Dockerfile` using `uv` for dependency management.
