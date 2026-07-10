import type { Language } from "../i18n";
import type { ReactNode } from "react";
import foresailLogo from "../assets/foresail-logo.png";

type Props = {
  activePath: string;
  children: ReactNode;
  language: Language;
  onNavigate: (path: string) => void;
  onToggleLanguage: () => void;
};

export function AppShell({ activePath, children, language, onNavigate, onToggleLanguage }: Props) {
  return (
    <div className="app-shell">
      <div className="app-frame">
        <nav className="fsnav" aria-label="Primary navigation">
          <button className="fsnav-brand" type="button" onClick={() => onNavigate("/cases")} aria-label="ForeSail home">
            <img src={foresailLogo} alt="ForeSail" draggable="false" />
          </button>
          <div className="fsnav-tabs">
            <button className={activePath.startsWith("/cases") ? "active" : ""} type="button" onClick={() => onNavigate("/cases")}>Trade Risk</button>
            <button type="button" onClick={() => onNavigate("/cases")}>Trade Ops</button>
          </div>
          <div className="fsnav-util">
            <button className="fsnav-icon notif" type="button" aria-label="Notifications"><span /></button>
            <button className="fsnav-icon" type="button" aria-label="Help">
              <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M9.5 9a2.5 2.5 0 0 1 4.5 1.5c0 1.5-2 2-2 3.5M12 17h.01" /></svg>
            </button>
            <button className="fsnav-lang" type="button" onClick={onToggleLanguage} aria-label="Switch language">
              <span aria-hidden="true" />
              <small>{language === "en" ? "EN" : "中文"} ▾</small>
            </button>
          </div>
        </nav>
        <main className="shell-main">{children}</main>
      </div>
    </div>
  );
}
