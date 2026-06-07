import React, { useEffect, useState } from 'react';
import { PipelineRunState, WebhookEvent } from '../types';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

interface LogsViewProps {
  state: PipelineRunState;
  autoScroll: boolean;
  setAutoScroll: (autoScroll: boolean) => void;
  onClearLogs: () => void;
  timelineEndRef: React.RefObject<HTMLDivElement | null>;
}

function timeAgo(isoString: string): string {
  const diff = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function WebhookStatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    pipeline_triggered: 'bg-green-900/50 text-green-400 border-green-700',
    pong: 'bg-blue-900/50 text-blue-400 border-blue-700',
    ignored: 'bg-zinc-800/50 text-zinc-400 border-zinc-700',
    received: 'bg-yellow-900/50 text-yellow-400 border-yellow-700',
  };
  const cls = map[status] ?? 'bg-zinc-800/50 text-zinc-400 border-zinc-700';
  return (
    <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${cls}`}>
      {status.replace('_', ' ')}
    </span>
  );
}

function WebhookEventIcon({ event }: { event: string }) {
  const icons: Record<string, string> = {
    push: 'upload',
    pull_request: 'merge',
    ping: 'wifi_tethering',
  };
  return (
    <span className="material-symbols-outlined text-zinc-400 text-base">
      {icons[event] ?? 'webhook'}
    </span>
  );
}

export default function LogsView({
  state,
  autoScroll,
  setAutoScroll,
  onClearLogs,
  timelineEndRef,
}: LogsViewProps) {
  const [activePanel, setActivePanel] = useState<'sse' | 'webhooks'>('sse');
  const [webhookEvents, setWebhookEvents] = useState<WebhookEvent[]>([]);
  const [webhookError, setWebhookError] = useState<string | null>(null);

  // Poll webhook events every 5 seconds
  useEffect(() => {
    const fetchWebhooks = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/webhook/events?limit=30`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setWebhookEvents(data);
        setWebhookError(null);
      } catch (e) {
        setWebhookError('Could not reach backend webhook events endpoint.');
      }
    };

    fetchWebhooks();
    const interval = setInterval(fetchWebhooks, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full flex flex-col bg-surface-container-lowest overflow-hidden">
      {/* Header */}
      <div className="p-md border-b border-outline-variant flex justify-between items-center bg-white">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-secondary">terminal</span>
          <h2 className="font-headline-sm text-headline-sm font-bold text-primary">Audit Logs</h2>
        </div>
        <div className="flex items-center gap-2">
          {/* Panel tabs */}
          <div className="flex bg-surface-container-low rounded-lg p-0.5 gap-0.5">
            <button
              onClick={() => setActivePanel('sse')}
              className={`text-xs px-3 py-1 rounded font-semibold transition-all ${
                activePanel === 'sse'
                  ? 'bg-secondary text-white shadow'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Pipeline Events
            </button>
            <button
              onClick={() => setActivePanel('webhooks')}
              className={`text-xs px-3 py-1 rounded font-semibold transition-all flex items-center gap-1 ${
                activePanel === 'webhooks'
                  ? 'bg-secondary text-white shadow'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Webhook Activity
              {webhookEvents.length > 0 && (
                <span className="bg-green-500 text-white text-[9px] rounded-full w-4 h-4 flex items-center justify-center font-bold">
                  {webhookEvents.length > 9 ? '9+' : webhookEvents.length}
                </span>
              )}
            </button>
          </div>

          {activePanel === 'sse' && (
            <>
              <label className="text-xs flex items-center gap-1.5 text-on-surface-variant cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="rounded border-outline-variant focus:ring-secondary text-secondary"
                />
                Auto-scroll
              </label>
              <button
                onClick={onClearLogs}
                className="text-xs text-on-surface-variant hover:text-primary underline font-medium"
              >
                Clear
              </button>
            </>
          )}
        </div>
      </div>

      {/* SSE Events Panel */}
      {activePanel === 'sse' && (
        <div className="flex-1 p-md overflow-y-auto custom-scrollbar bg-zinc-950 text-zinc-100 font-mono text-xs space-y-3">
          {state.events.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-zinc-400">
              <span className="material-symbols-outlined text-3xl mb-2">code_off</span>
              <p>No events streamed yet. Run the pipeline to display live logging.</p>
            </div>
          ) : (
            state.events.map((event, idx) => (
              <div key={idx} className="p-3 bg-[#1e1e20] rounded border border-zinc-800/60 leading-normal">
                <div className="flex justify-between text-[10px] text-zinc-400 border-b border-zinc-800/60 pb-1.5 mb-2 font-sans">
                  <span className="font-semibold text-sky-450 uppercase tracking-wider">{event.event}</span>
                  <span>{event.timestamp}</span>
                </div>
                <pre className="overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-40 custom-scrollbar text-emerald-400">
                  {JSON.stringify(event.data, null, 2)}
                </pre>
              </div>
            ))
          )}
          <div ref={timelineEndRef as any} />
        </div>
      )}

      {/* Webhook Activity Panel */}
      {activePanel === 'webhooks' && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Info bar */}
          <div className="px-md py-2 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-zinc-400">
              <span className="material-symbols-outlined text-sm text-green-400">webhook</span>
              <span>Webhook URL: <code className="text-green-400 bg-[#1e1e20] px-1 rounded font-mono">POST /api/webhook/github</code></span>
            </div>
            <div className="flex items-center gap-1 text-zinc-550">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
              <span>Polling every 5s</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar bg-zinc-950 p-md space-y-2">
            {webhookError ? (
              <div className="flex flex-col items-center justify-center h-full text-zinc-400 gap-2">
                <span className="material-symbols-outlined text-3xl text-red-400">error</span>
                <p className="text-xs">{webhookError}</p>
              </div>
            ) : webhookEvents.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-400 gap-3">
                <span className="material-symbols-outlined text-4xl">webhook</span>
                <div className="text-center">
                  <p className="font-semibold text-zinc-300 mb-1">No webhook events yet</p>
                  <p className="text-xs text-zinc-500 max-w-xs">
                    Configure your GitHub repo to send events to this server. See the setup guide below.
                  </p>
                </div>
                <div className="bg-[#1e1e20] rounded-lg p-4 text-xs text-zinc-300 border border-zinc-800 max-w-md w-full space-y-2 font-mono">
                  <p className="text-zinc-400 font-sans font-semibold text-[10px] uppercase tracking-wider mb-2">GitHub Setup</p>
                  <p>1. Go to <span className="text-sky-400">GitHub Repo → Settings → Webhooks</span></p>
                  <p>2. Payload URL: <span className="text-green-400">https://your-ngrok-url/api/webhook/github</span></p>
                  <p>3. Content type: <span className="text-yellow-400">application/json</span></p>
                  <p>4. Events: <span className="text-purple-400">push</span>, <span className="text-purple-400">pull_request</span></p>
                  <p>5. Set secret → copy to <span className="text-orange-400">GITHUB_WEBHOOK_SECRET</span> in .env</p>
                </div>
              </div>
            ) : (
              webhookEvents.map((wh) => (
                <div
                  key={wh.delivery_id}
                  className="bg-[#1e1e20] rounded-lg border border-zinc-800/60 p-3 flex items-start gap-3 hover:border-zinc-700 transition-all"
                >
                  <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <WebhookEventIcon event={wh.event} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-zinc-200 font-sans">{wh.repo}</span>
                        <WebhookStatusBadge status={wh.status} />
                      </div>
                      <span className="text-[10px] text-zinc-500 flex-shrink-0">{timeAgo(wh.received_at)}</span>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-zinc-400 font-sans">
                      <span className="flex items-center gap-0.5">
                        <span className="material-symbols-outlined text-[12px]">code_blocks</span>
                        {wh.event}
                      </span>
                      {wh.branch && (
                        <span className="flex items-center gap-0.5">
                          <span className="material-symbols-outlined text-[12px]">fork_right</span>
                          {wh.branch}
                        </span>
                      )}
                      {wh.session_id && (
                        <span className="flex items-center gap-0.5">
                          <span className="material-symbols-outlined text-[12px]">link</span>
                          <code className="text-sky-400">{wh.session_id}</code>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
