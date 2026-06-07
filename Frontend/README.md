# Frontend

This folder contains the frontend implementation for the Hindsight-powered DevOps pipeline.

## What it does

- Starts a backend analysis run through `POST /api/pipeline/start`
- Connects to the SSE stream returned by the backend
- Renders the live stage timeline
- Displays the strict JSON audit payload in a frontend-friendly layout

## Local development & Run locally

```bash
cd Frontend
npm install
npm run dev
```

If your backend is running on a different host or port, copy `.env.example` to `.env` and configure `VITE_BACKEND_URL`:

```bash
cp .env.example .env
```

## Build

```bash
npm run build
```

## Notes

- The UI expects the backend server from `Backend/server.py` to be running.
- The backend should be reachable at `http://localhost:8000` by default.
- The `final_payload` SSE event is the source of truth for the final rendered audit report.
