interface FooterProps {
  onClearSession: () => void;
}

export default function Footer({ onClearSession }: FooterProps) {
  return (
    <footer className="fixed bottom-0 left-0 w-full flex justify-between items-center px-lg h-12 gap-lg z-40 bg-surface-container-lowest border-t border-outline-variant text-xs">
      <div className="flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></span>
        <span className="font-code-md text-on-surface-variant">All Guardrails Active</span>
      </div>
      <div className="flex items-center gap-md">
        <button
          onClick={onClearSession}
          className="font-code-md text-on-surface-variant hover:text-primary transition-all flex items-center gap-0.5 hover:underline"
        >
          <span className="material-symbols-outlined text-sm">refresh</span>
          Clear Session
        </button>
        <div className="h-4 w-px bg-outline-variant"></div>
        <span className="font-code-md text-on-surface-variant opacity-60">© 2024 DevOps Deki-Guardrail</span>
      </div>
    </footer>
  );
}
