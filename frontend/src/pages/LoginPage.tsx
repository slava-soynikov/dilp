import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Button,
  MessageBar,
  MessageBarBody,
} from "@fluentui/react-components";
import { AuthLayout } from "../components/AuthLayout";
import { FormField } from "../components/FormField";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";
import { isEmail } from "../lib/validate";
import { t } from "../i18n/ru";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: { pathname: string } } };
  const redirectTo = location.state?.from?.pathname || "/";

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [identifierErr, setIdentifierErr] = useState<string>();
  const [passwordErr, setPasswordErr] = useState<string>();
  const [formError, setFormError] = useState<string>();
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(undefined);
    let ok = true;
    const looksLikeEmail = identifier.includes("@");
    if (looksLikeEmail && !isEmail(identifier)) {
      setIdentifierErr(t.common.invalidEmail);
      ok = false;
    } else if (!identifier.trim()) {
      setIdentifierErr(t.common.required);
      ok = false;
    } else setIdentifierErr(undefined);
    if (!password) {
      setPasswordErr(t.common.required);
      ok = false;
    } else setPasswordErr(undefined);
    if (!ok) return;

    setBusy(true);
    try {
      await login(identifier, password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setFormError(translateLoginError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout title={t.login.title}>
      <form onSubmit={onSubmit} noValidate>
        {formError && (
          <MessageBar intent="error" style={{ marginBottom: 12 }}>
            <MessageBarBody>{formError}</MessageBarBody>
          </MessageBar>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <FormField
            label={t.login.identifierLabel}
            value={identifier}
            onChange={setIdentifier}
            type="text"
            autoComplete="username"
            required
            error={identifierErr}
          />
          <FormField
            label={t.common.password}
            value={password}
            onChange={setPassword}
            type="password"
            autoComplete="current-password"
            required
            error={passwordErr}
          />
          <Button appearance="primary" type="submit" disabled={busy}>
            {busy ? t.common.loading : t.login.submit}
          </Button>
        </div>
      </form>
      <div className="auth-footer">
        <span>
          {t.login.noAccount} <Link to="/register">{t.login.register}</Link>
        </span>
        <span className="hint">{t.login.forgotHint}</span>
      </div>
    </AuthLayout>
  );
}

function translateLoginError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 401) return t.login.invalidCredentials;
    if (err.status === 403) {
      if (err.detail?.includes("verified")) return t.login.emailNotVerified;
      if (err.detail?.includes("disabled")) return t.login.accountDisabled;
      if (err.detail?.includes("consent")) return t.login.consentRequired;
    }
    if (err.status === 429) return t.common.tooManyRequests;
    if (err.status === 0) return t.common.networkError;
  }
  return t.common.networkError;
}