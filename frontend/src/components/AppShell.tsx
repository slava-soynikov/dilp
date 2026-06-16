import { useEffect, useRef, useState, type ReactNode } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../styles/ThemeProvider";
import { t } from "../i18n/ru";

type NavItem = {
  to: string;
  label: string;
  icon: string;
  note?: string;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

function buildSections(hasRole: (r: string) => boolean): NavSection[] {
  const main: NavItem[] = [
    { to: "/", label: t.nav.dashboard, icon: "🏠" },
    { to: "/profile", label: t.nav.profile, icon: "👤" },
  ];
  if (hasRole("parent")) {
    main.push({ to: "/children", label: t.nav.children, icon: "👨‍👩‍👧" });
    main.push({
      to: "/parent-dashboard",
      label: t.nav.parentDashboard,
      icon: "📊",
    });
  }
  if (hasRole("child"))
    main.push({ to: "/curriculum", label: t.nav.curriculum, icon: "📚" });

  const learning: NavItem[] = [];
  if (hasRole("teacher") || hasRole("parent") || hasRole("admin"))
    learning.push({ to: "/groups", label: t.nav.groups, icon: "👥" });
  if (hasRole("admin") || hasRole("teacher")) {
    learning.push({ to: "/programmes", label: t.nav.programmes, icon: "📖" });
    learning.push({ to: "/lesson-contents", label: t.nav.cms, icon: "✏️" });
  }

  const adminItems: NavItem[] = [];
  if (hasRole("admin")) {
    adminItems.push({ to: "/organization", label: t.nav.organization, icon: "🏫" });
    adminItems.push({ to: "/admin", label: t.nav.admin, icon: "🛠️" });
  }
  if (hasRole("admin") || hasRole("auditor") || hasRole("teacher")) {
    adminItems.push({ to: "/reports", label: t.nav.reports, icon: "📊" });
  }
  if (hasRole("admin") || hasRole("auditor")) {
    adminItems.push({ to: "/logs", label: t.nav.logs, icon: "🗂️" });
  }

  const sections: NavSection[] = [{ title: t.nav.sectionMain, items: main }];
  if (learning.length)
    sections.push({ title: t.nav.sectionLearning, items: learning });
  if (adminItems.length)
    sections.push({ title: t.nav.sectionAdmin, items: adminItems });
  return sections;
}

function initialsOf(me: { email: string | null; username: string | null }): string {
  const src = me.username || me.email || "?";
  const cleaned = src.replace(/[^a-zA-Zа-яА-Я0-9]/g, " ").trim();
  const parts = cleaned.split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return cleaned.slice(0, 2).toUpperCase();
}

function roleLabel(roles: string[]): string {
  if (roles.includes("admin")) return `🛠️ ${t.roles.admin}`;
  if (roles.includes("auditor")) return `🗂️ ${t.roles.auditor}`;
  if (roles.includes("teacher")) return `👩‍🏫 ${t.roles.teacher}`;
  if (roles.includes("parent")) return `👨‍👩‍👧 ${t.roles.parent}`;
  if (roles.includes("child")) return `🎒 ${t.roles.child}`;
  return "";
}

export function AppShell({ children }: { children: ReactNode }) {
  const { me, logout } = useAuth();
  const { mode, toggle } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!menuOpen) return;
    function onClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [menuOpen]);

  async function onLogout() {
    setMenuOpen(false);
    await logout();
    navigate("/login", { replace: true });
  }

  const sections = me ? buildSections((r) => me.roles.includes(r)) : [];
  const displayName = me?.username || me?.email || "";
  const role = me ? roleLabel(me.roles) : "";
  const initials = me ? initialsOf(me) : "??";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-left">
          <div className="user-box">
            <div className="avatar" aria-hidden="true">
              {initials}
            </div>
            <div className="user-meta">
              <div className="user-name">{displayName}</div>
              {role && <div className="user-role">{role}</div>}
            </div>
          </div>
        </div>

        <div className="topbar-right" ref={menuRef}>
          <span className="brand-name">{t.app.title} · {t.app.subtitle}</span>
          <button
            className="icon-btn"
            aria-label="Сменить тему"
            onClick={toggle}
            title={mode === "light" ? "Dunkles Design" : "Helles Design"}
          >
            {mode === "light" ? "🌙" : "☀️"}
          </button>
          <button
            className="icon-btn"
            aria-label="Меню профиля"
            onClick={() => setMenuOpen((v) => !v)}
          >
            👤
          </button>
          <div className={`profile-menu ${menuOpen ? "open" : ""}`}>
            <button className="menu-item" onClick={() => navigate("/profile")}>
              <span>👤 {t.nav.profile}</span>
              <span className="muted">{t.shell.account}</span>
            </button>
            <div className="menu-divider" />
            <button className="menu-item" onClick={onLogout}>
              <span>🚪 {t.app.logout}</span>
              <span className="muted">{t.shell.logoutNote}</span>
            </button>
          </div>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          {sections.map((section) => (
            <div key={section.title} className="sidebar-section">
              <div className="sidebar-title">{section.title}</div>
              <div className="nav-list">
                {section.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) =>
                      isActive ? "nav-link active" : "nav-link"
                    }
                  >
                    <span className="nav-left">
                      <span aria-hidden="true">{item.icon}</span>
                      <span>{item.label}</span>
                    </span>
                    {item.note && <span className="muted">{item.note}</span>}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </aside>

        <main className="content">{children}</main>
      </div>
    </div>
  );
}