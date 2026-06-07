import { useEffect, useRef, useState } from 'react';
import { PipelineRunState, FinalPayload } from './types';
import {
  RISKY_POOL_DIFF,
  SAFE_POOL_DIFF,
  RISKY_WEBSOCKET_DIFF,
  SAFE_WEBSOCKET_DIFF,
} from './constants';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import DashboardView from './components/DashboardView';
import SecurityView from './components/SecurityView';
import LogsView from './components/LogsView';

const backendUrl = import.meta.env.VITE_BACKEND_URL ?? 
  (window.location.port === '5173' ? 'http://localhost:8000' : window.location.origin);

const initialState: PipelineRunState = {
  sessionId: '',
  isRunning: false,
  currentStage: null,
  completedStages: [],
  events: [],
  finalPayload: null,
  error: null,
};

export default function App() {
  const [gitDiff, setGitDiff] = useState(RISKY_POOL_DIFF);
  const [githubRepo, setGithubRepo] = useState('11-anos/demo-vulnerable-microservice');
  const [inputType, setInputType] = useState<'diff' | 'github'>('github');
  const [author, setAuthor] = useState('demo_user');
  const [activeTab, setActiveTab] = useState<'dashboard' | 'security' | 'logs'>('dashboard');
  const [state, setState] = useState<PipelineRunState>(initialState);
  const [autoScroll, setAutoScroll] = useState(true);
  const eventSourceRef = useRef<EventSource | null>(null);
  const timelineEndRef = useRef<HTMLDivElement | null>(null);

  const sessionId = state.sessionId || state.finalPayload?.session_id || 'waiting';

  const appendEvent = (event: string, data: Record<string, unknown>) => {
    setState((prev) => ({
      ...prev,
      events: [...prev.events, { event, data, timestamp: new Date().toLocaleTimeString() }],
    }));
  };

  const closeStream = () => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
  };

  useEffect(() => {
    return () => closeStream();
  }, []);

  const handleStart = async (overrideDiff?: string, overrideType?: 'diff' | 'github') => {
    closeStream();
    setState({ ...initialState, isRunning: true });

    const finalType = overrideType ?? inputType;
    const finalDiff = overrideDiff ?? gitDiff;

    try {
      const response = await fetch(`${backendUrl.replace(/\/$/, '')}/api/pipeline/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          git_diff: finalType === 'diff' ? finalDiff : '',
          github_repo: finalType === 'github' ? githubRepo : undefined,
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
      const newSessionId = payload.session_id;

      setState((prev) => ({ ...prev, sessionId: newSessionId }));

      const eventsUrl = `${backendUrl.replace(/\/$/, '')}${payload.events_url}`;
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
          currentStage: data.stage,
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

  const handleApplyFix = () => {
    let fixDiff = SAFE_POOL_DIFF;
    if (gitDiff.includes('websocket_handler')) {
      fixDiff = SAFE_WEBSOCKET_DIFF;
    }
    setGitDiff(fixDiff);
    setInputType('diff');
    handleStart(fixDiff, 'diff');
  };

  const handleSimulatePush = (riskyType: 'pool' | 'websocket') => {
    const targetDiff = riskyType === 'pool' ? RISKY_POOL_DIFF : RISKY_WEBSOCKET_DIFF;
    setGitDiff(targetDiff);
    setInputType('diff');
    handleStart(targetDiff, 'diff');
  };

  const handleIgnoreForce = () => {
    if (state.finalPayload) {
      setState((prev) => ({
        ...prev,
        finalPayload: {
          ...prev.finalPayload!,
          final_audit_report: {
            ...prev.finalPayload!.final_audit_report,
            verdict: 'APPROVED',
            conclusion: '⚠️ VERDICT BYPASS: Developer forced approval of this run.',
          },
        },
      }));
    }
  };

  const handleClearSession = () => {
    closeStream();
    setState(initialState);
  };


  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-on-background">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        <main className="flex-1 overflow-hidden">
          {activeTab === 'dashboard' && (
            <DashboardView
              gitDiff={gitDiff}
              setGitDiff={setGitDiff}
              githubRepo={githubRepo}
              setGithubRepo={setGithubRepo}
              inputType={inputType}
              setInputType={setInputType}
              author={author}
              setAuthor={setAuthor}
              state={state}
              onStart={handleStart}
              onApplyFix={handleApplyFix}
              onIgnoreForce={handleIgnoreForce}
            />
          )}

          {activeTab === 'security' && (
            <SecurityView state={state} onRunDeepScan={() => { }} />
          )}

          {activeTab === 'logs' && (
            <LogsView
              state={state}
              autoScroll={autoScroll}
              setAutoScroll={setAutoScroll}
              onClearLogs={() => setState((prev) => ({ ...prev, events: [] }))}
              timelineEndRef={timelineEndRef}
            />
          )}
        </main>
      </div>

    </div>
  );
}