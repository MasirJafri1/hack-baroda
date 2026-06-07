import { useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

type PipelineEvent = {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
};

type PipelineRunState = {
  sessionId: string;
  isRunning: boolean;
  currentStage: string | null;
  completedStages: string[];
  events: PipelineEvent[];
  finalPayload: any | null;
  error: string | null;
};

type FinalPayload = {
  session_id: string;
  pipeline_metadata: {
    author: string;
    changed_files: string[];
    classification: {
      cloud_infra: string[];
      git_meta: string[];
      app_code: string[];
    };
  };
  triage_layer: {
    risk_flagged: boolean;
    matches_found: number;
    reasoning: string;
  };
  expert_analysis: {
    cloud_expert_notes: string;
    code_expert_notes: string;
    git_expert_notes: string;
  };
  final_audit_report: {
    verdict: 'APPROVED' | 'BLOCKED' | 'REQUIRES_REVIEW';
    risks: string[];
    mitigation_patches: string[];
    example_patch_code: string;
    conclusion: string;
  };
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

const sampleDiff = `diff --git a/app/websocket_handler.py b/app/websocket_handler.py
index 92c81da..a83b2ef 100644
--- a/app/websocket_handler.py
+++ b/app/websocket_handler.py
@@ -12,11 +12,12 @@ class ConnectionManager:
 
-    async def connect(self, websocket: WebSocket):
-        await websocket.accept()
-        self.active_connections.append(websocket)
-
-    async def disconnect(self, websocket: WebSocket):
-        self.active_connections.remove(websocket)
+    async def handle_connection(self, websocket: WebSocket):
+        await websocket.accept()
+        self.active_connections.append(websocket)
+        while True:
+            data = await websocket.receive_text()
+            await self.send_personal_message(f"Message received: {data}", websocket)
`;

const backendUrl = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

const stageLabels: Record<string, string> = {
  context_agent: 'Context Agent',
  reviewer_v1: 'Reviewer V1',
  reviewer_v2: 'Reviewer V2',
  retrieval_agent: 'Retrieval Agent',
  git_expert: 'Git Expert',
  cloud_expert: 'Cloud Expert',
  code_expert: 'Code Expert',
  big_boss: 'Big Boss',
};

function verdictTone(verdict?: string) {
  if (verdict === 'APPROVED') return 'approved';
  if (verdict === 'BLOCKED') return 'blocked';
  if (verdict === 'REQUIRES_REVIEW') return 'review';
  return 'idle';
}

function prettyJson(value: any) {
  return JSON.stringify(value, null, 2);
}

function VerdictPill({ verdict }: { verdict?: string }) {
  const safeVerdict = verdict ?? 'UNKNOWN';
  const tone =
    safeVerdict === 'APPROVED'
      ? 'pill pill-good'
      : safeVerdict === 'BLOCKED'
        ? 'pill pill-bad'
        : 'pill pill-warn';

  return <span className={tone}>{safeVerdict}</span>;
}

function StageChip({ label, active, done }: { label: string; active?: boolean; done?: boolean }) {
  return <span className={`stage-chip ${active ? 'active' : ''} ${done ? 'done' : ''}`}>{label}</span>;
}

export default function App() {
  const [gitDiff, setGitDiff] = useState(sampleDiff);
  const [author, setAuthor] = useState('demo_user');
  const [state, setState] = useState<PipelineRunState>(initialState);
  const [serverUrl, setServerUrl] = useState(backendUrl);
  const [autoScroll, setAutoScroll] = useState(true);
  const eventSourceRef = useRef<EventSource | null>(null);

  const verdict = state.finalPayload?.final_audit_report?.verdict as string | undefined;
  const sessionId = state.sessionId || state.finalPayload?.session_id || 'waiting';
  const stages = useMemo(
    () => ['context_agent', 'reviewer_v1', 'reviewer_v2', 'retrieval_agent', 'git_expert', 'cloud_expert', 'code_expert', 'big_boss'],
    [],
  );

  const appendEvent = (event: string, data: Record<string, unknown>) => {
    setState((prev) => ({
      ...prev,
      events: [...prev.events, { event, data, timestamp: new Date().toISOString() }],
    }));
  };

  const closeStream = () => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
  };

  useEffect(() => {
    return () => closeStream();
  }, []);

  const handleStart = async () => {
    closeStream();
    setState({ ...initialState, isRunning: true });

    try {
      const response = await fetch(`${serverUrl.replace(/\/$/, '')}/api/pipeline/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          git_diff: gitDiff,
          metadata: {
            author,
            timestamp: new Date().toISOString(),
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`Start request failed with status ${response.status}`);
      }

      const payload = await response.json();
      const newSessionId = payload.session_id as string;

      setState((prev) => ({ ...prev, sessionId: newSessionId }));

      const eventsUrl = `${serverUrl.replace(/\/$/, '')}${payload.events_url}`;
      const es = new EventSource(eventsUrl);
      eventSourceRef.current = es;

      es.addEventListener('run_started', (event) => {
        const data = JSON.parse((event as MessageEvent).data);
        appendEvent('run_started', data);
      });

      es.addEventListener('stage_started', (event) => {
        const data = JSON.parse((event as MessageEvent).data);
        setState((prev) => ({
          ...prev,
          currentStage: data.stage as string,
        }));
        appendEvent('stage_started', data);
      });

      es.addEventListener('stage_completed', (event) => {
        const data = JSON.parse((event as MessageEvent).data);
        setState((prev) => ({
          ...prev,
          completedStages: [...prev.completedStages, String(data.stage)],
        }));
        appendEvent('stage_completed', data);
      });

      es.addEventListener('final_payload', (event) => {
        const data = JSON.parse((event as MessageEvent).data) as FinalPayload;
        setState((prev) => ({
          ...prev,
          finalPayload: data,
          isRunning: false,
        }));
        appendEvent('final_payload', data);
      });

      es.addEventListener('error', (event) => {
        let message = 'Pipeline failed';
        try {
          message = JSON.parse((event as MessageEvent).data)?.message ?? message;
        } catch {
          message = (event as MessageEvent).data || message;
        }
        setState((prev) => ({ ...prev, error: message, isRunning: false }));
        appendEvent('error', { message });
        closeStream();
      });

      es.addEventListener('done', (event) => {
        const data = JSON.parse((event as MessageEvent).data);
        appendEvent('done', data);
        setState((prev) => ({ ...prev, isRunning: false }));
        closeStream();
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start pipeline';
      setState((prev) => ({ ...prev, error: message, isRunning: false }));
    }
  };

  const triage = state.finalPayload?.triage_layer;
  const pipelineMetadata = state.finalPayload?.pipeline_metadata;
  const expertAnalysis = state.finalPayload?.expert_analysis;
  const finalAudit = state.finalPayload?.final_audit_report;

  return (
    <div className="app-shell">
      <div className="grain" />
      <header className="hero">
        <div>
          <p className="eyebrow">Hindsight-powered DevOps Pipeline</p>
          <h1>Watch the audit run in real time.</h1>
          <p className="lede">
            Paste a git diff, stream the agent stages over SSE, and render the final strict-JSON audit directly in the UI.
          </p>
        </div>
        <div className="hero-card">
          <div className="hero-card-row">
            <span className="hero-label">Session</span>
            <span className="mono">{sessionId}</span>
          </div>
          <div className="hero-card-row">
            <span className="hero-label">Backend</span>
            <span className="mono">{serverUrl}</span>
          </div>
          <div className="hero-card-row">
            <span className="hero-label">Verdict</span>
            <VerdictPill verdict={verdict} />
          </div>
        </div>
      </header>

      <main className="layout">
        <section className="panel editor-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Input</p>
              <h2>Git diff and metadata</h2>
            </div>
            <div className="inline-actions">
              <label className="toggle">
                <input type="checkbox" checked={autoScroll} onChange={(e) => setAutoScroll(e.target.checked)} />
                Auto-scroll timeline
              </label>
            </div>
          </div>

          <label className="field">
            <span>Backend URL</span>
            <input value={serverUrl} onChange={(e) => setServerUrl(e.target.value)} placeholder="http://localhost:8000" />
          </label>

          <label className="field">
            <span>Author</span>
            <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="demo_user" />
          </label>

          <label className="field grow">
            <span>Git diff</span>
            <textarea value={gitDiff} onChange={(e) => setGitDiff(e.target.value)} spellCheck={false} />
          </label>

          <div className="actions">
            <button className="primary" onClick={handleStart} disabled={state.isRunning}>
              {state.isRunning ? 'Running...' : 'Start pipeline'}
            </button>
            <button className="secondary" onClick={() => setState(initialState)} disabled={state.isRunning}>
              Reset UI
            </button>
          </div>

          {state.error ? <div className="banner error">{state.error}</div> : null}
        </section>

        <section className="panel timeline-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Live stream</p>
              <h2>Agent timeline</h2>
            </div>
            <div className="stage-list">
              {stages.map((stage) => (
                <StageChip key={stage} label={stage} active={state.currentStage === stage} done={state.completedStages.includes(stage)} />
              ))}
            </div>
          </div>

          <div className="timeline" aria-live="polite">
            {state.events.length === 0 ? (
              <div className="empty-state">
                <h3>Waiting for a run</h3>
                <p>The SSE timeline will appear here once you start the pipeline.</p>
              </div>
            ) : (
              state.events.map((item, index) => (
                <article key={`${item.event}-${index}`} className="timeline-item">
                  <div className="timeline-dot" />
                  <div className="timeline-card">
                    <div className="timeline-head">
                      <strong>{item.event}</strong>
                      <span>{item.timestamp}</span>
                    </div>
                    <pre>{prettyJson(item.data)}</pre>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="panel results-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Output</p>
              <h2>Final audit payload</h2>
            </div>
            <VerdictPill verdict={verdict} />
          </div>

          {finalAudit ? (
            <div className="result-grid">
              <div className="result-card">
                <h3>Pipeline metadata</h3>
                <p><span>Author</span> {pipelineMetadata?.author ?? '—'}</p>
                <p><span>Session</span> {state.finalPayload?.session_id ?? '—'}</p>
                <p><span>Changed files</span> {(pipelineMetadata?.changed_files ?? []).join(', ') || 'None'}</p>
              </div>

              <div className="result-card">
                <h3>Triage layer</h3>
                <p><span>Risk</span> {String(triage?.risk_flagged ?? false)}</p>
                <p><span>Matches</span> {String(triage?.matches_found ?? 0)}</p>
                <p><span>Reasoning</span> {triage?.reasoning ?? '—'}</p>
              </div>

              <div className="result-card wide">
                <h3>Expert analysis</h3>
                <div className="expert-columns">
                  <article>
                    <h4>Cloud</h4>
                    <pre>{expertAnalysis?.cloud_expert_notes ?? '—'}</pre>
                  </article>
                  <article>
                    <h4>Code</h4>
                    <pre>{expertAnalysis?.code_expert_notes ?? '—'}</pre>
                  </article>
                  <article>
                    <h4>Git</h4>
                    <pre>{expertAnalysis?.git_expert_notes ?? '—'}</pre>
                  </article>
                </div>
              </div>

              <div className="result-card wide">
                <h3>Final audit report</h3>
                <div className="audit-summary">
                  <div>
                    <span>Verdict</span>
                    <VerdictPill verdict={finalAudit?.verdict as string | undefined} />
                  </div>
                  <div>
                    <span>Risks</span>
                    <ul>
                      {(finalAudit?.risks ?? []).map((risk: string, index: number) => (
                        <li key={index}>{risk}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <span>Mitigation patches</span>
                    <ul>
                      {(finalAudit?.mitigation_patches ?? []).map((patch: string, index: number) => (
                        <li key={index}>{patch}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="markdown-card">
                  <ReactMarkdown>{finalAudit?.conclusion ?? ''}</ReactMarkdown>
                </div>

                {finalAudit?.example_patch_code ? <pre className="code-block">{finalAudit.example_patch_code}</pre> : null}
              </div>
            </div>
          ) : (
            <div className="empty-state compact">
              <h3>Final payload will appear here</h3>
              <p>The frontend renders the strict JSON audit once the SSE stream emits <code>final_payload</code>.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}