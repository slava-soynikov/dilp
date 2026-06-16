import { useCallback, useEffect, useState } from "react";
import {
  Body1,
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  Spinner,
  Title2,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { PinDisplayDialog } from "../components/PinDisplayDialog";
import { childrenApi, type Child } from "../api/children";
import { consentsApi, type Consent } from "../api/consents";
import { ApiError } from "../api/client";
import { t } from "../i18n/ru";

const useStyles = makeStyles({
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
  },
  table: {
    width: "100%",
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    borderCollapse: "collapse",
    overflow: "hidden",
  },
  th: {
    textAlign: "left",
    ...shorthands.padding("12px", "16px"),
    backgroundColor: tokens.colorNeutralBackground2,
    fontWeight: 600,
    fontSize: "13px",
  },
  td: {
    ...shorthands.padding("12px", "16px"),
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
    fontSize: "14px",
  },
  statusPending: { color: "#a06a00", fontWeight: 600 },
  statusActive: { color: "#0a7d28", fontWeight: 600 },
  actionsCell: { display: "flex", gap: "8px", flexWrap: "wrap" },
});

const USERNAME_RE = /^[a-z0-9._-]{3,32}$/;

/** Find active data_processing consent for a child, if any. */
function activeConsentFor(child: Child, consents: Consent[]): Consent | undefined {
  return consents.find(
    (c) =>
      c.child_id === child.id &&
      c.consent_type === "data_processing" &&
      c.revoked_at === null
  );
}

export default function ChildrenPage() {
  const s = useStyles();
  const [children, setChildren] = useState<Child[] | null>(null);
  const [consents, setConsents] = useState<Consent[]>([]);
  const [err, setErr] = useState<string>();
  const [openCreate, setOpenCreate] = useState(false);
  const [pinDialog, setPinDialog] = useState<{ username: string; pin: string } | null>(null);
  const [editChild, setEditChild] = useState<Child | null>(null);
  const [consentAction, setConsentAction] = useState<
    | { kind: "grant"; child: Child }
    | { kind: "revoke"; child: Child; consent: Consent }
    | null
  >(null);

  const load = useCallback(async () => {
    setErr(undefined);
    try {
      const [list, cs] = await Promise.all([
        childrenApi.list(),
        consentsApi.list(),
      ]);
      setChildren(list);
      setConsents(cs);
    } catch {
      setErr(t.common.networkError);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <AppShell>
      <div className={s.header}>
        <Title2>{t.children.title}</Title2>
        <Button appearance="primary" onClick={() => setOpenCreate(true)}>
          {t.children.addButton}
        </Button>
      </div>

      {err && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}

      {children === null ? (
        <Spinner label={t.common.loading} />
      ) : children.length === 0 ? (
        <Body1>{t.children.empty}</Body1>
      ) : (
        <table className={s.table}>
          <thead>
            <tr>
              <th className={s.th}>{t.children.table.username}</th>
              <th className={s.th}>{t.children.table.name}</th>
              <th className={s.th}>{t.children.table.status}</th>
              <th className={s.th}>{t.children.table.consent}</th>
              <th className={s.th}>{t.children.table.actions}</th>
            </tr>
          </thead>
          <tbody>
            {children.map((c) => {
              const isActive = c.status === "active";
              const consent = activeConsentFor(c, consents);
              return (
                <tr key={c.id}>
                  <td className={s.td} style={{ fontFamily: "monospace" }}>
                    {c.username || t.common.none}
                  </td>
                  <td className={s.td}>
                    {c.first_name} {c.last_name}
                  </td>
                  <td className={s.td}>
                    <span className={isActive ? s.statusActive : s.statusPending}>
                      {(t.status as Record<string, string>)[c.status || ""] ||
                        t.common.unknown}
                    </span>
                  </td>
                  <td className={s.td}>
                    {consent ? t.children.consent.granted : t.children.consent.notGranted}
                  </td>
                  <td className={`${s.td} ${s.actionsCell}`}>
                    <Button size="small" onClick={() => setEditChild(c)}>
                      {t.common.edit}
                    </Button>
                    {consent ? (
                      <Button
                        size="small"
                        onClick={() =>
                          setConsentAction({ kind: "revoke", child: c, consent })
                        }
                      >
                        {t.children.consent.revoke}
                      </Button>
                    ) : (
                      <Button
                        size="small"
                        appearance="primary"
                        onClick={() => setConsentAction({ kind: "grant", child: c })}
                      >
                        {t.children.consent.grant}
                      </Button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <CreateChildDialog
        open={openCreate}
        onClose={() => setOpenCreate(false)}
        onCreated={(resp) => {
          setOpenCreate(false);
          setPinDialog({ username: resp.username || "", pin: resp.pin });
          load();
        }}
      />

      {pinDialog && (
        <PinDisplayDialog
          open
          username={pinDialog.username}
          pin={pinDialog.pin}
          onClose={() => setPinDialog(null)}
        />
      )}

      {editChild && (
        <EditChildDialog
          child={editChild}
          onClose={() => setEditChild(null)}
          onSaved={() => {
            setEditChild(null);
            load();
          }}
        />
      )}

      {consentAction && (
        <ConsentActionDialog
          action={consentAction}
          onDone={() => {
            setConsentAction(null);
            load();
          }}
        />
      )}
    </AppShell>
  );
}

function CreateChildDialog({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (c: { username: string | null; pin: string }) => void;
}) {
  const [username, setUsername] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  const [lang, setLang] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string>();
  const [unameErr, setUnameErr] = useState<string>();

  function reset() {
    setUsername("");
    setFirstName("");
    setLastName("");
    setDob("");
    setLang("");
    setUnameErr(undefined);
    setErr(undefined);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(undefined);
    if (!USERNAME_RE.test(username)) {
      setUnameErr(t.children.create.usernameInvalid);
      return;
    }
    setUnameErr(undefined);
    setBusy(true);
    try {
      const resp = await childrenApi.create({
        username,
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dob || undefined,
        native_language: lang || undefined,
      });
      reset();
      onCreated({ username: resp.username, pin: resp.pin });
    } catch (e) {
      if (e instanceof ApiError && e.status === 409)
        setErr(t.children.create.usernameTaken);
      else if (e instanceof ApiError && e.status === 422)
        setUnameErr(t.children.create.usernameInvalid);
      else if (e instanceof ApiError && e.detail)
        setErr(e.detail);
      else if (e instanceof ApiError)
        setErr(`${t.common.networkError} (HTTP ${e.status})`);
      else setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(_, d) => !d.open && onClose()}>
      <DialogSurface>
        <form onSubmit={submit}>
          <DialogBody>
            <DialogTitle>{t.children.create.title}</DialogTitle>
            <DialogContent>
              {err && (
                <MessageBar intent="error" style={{ marginBottom: 12 }}>
                  <MessageBarBody>{err}</MessageBarBody>
                </MessageBar>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <Field
                  label={t.children.create.username}
                  required
                  hint={t.children.create.usernameHelp}
                  validationState={unameErr ? "error" : undefined}
                  validationMessage={unameErr}
                >
                  <Input
                    value={username}
                    onChange={(_, d) => setUsername(d.value)}
                    autoComplete="off"
                  />
                </Field>
                <Field label={t.children.create.firstName} required>
                  <Input value={firstName} onChange={(_, d) => setFirstName(d.value)} />
                </Field>
                <Field label={t.children.create.lastName} required>
                  <Input value={lastName} onChange={(_, d) => setLastName(d.value)} />
                </Field>
                <Field label={t.children.create.dateOfBirth}>
                  <Input type="date" value={dob} onChange={(_, d) => setDob(d.value)} />
                </Field>
                <Field label={t.children.create.nativeLanguage}>
                  <Input
                    value={lang}
                    onChange={(_, d) => setLang(d.value)}
                    placeholder="z. B. uk, ru, ar"
                  />
                </Field>
              </div>
            </DialogContent>
            <DialogActions>
              <Button
                type="button"
                onClick={() => {
                  reset();
                  onClose();
                }}
                disabled={busy}
              >
                {t.common.cancel}
              </Button>
              <Button appearance="primary" type="submit" disabled={busy}>
                {busy ? t.common.loading : t.children.create.submit}
              </Button>
            </DialogActions>
          </DialogBody>
        </form>
      </DialogSurface>
    </Dialog>
  );
}

function EditChildDialog({
  child,
  onClose,
  onSaved,
}: {
  child: Child;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [firstName, setFirstName] = useState(child.first_name);
  const [lastName, setLastName] = useState(child.last_name);
  const [dob, setDob] = useState(child.date_of_birth || "");
  const [lang, setLang] = useState(child.native_language || "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string>();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(undefined);
    try {
      await childrenApi.patch(child.id, {
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dob || undefined,
        native_language: lang || undefined,
      });
      onSaved();
    } catch {
      setErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(_, d) => !d.open && onClose()}>
      <DialogSurface>
        <form onSubmit={submit}>
          <DialogBody>
            <DialogTitle>{t.children.edit.title}</DialogTitle>
            <DialogContent>
              {err && (
                <MessageBar intent="error" style={{ marginBottom: 12 }}>
                  <MessageBarBody>{err}</MessageBarBody>
                </MessageBar>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <Field label={t.children.create.firstName}>
                  <Input value={firstName} onChange={(_, d) => setFirstName(d.value)} />
                </Field>
                <Field label={t.children.create.lastName}>
                  <Input value={lastName} onChange={(_, d) => setLastName(d.value)} />
                </Field>
                <Field label={t.children.create.dateOfBirth}>
                  <Input type="date" value={dob} onChange={(_, d) => setDob(d.value)} />
                </Field>
                <Field label={t.children.create.nativeLanguage}>
                  <Input value={lang} onChange={(_, d) => setLang(d.value)} />
                </Field>
              </div>
            </DialogContent>
            <DialogActions>
              <Button type="button" onClick={onClose} disabled={busy}>
                {t.common.cancel}
              </Button>
              <Button appearance="primary" type="submit" disabled={busy}>
                {busy ? t.common.loading : t.common.save}
              </Button>
            </DialogActions>
          </DialogBody>
        </form>
      </DialogSurface>
    </Dialog>
  );
}

function ConsentActionDialog({
  action,
  onDone,
}: {
  action:
    | { kind: "grant"; child: Child }
    | { kind: "revoke"; child: Child; consent: Consent };
  onDone: () => void;
}) {
  const [busy, setBusy] = useState(false);

  async function confirm() {
    setBusy(true);
    try {
      if (action.kind === "grant") {
        await consentsApi.grant(action.child.id);
      } else {
        await consentsApi.revoke(action.consent.id);
      }
    } catch {
      // surfaced via reload in onDone
    } finally {
      setBusy(false);
      onDone();
    }
  }

  const grant = action.kind === "grant";
  return (
    <ConfirmDialog
      open
      title={grant ? t.children.consent.grantConfirmTitle : t.children.consent.revokeConfirmTitle}
      body={grant ? t.children.consent.grantConfirmBody : t.children.consent.revokeConfirmBody}
      confirmLabel={grant ? t.children.consent.grant : t.children.consent.revoke}
      destructive={!grant}
      busy={busy}
      onConfirm={confirm}
      onCancel={onDone}
    />
  );
}
