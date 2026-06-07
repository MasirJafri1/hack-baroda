# Frontend Integration Guide

This guide explains how to integrate the backend pipeline with a frontend application using Server-Sent Events (SSE).

The backend now exposes a streaming API that sends structured progress updates while the analysis runs, and then emits a final strict-JSON payload that the UI can render directly.

---

## 1. What the frontend receives

The backend produces two kinds of output:

1. **SSE events** during execution, such as stage start/completion, errors, and the final payload.
2. **A strict JSON result object** that contains everything the UI needs to render the timeline, badges, and audit panels.

The frontend should not parse raw terminal logs. It should only consume the SSE stream and the final JSON payload.

---

## 2. Backend endpoints

The backend server is exposed from `Backend/server.py`.

### Start a run

`POST /api/pipeline/start`

Request body:

```json
{
  "git_diff": "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-print('hello')\n+print('hello world')",
  "metadata": {
    "author": "demo_user",
    "timestamp": "2026-06-07T12:00:00Z"
  }
}
```

Response:

```json
{
  "session_id": "session_abc123",
  "events_url": "/api/pipeline/session_abc123/events",
  "result_url": "/api/pipeline/session_abc123/result"
}
```

### Stream events

`GET /api/pipeline/{session_id}/events`

This is an SSE endpoint. The frontend should open it with `EventSource` or an equivalent SSE client.

### Get final result

`GET /api/pipeline/{session_id}/result`

This returns the final JSON payload once the backend completes the run.

---

## 3. SSE event contract

The backend currently emits the following event types:

- `run_started`
- `stage_started`
- `stage_completed`
- `final_payload`
- `error`
- `done`

### Event payload shape

Each SSE message follows this shape:

```text
event: stage_started
data: {"stage":"reviewer_v1"}
```

or:

```text
event: final_payload
data: { ...strict JSON object... }
```

### Recommended UI behavior

- `run_started`: create a new timeline entry and initialize progress state.
- `stage_started`: mark the stage as in progress.
- `stage_completed`: mark the stage as complete and store any stage output.
- `final_payload`: render the final audit view from the JSON object.
- `error`: show a failure banner or retry affordance.
- `done`: close the SSE connection and mark the run as finished.

---

## 4. Final JSON schema

The frontend should render the payload returned in the `final_payload` event or from `GET /result`.

The object shape is:

```json
{
  "session_id": "string",
  "pipeline_metadata": {
    "author": "string",
    "changed_files": ["string"],
    "classification": {
      "cloud_infra": ["string"],
      "git_meta": ["string"],
      "app_code": ["string"]
    }
  },
  "triage_layer": {
    "risk_flagged": true,
    "matches_found": 2,
    "reasoning": "string"
  },
  "expert_analysis": {
    "cloud_expert_notes": "string",
    "code_expert_notes": "string",
    "git_expert_notes": "string"
  },
  "final_audit_report": {
    "verdict": "APPROVED | BLOCKED | REQUIRES_REVIEW",
    "risks": ["string"],
    "mitigation_patches": ["string"],
    "example_patch_code": "string",
    "conclusion": "string"
  }
}
```

### How to use this schema in the UI

- `pipeline_metadata` drives the top banner and file classification chips.
- `triage_layer` drives risk badges and the summary reason.
- `expert_analysis` populates expandable review cards or tabbed panels.
- `final_audit_report` drives the final verdict, risk list, patch suggestions, and markdown-rendered conclusion.

---

## 5. Recommended frontend state model

Use one top-level state object with these fields:

```ts
type PipelineRunState = {
  sessionId: string;
  isRunning: boolean;
  currentStage: string | null;
  completedStages: string[];
  events: Array<{ event: string; data: any; timestamp: string }>;
  finalPayload: any | null;
  error: string | null;
};
```

Suggested behavior:

- `sessionId`: set when the start request returns.
- `isRunning`: true when SSE opens, false when `done` or `error` is received.
- `currentStage`: update on `stage_started`.
- `completedStages`: append on `stage_completed`.
- `events`: keep the raw timeline for debugging and replay.
- `finalPayload`: assign when `final_payload` arrives.
- `error`: populate on any `error` event or failed HTTP request.

---

## 6. React integration example

Below is a practical client-side implementation using `fetch` to start the run and `EventSource` to receive SSE updates.

```tsx
import { useEffect, useRef, useState } from 'react';

type PipelineRunState = {
  sessionId: string;
  isRunning: boolean;
  currentStage: string | null;
  completedStages: string[];
  events: Array<{ event: string; data: any; timestamp: string }>;
  finalPayload: any | null;
  error: string | null;
};

const initialState: PipelineRunState = {
  sessionId: '',
  isRunning: false,
  currentStage: null,
  completedStages: [],
  events: [],
  finalPayload: null,
  error: null,
};

export function usePipelineRun() {
  const [state, setState] = useState<PipelineRunState>(initialState);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startRun = async (gitDiff: string, metadata: Record<string, any> = {}) => {
    setState((prev) => ({ ...prev, isRunning: true, error: null }));

    const response = await fetch('http://localhost:8000/api/pipeline/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ git_diff: gitDiff, metadata }),
    });

    if (!response.ok) {
      throw new Error(`Failed to start pipeline: ${response.status}`);
    }

    const data = await response.json();
    const sessionId = data.session_id as string;

    setState((prev) => ({ ...prev, sessionId }));

    const eventsUrl = `http://localhost:8000${data.events_url}`;
    const es = new EventSource(eventsUrl);
    eventSourceRef.current = es;

    es.addEventListener('run_started', (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      setState((prev) => ({
        ...prev,
        events: [...prev.events, { event: 'run_started', data: payload, timestamp: new Date().toISOString() }],
      }));
    });

    es.addEventListener('stage_started', (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      setState((prev) => ({
        ...prev,
        currentStage: payload.stage,
        events: [...prev.events, { event: 'stage_started', data: payload, timestamp: new Date().toISOString() }],
      }));
    });

    es.addEventListener('stage_completed', (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      setState((prev) => ({
        ...prev,
        completedStages: [...prev.completedStages, payload.stage],
        events: [...prev.events, { event: 'stage_completed', data: payload, timestamp: new Date().toISOString() }],
      }));
    });

    es.addEventListener('final_payload', (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      setState((prev) => ({
        ...prev,
        finalPayload: payload,
        events: [...prev.events, { event: 'final_payload', data: payload, timestamp: new Date().toISOString() }],
      }));
    });

    es.addEventListener('error', (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      setState((prev) => ({
        ...prev,
        error: payload.message || 'Pipeline failed',
        isRunning: false,
        events: [...prev.events, { event: 'error', data: payload, timestamp: new Date().toISOString() }],
      }));
      es.close();
    });

    es.addEventListener('done', (event) => {
      const payload = JSON.parse((event as MessageEvent).data);
      setState((prev) => ({
        ...prev,
        isRunning: false,
        events: [...prev.events, { event: 'done', data: payload, timestamp: new Date().toISOString() }],
      }));
      es.close();
    });
  };

  const stopRun = () => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setState((prev) => ({ ...prev, isRunning: false }));
  };

  useEffect(() => {
    return () => eventSourceRef.current?.close();
  }, []);

  return { state, startRun, stopRun };
}
```

---

## 7. Rendering the final payload

The final payload is designed so the UI can be declarative.

### Example rendering strategy

```tsx
function VerdictBadge({ verdict }: { verdict: string }) {
  const color = verdict === 'APPROVED'
    ? 'bg-green-600'
    : verdict === 'BLOCKED'
      ? 'bg-red-600'
      : 'bg-amber-500';

  return <span className={`rounded-full px-3 py-1 text-white ${color}`}>{verdict}</span>;
}
```

### Suggested UI sections

- **Header**: session ID, author, verdict badge.
- **Timeline**: one card per SSE event.
- **Risk summary**: `triage_layer.reasoning` and `matches_found`.
- **Expert tabs**: Git, Cloud, and Code analysis.
- **Patch panel**: render `mitigation_patches` in collapsible cards.
- **Markdown conclusion**: render `final_audit_report.conclusion` with a Markdown renderer.

---

## 8. Error handling

The frontend should handle these cases:

### Start request failure

- Show a toast or banner.
- Keep the page interactive.
- Allow retrying the same diff.

### SSE connection failure

- Set `isRunning = false`.
- Display a reconnect button.
- Optionally call `GET /result` if the session may have completed server-side.

### Backend returns `error`

- Display the server error message.
- Preserve the partial event timeline for debugging.

---

## 9. Reconnection strategy

If the SSE connection drops, use the `session_id` to query the backend result endpoint.

Recommended approach:

1. Keep `session_id` in local state or URL params.
2. On reconnect, open a fresh SSE connection if the backend still streams.
3. If the stream is done, call `GET /api/pipeline/{session_id}/result` and render the payload.

---

## 10. CORS and deployment notes

If the frontend runs on a different origin, the backend should allow CORS for the frontend domain.

For local development, the frontend usually runs on `http://localhost:3000` and the backend on `http://localhost:8000`.

If you add CORS middleware, allow at least:

- `http://localhost:3000`
- your staging frontend domain
- your production frontend domain

---

## 11. Integration checklist

- Start the backend server with `uvicorn server:app --reload --host 0.0.0.0 --port 8000`.
- Ensure `Backend/.env` includes `GROQ_API_KEY` and `GROQ_MODEL`.
- Call `POST /api/pipeline/start` with the git diff and metadata.
- Open the returned `events_url` as an SSE connection.
- Update the UI on `stage_started`, `stage_completed`, and `final_payload` events.
- Render the final payload instead of parsing free-form logs.
- Use `GET /result` as a fallback or replay endpoint.

---

## 12. Recommended next step

If you want the frontend to be fully wired, the next practical step is to create a small React hook and a page component that:

1. accepts a pasted git diff,
2. starts the pipeline,
3. displays the event timeline live,
4. renders the final JSON payload.

I can generate that frontend component next.
