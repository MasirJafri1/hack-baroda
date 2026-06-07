interface SidebarProps {
  activeTab: 'dashboard' | 'security' | 'logs';
  setActiveTab: (tab: 'dashboard' | 'security' | 'logs') => void;
}

export default function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  return (
    <aside className="hidden md:flex flex-col py-6 bg-surface-container-low border-r border-outline-variant h-full w-64 select-none">
      {/* Header & Connection Badge */}
      <div className="px-6 pb-4">
        <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant/70">System Monitor</div>
        <div className="flex items-center gap-2 mt-2 bg-emerald-500/10 text-emerald-800 px-3 py-1.5 rounded-lg border border-emerald-500/20 w-fit text-[11px] font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-sm shadow-emerald-500/50"></span>
          Hindsight Connected
        </div>
      </div>

      <div className="h-px bg-outline-variant/60 mx-4 mb-4"></div>

      {/* Navigation Options */}
      <div className="flex flex-col gap-1.5 flex-1">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`mx-3 px-4 py-2.5 rounded-lg flex items-center gap-3 transition-all duration-200 text-left outline-none ${
            activeTab === 'dashboard'
              ? 'bg-primary text-white font-semibold shadow-sm shadow-primary/10'
              : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
          }`}
        >
          <span className="material-symbols-outlined text-[20px] flex items-center justify-center">dashboard</span>
          <span className="text-sm font-semibold">Dashboard</span>
        </button>
        
        <button
          onClick={() => setActiveTab('security')}
          className={`mx-3 px-4 py-2.5 rounded-lg flex items-center gap-3 transition-all duration-200 text-left outline-none ${
            activeTab === 'security'
              ? 'bg-primary text-white font-semibold shadow-sm shadow-primary/10'
              : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
          }`}
        >
          <span className="material-symbols-outlined text-[20px] flex items-center justify-center">security</span>
          <span className="text-sm font-semibold">Security</span>
        </button>
        
        <button
          onClick={() => setActiveTab('logs')}
          className={`mx-3 px-4 py-2.5 rounded-lg flex items-center gap-3 transition-all duration-200 text-left outline-none ${
            activeTab === 'logs'
              ? 'bg-primary text-white font-semibold shadow-sm shadow-primary/10'
              : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
          }`}
        >
          <span className="material-symbols-outlined text-[20px] flex items-center justify-center">terminal</span>
          <span className="text-sm font-semibold">Audit Logs</span>
        </button>
      </div>

      {/* Footer Version Info */}
      <div className="px-6 py-4 mt-auto border-t border-outline-variant/60 bg-surface-container-low flex justify-between items-center opacity-60">
        <span className="text-[10px] font-mono tracking-tight">VERSION: v0.1.0-beta</span>
        <span className="text-[10px] font-mono tracking-tight font-semibold bg-outline-variant/30 px-1.5 py-0.5 rounded">localhost</span>
      </div>
    </aside>
  );
}
