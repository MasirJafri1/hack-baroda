import ReactMarkdown from 'react-markdown';
import { PipelineRunState } from '../types';
import { stageLabels, stages } from '../constants';

const MarkdownRenderer = ({ content }: { content: string }) => {
  return (
    <ReactMarkdown
      components={{
        code({ node, inline, className, children, ...props }) {
          return inline ? (
            <code className="bg-slate-100 dark:bg-slate-800 text-red-600 px-1 py-0.5 rounded font-mono text-[10px]" {...props}>
              {children}
            </code>
          ) : (
            <pre className="bg-[#0F172A] text-white p-2.5 rounded font-mono text-[10px] overflow-x-auto my-2 leading-normal">
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

interface DashboardViewProps {
  gitDiff: string;
  setGitDiff: (diff: string) => void;
  githubRepo: string;
  setGithubRepo: (repo: string) => void;
  inputType: 'diff' | 'github';
  setInputType: (type: 'diff' | 'github') => void;
  author: string;
  setAuthor: (author: string) => void;
  state: PipelineRunState;
  onStart: (overrideDiff?: string, overrideType?: 'diff' | 'github') => void;
  onApplyFix: () => void;
  onIgnoreForce: () => void;
}

export default function DashboardView({
  gitDiff,
  setGitDiff,
  githubRepo,
  setGithubRepo,
  inputType,
  setInputType,
  author,
  setAuthor,
  state,
  onStart,
  onApplyFix,
  onIgnoreForce,
}: DashboardViewProps) {
  const verdict = state.finalPayload?.final_audit_report?.verdict;
  const sessionId = state.sessionId || state.finalPayload?.session_id || 'waiting';

  const githubData = state.finalPayload?.pipeline_metadata?.github_data;
  const isBlocked = verdict === 'BLOCKED';
  const isApproved = verdict === 'APPROVED';
  const isReview = verdict === 'REQUIRES_REVIEW';

  return (
    <div className="h-full grid grid-cols-1 lg:grid-cols-12 gap-0">

      {/* Panel 1: The Trigger */}
      <section className="lg:col-span-4 border-r border-outline-variant flex flex-col bg-surface-container-lowest overflow-hidden">
        <div className="p-md border-b border-outline-variant flex justify-between items-center">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-secondary">history</span>
            <h2 className="font-headline-sm text-headline-sm font-semibold text-primary">The Trigger</h2>
          </div>
          <span className="label-caps font-label-caps px-sm py-0.5 bg-surface-container-high rounded text-on-surface-variant">
            {inputType === 'github' ? 'GITHUB REPO' : 'LOCAL DIFF'}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-md custom-scrollbar space-y-md">
          {/* Input Type Selector */}
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1">INPUT SOURCE</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setInputType('github')}
                className={`text-xs py-1.5 rounded transition-all ${inputType === 'github' ? 'bg-secondary text-white font-bold' : 'bg-surface-container-high text-on-surface'
                  }`}
              >
                GitHub Crawler
              </button>
              <button
                type="button"
                onClick={() => setInputType('diff')}
                className={`text-xs py-1.5 rounded transition-all ${inputType === 'diff' ? 'bg-secondary text-white font-bold' : 'bg-surface-container-high text-on-surface'
                  }`}
              >
                Manual Git Diff
              </button>
            </div>
          </div>

          {/* GitHub Repo Input */}
          {inputType === 'github' && (
            <div className="space-y-2">
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant mb-1">REPOSITORY PATH</label>
                <input
                  className="w-full bg-surface-container-low border border-outline-variant rounded px-2 py-1.5 text-sm focus:ring-1 focus:ring-secondary outline-none"
                  value={githubRepo}
                  placeholder="owner/repo or HTTP URL"
                  onChange={(e) => setGithubRepo(e.target.value)}
                />
              </div>
              <div className="text-[11px] text-on-surface-variant bg-surface-container-low p-2 rounded">
                💡 Reads repository commits, fetches the newest commit's diff, and pulls issues.
              </div>
            </div>
          )}

          {/* Git Diff Input */}
          {inputType === 'diff' && (
            <div className="flex-1 flex flex-col">
              <label className="block text-xs font-semibold text-on-surface-variant mb-1">GIT UNIFIED DIFF</label>
              <textarea
                className="w-full bg-surface-container-low border border-outline-variant rounded p-2 text-xs code-font h-64 focus:ring-1 focus:ring-secondary outline-none"
                value={gitDiff}
                onChange={(e) => setGitDiff(e.target.value)}
                spellCheck={false}
              />
            </div>
          )}

          {/* Common: Author Name */}
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1">AUTHOR IDENTIFICATION</label>
            <input
              className="w-full bg-surface-container-low border border-outline-variant rounded px-2 py-1.5 text-sm focus:ring-1 focus:ring-secondary outline-none"
              value={author}
              placeholder="e.g. developer_name"
              onChange={(e) => setAuthor(e.target.value)}
            />
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex gap-2">
            <button
              onClick={() => onStart()}
              disabled={state.isRunning}
              className="flex-1 py-2 bg-primary text-white font-bold rounded hover:opacity-90 transition-all flex items-center justify-center gap-1 text-xs"
            >
              <span className="material-symbols-outlined text-sm">play_arrow</span>
              {state.isRunning ? 'Executing...' : 'Start Audit'}
            </button>
          </div>

          {githubData && (
            <div className="pt-4 border-t border-outline-variant space-y-3">
              <h4 className="font-semibold text-sm">GitHub Crawler Results</h4>
              <p className="text-xs text-on-surface-variant">Repository: <span className="font-semibold text-on-surface">{githubRepo}</span></p>

              {githubData.commits && githubData.commits.length > 0 && (
                <div>
                  <h5 className="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-1">Recent Commits</h5>
                  <div className="space-y-1">
                    {githubData.commits.map((commit, idx) => (
                      <div key={idx} className="p-1.5 bg-surface-container-low rounded text-xs flex justify-between items-start gap-1">
                        <div className="overflow-hidden">
                          <p className="font-semibold truncate">{commit.message}</p>
                          <p className="text-[10px] text-on-surface-variant">by {commit.author}</p>
                        </div>
                        <span className="font-mono text-[10px] bg-surface-container-high px-1 rounded">{commit.sha}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {githubData.issues && githubData.issues.length > 0 && (
                <div>
                  <h5 className="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider mb-1">Open Issues ({githubData.issues.length})</h5>
                  <div className="space-y-1 max-h-40 overflow-y-auto custom-scrollbar">
                    {githubData.issues.map((issue, idx) => (
                      <div key={idx} className="p-1.5 bg-surface-container-low rounded text-xs flex justify-between items-center gap-1">
                        <span className="truncate">#{issue.number}: {issue.title}</span>
                        <span className={`text-[9px] uppercase px-1 rounded font-bold ${issue.state === 'open' ? 'bg-error-container text-error' : 'bg-green-100 text-green-700'}`}>
                          {issue.state}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {inputType === 'github' && state.finalPayload?.pipeline_metadata?.changed_files && (
            <div className="pt-4 border-t border-outline-variant">
              <label className="block text-xs font-semibold text-on-surface-variant mb-1">EXTRACTED DIFF FROM GITHUB</label>
              <div className="rounded border border-outline-variant overflow-hidden bg-white">
                <div className="bg-surface-container-low px-2 py-1 border-b border-outline-variant flex gap-1">
                  <span className="text-[10px] font-mono font-semibold text-on-surface-variant truncate">
                    {state.finalPayload.pipeline_metadata.changed_files[0] || 'Unknown File'}
                  </span>
                </div>
                <pre className="font-code-md text-[11px] p-2 overflow-x-auto max-h-48 bg-[#0F172A] text-white">
                  {gitDiff}
                </pre>
              </div>
            </div>
          )}

        </div>
      </section>

      {/* Panel 2: The Brain */}
      <section className="lg:col-span-4 border-r border-outline-variant flex flex-col bg-surface overflow-hidden">
        <div className="p-md border-b border-outline-variant flex justify-between items-center bg-white">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-tertiary-fixed-dim" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
            <h2 className="font-headline-sm text-headline-sm font-semibold text-primary">The Brain</h2>
          </div>
          {state.finalPayload && (
            <div className={`flex items-center gap-xs px-sm py-0.5 rounded-full ${verdict === 'BLOCKED' ? 'bg-error-container text-on-error-container' : verdict === 'APPROVED' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-800'
              }`}>
              <span className="material-symbols-outlined text-[14px]">{verdict === 'BLOCKED' ? 'warning' : verdict === 'APPROVED' ? 'check_circle' : 'help_outline'}</span>
              <span className="font-label-caps text-label-caps uppercase">{verdict || 'PENDING'}</span>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-md space-y-md custom-scrollbar">
          {/* Hindsight Triage Status — real data from triage_layer */}
          <div className="space-y-sm">
            <h3 className="font-label-caps text-label-caps text-on-surface-variant font-bold">HINDSIGHT TRIAGE STATUS</h3>
            <div className={`rounded-lg border p-sm flex items-center gap-3 ${!state.finalPayload
                ? 'border-outline-variant bg-surface-container-low'
                : state.finalPayload.triage_layer.risk_flagged
                  ? 'border-error/40 bg-error-container'
                  : 'border-green-200 bg-green-50'
              }`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${!state.finalPayload ? 'bg-surface-container-high text-on-surface-variant' :
                  state.finalPayload.triage_layer.risk_flagged ? 'bg-error text-white' : 'bg-green-100 text-green-700'
                }`}>
                <span className="material-symbols-outlined text-base">
                  {!state.finalPayload ? 'hourglass_empty' : state.finalPayload.triage_layer.risk_flagged ? 'warning' : 'check_circle'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-xs font-bold ${!state.finalPayload ? 'text-on-surface-variant' :
                    state.finalPayload.triage_layer.risk_flagged ? 'text-error' : 'text-green-700'
                  }`}>
                  {!state.finalPayload ? 'Awaiting run...' :
                    state.finalPayload.triage_layer.risk_flagged
                      ? `Risk Flagged — ${state.finalPayload.triage_layer.matches_found} match(es) found`
                      : 'Cleared — No historical risk patterns matched'}
                </p>
                {state.finalPayload?.triage_layer.reasoning && (
                  <p className="text-[11px] text-on-surface-variant truncate mt-0.5" title={state.finalPayload.triage_layer.reasoning}>
                    {state.finalPayload.triage_layer.reasoning}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Agent Status Stack */}
          <div className="space-y-sm">
            <h3 className="font-label-caps text-label-caps text-on-surface-variant font-bold">AGENT TRIAGE STACK</h3>
            {stages.map((stage) => {
              const isActive = state.currentStage === stage;
              const isDone = state.completedStages.includes(stage);
              return (
                <div
                  key={stage}
                  className={`p-sm bg-white border border-outline-variant rounded flex items-center gap-md relative overflow-hidden transition-all duration-200 ${isActive ? 'border-secondary ring-1 ring-secondary' : ''
                    } ${!isActive && !isDone ? 'opacity-55 grayscale' : ''}`}
                >
                  {isActive && <div className="absolute inset-0 bg-secondary/5"></div>}
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center relative z-10 ${isDone ? 'bg-green-100 text-green-700' : isActive ? 'bg-secondary-container text-white' : 'bg-surface-container-high text-primary'
                    }`}>
                    <span className="material-symbols-outlined text-md">
                      {stage === 'github_crawler' ? 'cloud_download' :
                        stage === 'context_agent' ? 'art_track' :
                          stage === 'reviewer_v1' ? 'security' :
                            stage === 'reviewer_v2' ? 'search' :
                              stage === 'retrieval_agent' ? 'database' :
                                stage === 'git_expert' ? 'history' :
                                  stage === 'cloud_expert' ? 'cloud' :
                                    stage === 'code_expert' ? 'code' : 'psychology'}
                    </span>
                  </div>
                  <div className="flex-1 relative z-10">
                    <p className="font-body-md text-body-md font-bold leading-none">{stageLabels[stage]}</p>
                    <p className="text-[11px] text-on-surface-variant truncate mt-0.5">
                      {isActive ? 'Processing...' : isDone ? 'Task Completed' : 'Waiting...'}
                    </p>
                  </div>
                  {isDone ? (
                    <span className="material-symbols-outlined text-green-500 z-10">check_circle</span>
                  ) : isActive ? (
                    <div className="w-2 h-2 rounded-full bg-secondary animate-ping relative z-10"></div>
                  ) : (
                    <span className="material-symbols-outlined text-on-surface-variant text-sm z-10">hourglass_empty</span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Pipeline Progress Summary */}
          <div className={`rounded-lg border p-sm flex flex-col gap-1 ${!state.finalPayload && !state.isRunning
              ? 'border-outline-variant bg-surface-container-low'
              : state.isRunning
                ? 'border-secondary/40 bg-secondary/5'
                : isBlocked ? 'border-error/40 bg-error-container'
                  : isApproved ? 'border-green-200 bg-green-50'
                    : 'border-yellow-200 bg-yellow-50'
            }`}>
            <p className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Pipeline Status</p>
            <p className={`text-sm font-extrabold ${state.isRunning ? 'text-secondary' :
                !state.finalPayload ? 'text-on-surface-variant' :
                  isBlocked ? 'text-error' : isApproved ? 'text-green-700' : 'text-yellow-700'
              }`}>
              {state.isRunning
                ? `Running — ${state.completedStages.length} stage(s) done`
                : !state.finalPayload
                  ? 'Idle — No run yet'
                  : isBlocked ? 'BLOCKED'
                    : isApproved ? 'APPROVED'
                      : 'REQUIRES REVIEW'}
            </p>
            {state.finalPayload && (
              <p className="text-[11px] text-on-surface-variant">
                {state.completedStages.length} of {state.completedStages.length} stages completed
              </p>
            )}
          </div>

        </div>
      </section>

      {/* Panel 3: Executive Verdict */}
      <section className="lg:col-span-4 flex flex-col bg-surface-container-lowest overflow-hidden">
        <div className={`p-md border-b border-outline-variant flex justify-between items-center ${isBlocked ? 'bg-error-container text-on-error-container' : isApproved ? 'bg-green-100 text-green-800' : isReview ? 'bg-yellow-100 text-yellow-800' : 'bg-surface-container-low'
          }`}>
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
              {isBlocked ? 'block' : isApproved ? 'check_circle' : 'security'}
            </span>
            <h2 className="font-headline-sm text-headline-sm font-bold">Executive Verdict</h2>
          </div>
        </div>

        <div className="flex-1 overflow-y-scroll p-md space-y-md custom-scrollbar">
          {!state.finalPayload ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-md">
              <div className="w-16 h-16 rounded-full bg-surface-container-low flex items-center justify-center mb-md text-on-surface-variant">
                <span className="material-symbols-outlined text-3xl">hourglass_empty</span>
              </div>
              <h3 className="font-bold text-on-surface mb-sm">No Audit Run Executed</h3>
              <p className="text-xs text-on-surface-variant max-w-xs">
                Configure the triggers on the left and run the pipeline to start Hindsight's real-time risk assessment.
              </p>
            </div>
          ) : (
            <div className="space-y-md">
              <div className="flex flex-col items-center py-sm text-center gap-md">
                <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center ${isBlocked ? 'border-error text-error bg-error/5' : isApproved ? 'border-green-500 text-green-500 bg-green-50' : 'border-yellow-500 text-yellow-500 bg-yellow-50'
                  }`}>
                  <span className="material-symbols-outlined text-3xl font-bold">
                    {isBlocked ? 'cancel' : isApproved ? 'verified' : 'help'}
                  </span>
                </div>
                <div>
                  <h1 className={`font-headline-md text-headline-md font-extrabold ${isBlocked ? 'text-error' : isApproved ? 'text-green-600' : 'text-yellow-600'}`}>
                    {isBlocked ? 'DEPLOYMENT BLOCKED' : isApproved ? 'DEPLOYMENT CLEARED' : 'NEEDS MANUAL REVIEW'}
                  </h1>
                  <p className="font-body-md text-on-surface-variant mt-1 text-xs">
                    Session Identifier: <span className="font-mono text-on-surface bg-surface-container-low px-1 rounded">{sessionId}</span>
                  </p>
                </div>
              </div>

              {/* Conclusion */}
              <div className="p-md bg-white border border-outline-variant rounded-lg">
                <h3 className="font-label-caps text-label-caps text-on-surface-variant mb-sm">EXECUTIVE CONCLUSION</h3>
                <div className="text-xs text-on-surface leading-normal markdown-card">
                  <MarkdownRenderer content={state.finalPayload.final_audit_report.conclusion || 'No conclusion details provided.'} />
                </div>
              </div>

              {/* Risks */}
              {state.finalPayload.final_audit_report.risks && state.finalPayload.final_audit_report.risks.length > 0 && (
                <div className="p-md bg-white border border-outline-variant rounded-lg">
                  <h3 className="font-label-caps text-label-caps text-red-600 mb-sm">IDENTIFIED RISKS ({state.finalPayload.final_audit_report.risks.length})</h3>
                  <ul className="list-disc list-inside text-xs text-on-surface space-y-1">
                    {state.finalPayload.final_audit_report.risks.map((risk, idx) => (
                      <li key={idx} className="leading-tight">{risk}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Mitigation Patches */}
              {state.finalPayload.final_audit_report.mitigation_patches && state.finalPayload.final_audit_report.mitigation_patches.length > 0 && (
                <div className="p-md bg-white border border-outline-variant rounded-lg">
                  <h3 className="font-label-caps text-label-caps text-green-700 mb-sm">EXPERT MITIGATION SUGGESTIONS</h3>
                  <div className="space-y-2">
                    {state.finalPayload.final_audit_report.mitigation_patches.map((patch, idx) => (
                      <div key={idx} className="bg-surface-container-low p-2.5 rounded text-xs border-l-2 border-green-500">
                        <MarkdownRenderer content={patch} />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Preventive Fix */}
              {state.finalPayload.final_audit_report.example_patch_code && (
                <div className="space-y-sm">
                  <h3 className="font-label-caps text-label-caps text-on-surface-variant">RECOMMENDED PREVENTIVE FIX</h3>
                  <div className="rounded-lg border border-outline-variant overflow-hidden bg-surface-container-high">
                    <div className="bg-surface-container-highest px-3 py-1.5 flex justify-between items-center text-xs">
                      <span className="font-code-md text-on-surface-variant">remediation-patch.ts</span>
                      <button
                        onClick={() => navigator.clipboard.writeText(state.finalPayload!.final_audit_report.example_patch_code)}
                        className="material-symbols-outlined text-secondary text-sm cursor-pointer hover:bg-surface-container-high p-1 rounded"
                      >
                        content_copy
                      </button>
                    </div>
                    <pre className="font-code-md text-[11px] p-3 bg-[#0F172A] text-white overflow-x-auto max-h-48 leading-relaxed">
                      {state.finalPayload.final_audit_report.example_patch_code}
                    </pre>
                  </div>
                </div>
              )}

              {/* Panel Actions */}
              <div className="flex gap-md pt-2">
                {isBlocked && state.finalPayload.final_audit_report.example_patch_code && (
                  <button
                    onClick={onApplyFix}
                    className="flex-1 py-2.5 bg-primary text-white font-bold rounded hover:opacity-90 transition-all flex items-center justify-center gap-1 text-xs"
                  >
                    <span className="material-symbols-outlined text-sm">auto_fix_high</span>
                    Apply Auto Fix
                  </button>
                )}
                <button
                  onClick={onIgnoreForce}
                  className="flex-1 py-2.5 border border-outline text-on-surface font-bold rounded hover:bg-surface-container-high transition-all text-xs"
                >
                  Ignore &amp; Bypass
                </button>
              </div>

            </div>
          )}
        </div>
      </section>

    </div>
  );
}
