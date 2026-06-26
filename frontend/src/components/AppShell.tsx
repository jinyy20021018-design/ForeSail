import type { Language } from "../i18n";
import type { ReactNode } from "react";

type Props = {
  activePath: string;
  children: ReactNode;
  language: Language;
  onNavigate: (path: string) => void;
  onToggleLanguage: () => void;
};

const navItems = [
  { label: "Case Library", path: "/cases", marker: "CL" },
  { label: "Action Center", path: "/cases", marker: "AC", badge: "12" },
  { label: "Agent Run History", path: "/cases", marker: "AR" },
  { label: "Documents", path: "/cases", marker: "DO" },
  { label: "Reports", path: "/cases", marker: "RP" },
  { label: "Settings", path: "/cases", marker: "ST" }
];

export function AppShell({ activePath, children, language, onNavigate, onToggleLanguage }: Props) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" type="button" onClick={() => onNavigate("/cases")}>
          <span className="brand-mark">FS</span>
          <span>
            <strong>ForeSail</strong>
            <small>Trade Monitor</small>
          </span>
        </button>

        <nav className="side-nav">
          {navItems.map((item) => (
            <button
              key={item.label}
              className={activePath.startsWith(item.path) && item.label === "Case Library" ? "nav-item active" : "nav-item"}
              type="button"
              onClick={() => onNavigate(item.path)}
            >
              <span>{item.marker}</span>
              <strong>{item.label}</strong>
              {item.badge && <em>{item.badge}</em>}
            </button>
          ))}
        </nav>

        <div className="snapshot-box">
          <strong>Today's Snapshot</strong>
          <p><span>At Risk</span><b className="danger-text">3</b></p>
          <p><span>Action Required</span><b className="danger-text">4</b></p>
          <p><span>Deadlines in 7 Days</span><b className="warning-text">5</b></p>
          <p><span>Open Information Gaps</span><b className="primary-text">8</b></p>
        </div>
      </aside>

      <div className="shell-main">
        <header className="topbar">
          <button className="ghost-button" type="button" onClick={onToggleLanguage}>
            {language === "en" ? "中文" : "English"}
          </button>
          <div className="user-chip">
            <span>JL</span>
            <div>
              <strong>Jenny Li</strong>
              <small>Trade Ops</small>
            </div>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
