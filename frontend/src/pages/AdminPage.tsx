import { useState } from "react";
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
  Title2,
  Title3,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { adminApi } from "../api/admin";
import { ApiError } from "../api/client";
import { isEmail } from "../lib/validate";
import { t } from "../i18n/ru";

const useStyles = makeStyles({
  section: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding("24px"),
    marginBottom: "16px",
    maxWidth: "520px",
  },
  pwdBox: {
    fontFamily: "monospace",
    fontSize: "16px",
    backgroundColor: tokens.colorNeutralBackground3,
    ...shorthands.padding("8px", "12px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    marginBottom: "12px",
    userSelect: "all",
    wordBreak: "break-all",
  },
});

type Reveal = { title: string; subject: string; password: string } | null;

export default function AdminPage() {
  const s = useStyles();
  const [reveal, setReveal] = useState<Reveal>(null);
  return (
    <AppShell>
      <Title2 style={{ marginBottom: 16 }}>{t.admin.title}</Title2>
      <InviteTeacherSection styles={s} onReveal={setReveal} />
      <ResetPasswordSection styles={s} onReveal={setReveal} />
      {reveal && (
        <PasswordRevealDialog
          title={reveal.title}
          subject={reveal.subject}
          password={reveal.password}
          onClose={() => setReveal(null)}
        />
      )}
    </AppShell>
  );
}

function InviteTeacherSection({
  styles,
  onReveal,
}: {
  styles: ReturnType<typeof useStyles>;
  onReveal: (r: { title: string; subject: string; password: string }) => void;
}) {
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [emailErr, setEmailErr] = useState<string>();
  const [nameErr, setNameErr] = useState<string>();
  const [formErr, setFormErr] = useState<string>();
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormErr(undefined);
    if (!isEmail(email)) {
      setEmailErr(t.common.invalidEmail);
      return;
    }
    setEmailErr(undefined);
    if (!firstName.trim() || !lastName.trim()) {
      setNameErr(t.common.required);
      return;
    }
    setNameErr(undefined);
    setBusy(true);
    try {
      const res = await adminApi.inviteTeacher(email, firstName.trim(), lastName.trim());
      onReveal({
        title: t.admin.tempPwd.title,
        subject: res.email || "",
        password: res.temp_password,
      });
      setEmail("");
      setFirstName("");
      setLastName("");
    } catch (e) {
      if (e instanceof ApiError && e.status === 409)
        setFormErr(t.admin.inviteTeacher.emailTaken);
      else if (e instanceof ApiError && e.status === 403)
        setFormErr(t.common.error);
      else setFormErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.section}>
      <Title3>{t.admin.inviteTeacher.title}</Title3>
      <Body1 style={{ marginBottom: 12 }}>{t.admin.inviteTeacher.intro}</Body1>
      {formErr && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{formErr}</MessageBarBody>
        </MessageBar>
      )}
      <form onSubmit={submit}>
        <Field
          label={t.admin.inviteTeacher.email}
          required
          validationState={emailErr ? "error" : undefined}
          validationMessage={emailErr}
        >
          <Input
            type="email"
            value={email}
            onChange={(_, d) => setEmail(d.value)}
            autoComplete="off"
          />
        </Field>
        <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
          <Field
            label={t.admin.inviteTeacher.firstName}
            required
            style={{ flex: 1 }}
            validationState={nameErr ? "error" : undefined}
            validationMessage={nameErr}
          >
            <Input
              value={firstName}
              onChange={(_, d) => setFirstName(d.value)}
              autoComplete="off"
            />
          </Field>
          <Field
            label={t.admin.inviteTeacher.lastName}
            required
            style={{ flex: 1 }}
          >
            <Input
              value={lastName}
              onChange={(_, d) => setLastName(d.value)}
              autoComplete="off"
            />
          </Field>
        </div>
        <Button
          appearance="primary"
          type="submit"
          disabled={busy}
          style={{ marginTop: 12 }}
        >
          {busy ? t.common.loading : t.admin.inviteTeacher.submit}
        </Button>
      </form>
    </div>
  );
}

function ResetPasswordSection({
  styles,
  onReveal,
}: {
  styles: ReturnType<typeof useStyles>;
  onReveal: (r: { title: string; subject: string; password: string }) => void;
}) {
  const [ident, setIdent] = useState("");
  const [identErr, setIdentErr] = useState<string>();
  const [formErr, setFormErr] = useState<string>();
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormErr(undefined);
    if (!ident.trim()) {
      setIdentErr(t.common.required);
      return;
    }
    setIdentErr(undefined);
    setBusy(true);
    try {
      const res = await adminApi.resetUserPassword(ident.trim());
      onReveal({
        title: t.admin.resetPwd.title,
        subject: res.email || res.username || "",
        password: res.new_password,
      });
      setIdent("");
    } catch (e) {
      if (e instanceof ApiError && e.status === 404)
        setFormErr(t.admin.resetPwd.notFound);
      else if (e instanceof ApiError && e.status === 403)
        setFormErr(t.common.error);
      else setFormErr(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.section}>
      <Title3>{t.admin.resetPwd.title}</Title3>
      <Body1 style={{ marginBottom: 12 }}>{t.admin.resetPwd.intro}</Body1>
      {formErr && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{formErr}</MessageBarBody>
        </MessageBar>
      )}
      <form onSubmit={submit}>
        <Field
          label={t.admin.resetPwd.identifier}
          required
          validationState={identErr ? "error" : undefined}
          validationMessage={identErr}
        >
          <Input
            type="text"
            value={ident}
            onChange={(_, d) => setIdent(d.value)}
            autoComplete="off"
          />
        </Field>
        <Button
          appearance="primary"
          type="submit"
          disabled={busy}
          style={{ marginTop: 12 }}
        >
          {busy ? t.common.loading : t.admin.resetPwd.submit}
        </Button>
      </form>
    </div>
  );
}

function PasswordRevealDialog({
  title,
  subject,
  password,
  onClose,
}: {
  title: string;
  subject: string;
  password: string;
  onClose: () => void;
}) {
  const s = useStyles();
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(password);
      setCopied(true);
    } catch {
      // ignore
    }
  }

  return (
    <Dialog open onOpenChange={(_, d) => !d.open && onClose()}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{title}</DialogTitle>
          <DialogContent>
            <Body1 style={{ marginBottom: 12 }}>{t.admin.tempPwd.intro}</Body1>
            {subject && (
              <Body1 style={{ marginBottom: 8 }}>
                <strong>{subject}</strong>
              </Body1>
            )}
            <div className={s.pwdBox}>{password}</div>
            <Button onClick={copy}>
              {copied ? t.admin.tempPwd.copied : t.admin.tempPwd.copy}
            </Button>
          </DialogContent>
          <DialogActions>
            <Button appearance="primary" onClick={onClose}>
              {t.admin.tempPwd.gotIt}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}