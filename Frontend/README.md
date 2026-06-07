# Frontend

This folder contains the frontend implementation for the Hindsight-powered DevOps pipeline.

## What it does

- Starts a backend analysis run through `POST /api/pipeline/start`
- Connects to the SSE stream returned by the backend
- Renders the live stage timeline
- Displays the strict JSON audit payload in a frontend-friendly layout

## Local development

1. Copy `.env.example` to `.env` and set `VITE_BACKEND_URL` if needed.
2. Install dependencies.
3. Start the dev server.

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Notes

- The UI expects the backend server from `Backend/server.py` to be running.
- The backend should be reachable at `http://localhost:8000` by default.
- The `final_payload` SSE event is the source of truth for the final rendered audit report.# Frontend

This directory contains a Vite + React frontend for the Hindsight DevOps pipeline.

## Run locally

```bash
cd Frontend
npm install
npm run dev
```

If your backend is running on a different host or port, set:

```bash
cp .env.example .env
```

Then edit `VITE_BACKEND_URL` as needed.

## What it does

- Starts a review run via `POST /api/pipeline/start`
- Listens to `/events` with `EventSource`
- Renders the final strict JSON payload into a dashboard
- Shows a live timeline of SSE events
