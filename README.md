# Protein Purification Web

A modern web-based educational simulation of protein separation techniques, [originally created by Prof. Andrew Booth in 1983](https://github.com/agbooth/protein_purification). This webapp replaces the legacy Windows (C++), macOS (Obj-C), and iOS (Obj-C) versions with a single cross-platform solution.

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / Pydantic
- **Frontend**: TypeScript / Vite / Plotly.js / HTML5 Canvas
- **Testing**: pytest / pytest-asyncio

## Quick Start

### Backend

```bash
cd protein_purification_web
pip install -e ".[dev]"
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd protein_purification_web/frontend
npm install
npm run dev
```

### Tests

```bash
cd protein_purification_web
pytest
```

## Project Structure

```
protein_purification_web/
├── pyproject.toml          # Python project config and dependencies
├── backend/
│   ├── main.py             # FastAPI app entry point
│   ├── config.py           # App configuration
│   ├── session_store.py    # In-memory session management
│   ├── dependencies.py     # FastAPI dependency injection
│   ├── engine/             # Pure simulation engine (no web deps)
│   │   ├── protein.py      # Protein dataclass
│   │   ├── protein_data.py # Charge calculations, isoelectric point
│   │   ├── separation.py   # All 7 separation techniques
│   │   ├── account.py      # Cost tracking, step records
│   │   ├── gel.py          # PAGE electrophoresis calculations
│   │   ├── session.py      # PurificationSession state machine
│   │   ├── mixture_io.py   # Mixture file parser/writer
│   │   ├── constants.py    # Named constants
│   │   └── enums.py        # Enumeration types
│   └── api/                # FastAPI route handlers
│       ├── sessions.py     # Session lifecycle
│       ├── mixtures.py     # Mixture listing
│       ├── separation.py   # Run technique
│       ├── fractions.py    # Assay, dilute, pool
│       ├── electrophoresis.py # PAGE endpoints
│       └── files.py        # Save/load .ppmixture
├── frontend/
│   ├── package.json        # Frontend dependencies
│   ├── vite.config.ts      # Vite build configuration
│   └── src/
│       ├── main.ts         # Entry point
│       ├── api.ts          # Backend API client
│       ├── state.ts        # Client-side state mirror
│       ├── views/          # Main display views
│       ├── dialogs/        # Parameter input modals
│       ├── components/     # Reusable UI components
│       ├── i18n/           # Localization resources
│       └── styles/         # CSS
├── data/
│   └── mixtures/           # Bundled mixture files
└── tests/
    ├── engine/             # Unit tests for simulation engine
    └── api/                # Integration tests for REST API
```

## Architecture

The codebase follows a clean separation of concerns:

1. **Engine** (`backend/engine/`): Pure Python simulation with zero web dependencies. Testable independently, usable from notebooks or CLI.
2. **API** (`backend/api/`): Thin FastAPI adapter layer translating HTTP requests to engine calls.
3. **Frontend** (`frontend/`): Vanilla TypeScript SPA communicating via REST API.

The server is authoritative---all simulation runs server-side. The frontend mirrors state returned from each API response.

## See Also

- [FEATURES.md](FEATURES.md) --- Detailed feature design and implementation milestones
- [spec.md](../spec.md) --- Full application specification
