import { useNavigate } from "react-router-dom";
import { Button, Spinner } from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { useAuth } from "../auth/AuthContext";
import { t } from "../i18n/ru";

type Card = {
  icon: string;
  title: string;
  body: string;
  cta: string;
  to: string;
  primary?: boolean;
};

export default function DashboardPage() {
  const { me, loadingMe, hasRole } = useAuth();
  const navigate = useNavigate();

  if (loadingMe || !me) {
    return (
      <AppShell>
        <Spinner label={t.common.loading} />
      </AppShell>
    );
  }

  const intro = hasRole("parent")
    ? t.dashboard.parentIntro
    : hasRole("teacher")
    ? t.dashboard.teacherIntro
    : hasRole("admin")
    ? t.dashboard.adminIntro
    : hasRole("auditor")
    ? t.dashboard.auditorIntro
    : t.dashboard.childIntro;

  const cards: Card[] = [];
  if (hasRole("child")) {
    cards.push({
      icon: "📚",
      title: t.nav.curriculum,
      body: t.curriculum.intro,
      cta: t.curriculum.title,
      to: "/curriculum",
      primary: true,
    });
  }
  if (hasRole("parent")) {
    cards.push({
      icon: "👨‍👩‍👧",
      title: t.nav.children,
      body: t.dashboard.parentIntro,
      cta: t.dashboard.goToChildren,
      to: "/children",
      primary: true,
    });
  }
  cards.push({
    icon: "👤",
    title: t.nav.profile,
    body: t.profile.gdprIntro,
    cta: t.dashboard.goToProfile,
    to: "/profile",
  });
  if (hasRole("admin") || hasRole("teacher")) {
    cards.push({
      icon: "📖",
      title: t.nav.programmes,
      body: t.programmes.title,
      cta: t.programmes.title,
      to: "/programmes",
    });
  }
  if (hasRole("admin")) {
    cards.push({
      icon: "🛠️",
      title: t.nav.admin,
      body: t.dashboard.adminIntro,
      cta: t.admin.title,
      to: "/admin",
    });
  }
  if (hasRole("admin") || hasRole("auditor")) {
    cards.push({
      icon: "🗂️",
      title: t.nav.logs,
      body: t.dashboard.auditorIntro,
      cta: t.nav.logs,
      to: "/logs",
    });
  }

  return (
    <AppShell>
      <div className="page-head">
        <div>
          <h1 className="page-title">
            {t.dashboard.title}, {me.username || me.email}
          </h1>
          <p className="page-subtitle">{intro}</p>
        </div>
      </div>

      <div className="section">
        <div className="section-head">
          <div>
            <div className="section-title">⚡ {t.dashboard.quickActions}</div>
            <div className="section-desc">{t.dashboard.quickHint}</div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "var(--space-4)",
          }}
        >
          {cards.map((c) => (
            <div key={c.to} className="card card-padded">
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-2)",
                  marginBottom: "var(--space-2)",
                  fontWeight: 600,
                  fontSize: "var(--text-base)",
                }}
              >
                <span aria-hidden="true">{c.icon}</span>
                <span>{c.title}</span>
              </div>
              <p
                className="muted"
                style={{ fontSize: "var(--text-sm)", marginBottom: "var(--space-4)" }}
              >
                {c.body}
              </p>
              <Button
                appearance={c.primary ? "primary" : "secondary"}
                onClick={() => navigate(c.to)}
              >
                {c.cta}
              </Button>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
