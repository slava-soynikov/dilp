import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Body1,
  Button,
  MessageBar,
  MessageBarBody,
  Spinner,
  Title2,
  Title3,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { usersApi } from "../api/users";
import { useAuth } from "../auth/AuthContext";
import { t } from "../i18n/ru";

const useStyles = makeStyles({
  section: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding("24px"),
    marginBottom: "16px",
    display: "flex",
    flexDirection: "column",
    rowGap: "8px",
  },
  row: { display: "flex", gap: "12px", flexWrap: "wrap" },
  field: { display: "flex", gap: "8px" },
  label: { color: tokens.colorNeutralForeground2, minWidth: "140px" },
});

function statusLabel(s: string): string {
  return (t.status as Record<string, string>)[s] ?? s;
}

function roleLabel(r: string): string {
  return (t.roles as Record<string, string>)[r] ?? r;
}

export default function ProfilePage() {
  const s = useStyles();
  const { me, loadingMe, hasRole, logout } = useAuth();
  const navigate = useNavigate();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [info, setInfo] = useState<string>();

  if (loadingMe || !me) {
    return (
      <AppShell>
        <Spinner label={t.common.loading} />
      </AppShell>
    );
  }

  async function onExport() {
    setError(undefined);
    try {
      await usersApi.exportMe();
    } catch {
      setError(t.common.networkError);
    }
  }

  async function onDelete() {
    setBusy(true);
    setError(undefined);
    try {
      await usersApi.deleteMe();
      setInfo(t.profile.deleted);
      await logout();
      navigate("/login", { replace: true });
    } catch {
      setError(t.common.networkError);
    } finally {
      setBusy(false);
      setConfirmDelete(false);
    }
  }

  return (
    <AppShell>
      <Title2 style={{ marginBottom: 16 }}>{t.profile.title}</Title2>

      {error && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      )}
      {info && (
        <MessageBar intent="success" style={{ marginBottom: 12 }}>
          <MessageBarBody>{info}</MessageBarBody>
        </MessageBar>
      )}

      <div className={s.section}>
        <Title3>{t.profile.accountSection}</Title3>
        <div className={s.field}>
          <span className={s.label}>{t.common.email}:</span>
          <span>{me.email || t.common.none}</span>
        </div>
        <div className={s.field}>
          <span className={s.label}>{t.profile.id}:</span>
          <span style={{ fontFamily: "monospace", fontSize: 12 }}>{me.id}</span>
        </div>
        <div className={s.field}>
          <span className={s.label}>{t.profile.status}:</span>
          <span>{statusLabel(me.status)}</span>
        </div>
        <div className={s.field}>
          <span className={s.label}>{t.profile.roles}:</span>
          <span>{me.roles.map(roleLabel).join(", ")}</span>
        </div>
        <div className={s.field}>
          <span className={s.label}>{t.profile.createdAt}:</span>
          <span>{new Date(me.created_at).toLocaleString("ru-RU")}</span>
        </div>
      </div>

      <div className={s.section}>
        <Title3>{t.profile.gdprSection}</Title3>
        <Body1>{t.profile.gdprIntro}</Body1>
        <div className={s.row}>
          <Button onClick={onExport}>{t.profile.exportButton}</Button>
          <Button
            onClick={() => setConfirmDelete(true)}
            style={{ color: "#b00020" }}
          >
            {t.profile.deleteButton}
          </Button>
        </div>
      </div>

      <ConfirmDialog
        open={confirmDelete}
        title={t.profile.deleteConfirmTitle}
        body={
          hasRole("parent")
            ? t.profile.deleteConfirmBodyParent
            : t.profile.deleteConfirmBody
        }
        confirmLabel={t.common.delete}
        destructive
        busy={busy}
        onConfirm={onDelete}
        onCancel={() => setConfirmDelete(false)}
      />
    </AppShell>
  );
}