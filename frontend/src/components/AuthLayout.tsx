import type { ReactNode } from "react";
import { t } from "../i18n/ru";

export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="brand-mark" aria-hidden="true">
            D
          </div>
          <div>
            <div className="brand-name" style={{ margin: 0 }}>
              {t.app.title}
            </div>
            <div className="muted" style={{ fontSize: "var(--text-xs)" }}>
              {t.app.subtitle}
            </div>
          </div>
        </div>
        <h1 className="auth-title">{title}</h1>
        {subtitle && <p className="auth-subtitle">{subtitle}</p>}
        {children}
      </div>
    </div>
  );
}