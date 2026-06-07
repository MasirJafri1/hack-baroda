import ReactMarkdown from 'react-markdown';
import { PipelineRunState } from '../types';

const MarkdownRenderer = ({ content }: { content: string }) => {
  return (
    <ReactMarkdown
      components={{
        code({ node, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !match ? (
            <code className="bg-slate-100 dark:bg-slate-800 text-red-600 px-1 py-0.5 rounded font-mono text-[10px]" {...props}>
              {children}
            </code>
          ) : (
            <pre className="bg-[#1e1e20] text-white p-2.5 rounded font-mono text-[10px] overflow-x-auto my-2 leading-normal">
              <code className={className} {...props}>
                {children}
              </code>
            </pre>
          );
        },
        p({ children }) {
          return <p className="mb-2 last:mb-0 leading-normal">{children}</p>;
        },
        ul({ children }) {
          return <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>;
        },
        ol({ children }) {
          return <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>;
        },
        li({ children }) {
          return <li className="leading-tight">{children}</li>;
        },
        h1({ children }) { return <h1 className="text-xs font-bold mt-2 mb-1 text-primary">{children}</h1>; },
        h2({ children }) { return <h2 className="text-xs font-bold mt-1.5 mb-1 text-primary">{children}</h2>; },
        h3({ children }) { return <h3 className="text-[11px] font-bold mt-1.5 mb-1 text-primary">{children}</h3>; },
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

interface SecurityViewProps {
  state: PipelineRunState;
  onRunDeepScan: () => void;
}

export default function SecurityView({ state }: SecurityViewProps) {
  const payload = state.finalPayload;
  const hasRun = !!payload;
  const verdict = payload?.final_audit_report?.verdict;
  const classification = payload?.pipeline_metadata?.classification;
  const risks = payload?.final_audit_report?.risks || [];
  const triage = payload?.triage_layer;
  const expertAnalysis = payload?.expert_analysis;

  // --------------------------------------------------------------------------
  // Heatmap — driven by real verdict + triage data
  // --------------------------------------------------------------------------
  const renderHeatmapCells = () => {
    const totalCells = 24;
    const cells = [];

    if (!hasRun) {
      for (let i = 0; i < totalCells; i++) {
        cells.push(
          <div
            key={i}
            className="col-span-1 bg-surface-container border border-outline-variant rounded-sm"
          />
        );
      }
    } else if (verdict === 'APPROVED') {
      for (let i = 0; i < totalCells; i++) {
        const isHighlight = i % 7 === 0;
        cells.push(
          <div
            key={i}
            className={`col-span-1 border rounded-sm transition-all duration-300 hover:scale-105 cursor-pointer ${
              isHighlight ? 'bg-green-300 border-green-400' : 'bg-green-100 border-green-200'
            }`}
            title="Cleared: File analyzed and marked safe"
          />
        );
      }
    } else if (verdict === 'BLOCKED') {
      const matchesCount = triage?.matches_found || 1;
      const redCount = Math.min(8, Math.max(2, matchesCount * 2));
      for (let i = 0; i < totalCells; i++) {
        const isRed = i < redCount;
        const isWarning = !isRed && i < redCount + 4;
        cells.push(
          <div
            key={i}
            className={`col-span-1 border rounded-sm transition-all duration-300 hover:scale-105 cursor-pointer ${
              isRed
                ? 'bg-error border-error-container animate-pulse'
                : isWarning
                  ? 'bg-secondary-container/40 border-secondary'
                  : 'bg-primary-fixed-dim/20 border-outline-variant'
            }`}
            title={isRed ? 'Critical Risk: Vulnerability detected' : isWarning ? 'Warning: Review required' : 'Low concern'}
          />
        );
      }
    } else {
      for (let i = 0; i < totalCells; i++) {
        const isOrange = i % 5 === 0;
        cells.push(
          <div
            key={i}
            className={`col-span-1 border rounded-sm transition-all duration-300 hover:scale-105 cursor-pointer ${
              isOrange ? 'bg-yellow-400 border-yellow-500' : 'bg-primary-fixed-dim/20 border-outline-variant'
            }`}
            title={isOrange ? 'Review required' : 'Analyzed'}
          />
        );
      }
    }
    return cells;
  };

  // --------------------------------------------------------------------------
  // Threat Feed — driven by real SSE stage events + actual risks from backend
  // --------------------------------------------------------------------------
  const getThreatFeedItems = () => {
    if (!hasRun && !state.isRunning) return null;

    const items: { id: string; type: string; code: string; desc: string }[] = [];

    state.events.forEach((ev, idx) => {
      if (ev.event === 'stage_completed') {
        const stage = String(ev.data?.stage || '');
        if (stage === 'github_crawler') {
          items.push({
            id: `crawler-${idx}`,
            type: 'info',
            code: 'GITHUB_CRAWLER_COMPLETE',
            desc: 'Repository resources crawled — latest commit diff extracted.',
          });
        } else if (stage === 'context_agent') {
          const fileCount = payload?.pipeline_metadata?.changed_files?.length ?? 0;
          items.push({
            id: `context-${idx}`,
            type: 'info',
            code: 'FILES_CLASSIFIED',
            desc: `Diff ingested. ${fileCount} changed file(s) classified.`,
          });
        } else if (stage === 'reviewer_v1') {
          items.push({
            id: `rv1-${idx}`,
            type: triage?.risk_flagged ? 'error' : 'success',
            code: triage?.risk_flagged ? 'TRIAGE_RISK_FLAGGED' : 'TRIAGE_CLEARED',
            desc: triage?.risk_flagged
              ? `Risk flagged — ${triage.matches_found} historical incident match(es).`
              : 'No historical risk patterns matched. Diff is clear.',
          });
        }
      }
    });

    risks.forEach((risk, idx) => {
      items.push({
        id: `risk-${idx}`,
        type: 'error',
        code: verdict === 'BLOCKED' ? 'CRITICAL_RISK' : 'RISK_ALERT',
        desc: risk,
      });
    });

    if (verdict === 'APPROVED' && items.length > 0) {
      items.push({
        id: 'all-clear',
        type: 'success',
        code: 'PIPELINE_CLEARED',
        desc: 'All agents completed — no blocking issues found.',
      });
    }

    return items;
  };

  const threatItems = getThreatFeedItems();

  // --------------------------------------------------------------------------
  // Classification Breakdown — real data from context_agent
  // --------------------------------------------------------------------------
  const renderClassification = () => {
    if (!hasRun) {
      return (
        <p className="text-xs text-on-surface-variant italic text-center py-6">
          Run the pipeline to see file classification.
        </p>
      );
    }

    const cats = [
      { label: 'App Code', icon: 'code', files: classification?.app_code || [], color: 'text-blue-600 bg-blue-50 border-blue-200' },
      { label: 'Cloud Infra', icon: 'cloud', files: classification?.cloud_infra || [], color: 'text-orange-600 bg-orange-50 border-orange-200' },
      { label: 'Git Meta', icon: 'history', files: classification?.git_meta || [], color: 'text-purple-600 bg-purple-50 border-purple-200' },
    ];

    const allEmpty = cats.every(c => c.files.length === 0);
    if (allEmpty) {
      return (
        <p className="text-xs text-on-surface-variant italic text-center py-6">
          No files were classified in this run.
        </p>
      );
    }

    return (
      <div className="space-y-3">
        {cats.map(cat => (
          cat.files.length > 0 && (
            <div key={cat.label}>
              <div className="flex items-center gap-1.5 mb-1.5">
                <span className="material-symbols-outlined text-sm text-on-surface-variant">{cat.icon}</span>
                <span className="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant">{cat.label}</span>
                <span className="ml-auto text-[10px] font-bold bg-surface-container-high px-1.5 rounded-full">{cat.files.length}</span>
              </div>
              <div className="space-y-1">
                {cat.files.map((f, i) => (
                  <div key={i} className={`text-[11px] px-2 py-1 rounded border font-mono truncate ${cat.color}`} title={f}>
                    {f}
                  </div>
                ))}
              </div>
            </div>
          )
        ))}
      </div>
    );
  };

  // --------------------------------------------------------------------------
  // Expert Analysis — real notes from git_expert, cloud_expert, code_expert
  // --------------------------------------------------------------------------
  const renderExpertPanel = (title: string, icon: string, content: string | undefined, color: string) => {
    if (!content) return null;
    return (
      <div className={`bg-white border border-outline-variant rounded-xl overflow-hidden`}>
        <div className={`px-md py-3 border-b border-outline-variant flex items-center gap-2 ${color}`}>
          <span className="material-symbols-outlined text-sm">{icon}</span>
          <h4 className="text-xs font-bold uppercase tracking-wide">{title}</h4>
        </div>
        <div className="p-md text-xs text-on-surface leading-normal markdown-card">
          <MarkdownRenderer content={content} />
        </div>
      </div>
    );
  };

  const verdictColor = verdict === 'BLOCKED'
    ? 'text-error'
    : verdict === 'APPROVED'
      ? 'text-green-600'
      : 'text-yellow-600';

  const verdictBg = verdict === 'BLOCKED'
    ? 'bg-error-container border-error/30'
    : verdict === 'APPROVED'
      ? 'bg-green-50 border-green-200'
      : 'bg-yellow-50 border-yellow-200';

  return (
    <div className="h-full overflow-y-auto p-lg pb-24 custom-scrollbar bg-background space-y-lg">

      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-primary">Security Analysis</h2>
          <p className="text-xs text-on-surface-variant/80 mt-1">
            Live threat detection powered by Hindsight AI — driven entirely by real pipeline output.
          </p>
        </div>
        {hasRun && (
          <div className={`flex items-center gap-2 px-md py-sm rounded-lg border text-sm font-bold ${verdictBg} ${verdictColor}`}>
            <span className="material-symbols-outlined text-base">
              {verdict === 'BLOCKED' ? 'cancel' : verdict === 'APPROVED' ? 'verified' : 'help'}
            </span>
            {verdict}
          </div>
        )}
      </div>

      {/* Triage Summary Strip */}
      {hasRun && triage && (
        <div className={`rounded-xl border p-md flex flex-wrap gap-lg ${verdictBg}`}>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-on-surface-variant text-base">search</span>
            <div>
              <p className="text-[10px] uppercase font-bold text-on-surface-variant">Historical Matches</p>
              <p className={`font-bold text-sm ${triage.risk_flagged ? 'text-error' : 'text-green-600'}`}>
                {triage.matches_found} found
              </p>
            </div>
          </div>
          <div className="h-8 w-px bg-outline-variant" />
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-on-surface-variant text-base">
              {triage.risk_flagged ? 'warning' : 'check_circle'}
            </span>
            <div>
              <p className="text-[10px] uppercase font-bold text-on-surface-variant">Risk Status</p>
              <p className={`font-bold text-sm ${triage.risk_flagged ? 'text-error' : 'text-green-600'}`}>
                {triage.risk_flagged ? 'Risk Flagged' : 'Clear'}
              </p>
            </div>
          </div>
          {triage.reasoning && (
            <>
              <div className="h-8 w-px bg-outline-variant" />
              <div className="flex-1 min-w-0">
                <p className="text-[10px] uppercase font-bold text-on-surface-variant">Triage Reasoning</p>
                <p className="text-xs text-on-surface truncate" title={triage.reasoning}>{triage.reasoning}</p>
              </div>
            </>
          )}
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-4">

        {/* Vulnerability Heatmap */}
        <div className="col-span-12 lg:col-span-8 bg-white border border-outline-variant rounded-xl p-lg flex flex-col min-h-[260px]">
          <div className="flex justify-between items-center mb-md">
            <h3 className="font-headline-sm text-headline-sm font-bold">Risk Heatmap</h3>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-error"></div><span className="text-xs">Critical</span></div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-yellow-400"></div><span className="text-xs">Warning</span></div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-green-300"></div><span className="text-xs">Clear</span></div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-surface-container"></div><span className="text-xs">Idle</span></div>
            </div>
          </div>
          <div className="flex-1 grid grid-cols-12 grid-rows-6 gap-2">
            {renderHeatmapCells()}
          </div>
          {!hasRun && (
            <p className="text-center text-xs text-on-surface-variant italic mt-3">
              Heatmap populates after running the pipeline.
            </p>
          )}
        </div>

        {/* Threat Feed */}
        <div className="col-span-12 lg:col-span-4 bg-white border border-outline-variant rounded-xl p-lg overflow-hidden flex flex-col max-h-[260px]">
          <div className="flex items-center justify-between mb-md">
            <h3 className="font-headline-sm text-headline-sm font-bold">Threat Feed</h3>
            {(state.isRunning || (triage?.risk_flagged)) && (
              <span className="flex h-2 w-2 rounded-full bg-error animate-pulse"></span>
            )}
          </div>
          <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar">
            {state.isRunning && !hasRun ? (
              <div className="flex flex-col items-center justify-center py-6 text-on-surface-variant text-xs gap-2">
                <span className="material-symbols-outlined animate-spin text-secondary">sync</span>
                <span>Audit pipeline running...</span>
              </div>
            ) : !hasRun ? (
              <p className="text-center py-8 text-on-surface-variant text-xs italic">
                System idle. Run the pipeline to stream threat telemetry.
              </p>
            ) : threatItems && threatItems.length === 0 ? (
              <div className="text-center py-6 text-green-600 text-xs font-semibold flex flex-col items-center gap-1">
                <span className="material-symbols-outlined">check_circle</span>
                No threats detected in this run.
              </div>
            ) : (
              threatItems?.map(item => (
                <div
                  key={item.id}
                  className={`flex gap-3 border-l-2 pl-3 py-1.5 ${
                    item.type === 'error' ? 'border-error' : item.type === 'success' ? 'border-green-500' : 'border-secondary'
                  }`}
                >
                  <div className="flex-1">
                    <p className={`font-mono text-xs font-bold ${
                      item.type === 'error' ? 'text-error' : item.type === 'success' ? 'text-green-600' : 'text-secondary'
                    }`}>{item.code}</p>
                    <p className="text-xs text-on-surface-variant leading-tight mt-0.5">{item.desc}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* File Classification */}
        <div className="col-span-12 lg:col-span-5 bg-white border border-outline-variant rounded-xl p-lg">
          <h3 className="font-headline-sm text-headline-sm font-bold mb-md">File Classification</h3>
          {renderClassification()}
        </div>

        {/* Expert Analysis */}
        <div className="col-span-12 lg:col-span-7 space-y-3">
          <h3 className="font-headline-sm text-headline-sm font-bold">Expert Agent Analysis</h3>
          {!hasRun ? (
            <div className="bg-white border border-outline-variant rounded-xl p-lg text-center">
              <span className="material-symbols-outlined text-3xl text-on-surface-variant mb-2 block">psychology</span>
              <p className="text-xs text-on-surface-variant italic">
                Expert agent findings appear here after a pipeline run.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {renderExpertPanel('Git Expert', 'history', expertAnalysis?.git_expert_notes, 'bg-purple-50 text-purple-700')}
              {renderExpertPanel('Cloud Expert', 'cloud', expertAnalysis?.cloud_expert_notes, 'bg-orange-50 text-orange-700')}
              {renderExpertPanel('Code Expert', 'code', expertAnalysis?.code_expert_notes, 'bg-blue-50 text-blue-700')}
              {!expertAnalysis?.git_expert_notes && !expertAnalysis?.cloud_expert_notes && !expertAnalysis?.code_expert_notes && (
                <div className="bg-white border border-outline-variant rounded-xl p-lg text-center">
                  <p className="text-xs text-on-surface-variant italic">
                    Pipeline approved at triage — specialist agents were not invoked.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
