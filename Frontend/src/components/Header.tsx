export default function Header() {
  return (
    <header className="bg-surface-container-lowest border-b border-outline-variant flex justify-between items-center w-full px-6 h-16 z-50 select-none">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <span className="material-symbols-outlined text-secondary text-2xl flex items-center justify-center" style={{ fontVariationSettings: "'FILL' 1" }}>security</span>
          <span className="font-bold text-lg tracking-tight text-primary">DevOps Deki-Guardrail</span>
        </div>
        <span className="hidden md:block h-5 w-px bg-outline-variant/60"></span>
        <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-primary/5 text-primary border border-primary/10">
          Agent Mode
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-sm shadow-emerald-500/50"></span>
          <span className="text-[11px] font-bold uppercase tracking-wider">Guardrails Active</span>
        </div>
        
        <button className="material-symbols-outlined text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high p-2 rounded-lg transition-all text-xl cursor-pointer">
          notifications
        </button>
        
        <div className="h-8 w-px bg-outline-variant/60"></div>
        
        <div className="flex items-center gap-2.5 pl-1">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-xs font-bold shadow-sm shadow-primary/10">
            MJ
          </div>
          <div className="hidden sm:flex flex-col">
            <span className="text-xs font-semibold text-primary leading-tight">Masir Jafri</span>
            <span className="text-[10px] text-on-surface-variant opacity-80 leading-none">Security Admin</span>
          </div>
        </div>
      </div>
    </header>
  );
}

