interface HeaderProps {
  activeTab: 'dashboard' | 'security' | 'logs';
  setActiveTab: (tab: 'dashboard' | 'security' | 'logs') => void;
}

export default function Header({ activeTab, setActiveTab }: HeaderProps) {
  return (
    <header className="bg-surface-container-lowest border-b border-outline-variant flex justify-between items-center w-full px-lg h-16 z-50">
      <div className="flex items-center gap-md">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>security</span>
          <span className="font-headline-md text-headline-md font-bold text-primary">DevOps Guardrail AI</span>
        </div>
        <span className="hidden md:block h-6 w-px bg-outline-variant"></span>
        <nav className="hidden md:flex gap-md">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`font-semibold px-sm py-xs border-b-2 transition-all ${
              activeTab === 'dashboard' ? 'border-secondary text-primary font-bold' : 'border-transparent text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`font-semibold px-sm py-xs border-b-2 transition-all ${
              activeTab === 'security' ? 'border-secondary text-primary font-bold' : 'border-transparent text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Security
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`font-semibold px-sm py-xs border-b-2 transition-all ${
              activeTab === 'logs' ? 'border-secondary text-primary font-bold' : 'border-transparent text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Audit Logs
          </button>
        </nav>
      </div>
      <div className="flex items-center gap-md">
        <div className="flex items-center gap-xs px-sm py-1 rounded-full bg-green-100 text-green-700">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span className="text-xs font-semibold">Guardrails Active</span>
        </div>
        <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:bg-surface-container-high p-1.5 rounded transition-all">notifications</span>
        <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-white text-xs font-bold cursor-pointer">MJ</div>
      </div>
    </header>
  );
}
