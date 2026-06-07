interface SidebarProps {
  activeTab: 'dashboard' | 'security' | 'logs';
  setActiveTab: (tab: 'dashboard' | 'security' | 'logs') => void;
}

export default function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  return (
    <aside className="hidden md:flex flex-col py-md gap-sm bg-surface-container-low border-r border-outline-variant h-full w-64">
      <div className="px-lg pb-md">
        <div className="font-headline-sm text-headline-sm font-bold text-primary">System View</div>
        <div className="font-body-md text-body-md text-on-surface-variant">Hindsight Cloud: Connected</div>
      </div>
      <div className="flex flex-col gap-xs flex-1">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`mx-2 px-md py-sm rounded-lg flex items-center gap-sm transition-all duration-200 text-left ${
            activeTab === 'dashboard' ? 'bg-secondary-container text-white font-semibold' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
          }`}
        >
          <span className="material-symbols-outlined">dashboard</span>
          <span className="font-body-md text-body-md">Dashboard</span>
        </button>
        <button
          onClick={() => setActiveTab('security')}
          className={`mx-2 px-md py-sm rounded-lg flex items-center gap-sm transition-all duration-200 text-left ${
            activeTab === 'security' ? 'bg-secondary-container text-white font-semibold' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
          }`}
        >
          <span className="material-symbols-outlined">security</span>
          <span className="font-body-md text-body-md">Security</span>
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={`mx-2 px-md py-sm rounded-lg flex items-center gap-sm transition-all duration-200 text-left ${
            activeTab === 'logs' ? 'bg-secondary-container text-white font-semibold' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
          }`}
        >
          <span className="material-symbols-outlined">terminal</span>
          <span className="font-body-md text-body-md">Logs</span>
        </button>
      </div>
    </aside>
  );
}
