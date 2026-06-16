import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Button,
  MessageBar,
  MessageBarBody,
} from "@fluentui/react-components";
import { AuthLayout } from "../components/AuthLayout";
import { FormField } from "../components/FormField";
import { authApi } from "../api/auth";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { isEmail, passwordPolicyOk } from "../lib/validate";
import { t } from "../i18n/ru";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordRepeat, setPasswordRepeat] = useState("");
  const [emailErr, setEmailErr] = useState<string>();
  const [passwordErr, setPasswordErr] = useState<string>();
  const [repeatErr, setRepeatErr] = useState<string>();
  const [formError, setFormError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(undefined);
    let ok = true;
    if (!isEmail(email)) {
      setEmailErr(t.common.invalidEmail);
      ok = false;
    } else setEmailErr(undefined);
    if (!passwordPolicyOk(password)) {
      setPasswordErr(t.common.passwordPolicy);
      ok = false;
    } else setPasswordErr(undefined);
    if (password !== passwordRepeat) {
      setRepeatErr(t.common.passwordsDontMatch);
      ok = false;
    } else setRepeatErr(undefined);
    if (!ok) return;

    setBusy(true);
    try {
      await authApi.register(email, password, "parent");
      // POC: parent is the only public-registration role and gets activated
      // immediately by AuthService. Log them in straight away and go to the
      // dashboard — no reason to make the user re-enter credentials.
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409)
        setFormError(t.register.emailTaken);
      else if (err instanceof ApiError && err.status === 422)
        setFormError(t.common.passwordPolicy);
      else if (err instanceof ApiError && err.status === 429)
        setFormError(t.common.tooManyRequests);
      else setFormError(t.common.networkError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout title={t.register.title}>
      <form onSubmit={onSubmit} noValidate>
        {formError && (
          <MessageBar intent="error" style={{ marginBottom: 12 }}>
            <MessageBarBody>{formError}</MessageBarBody>
          </MessageBar>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <FormField
            label={t.common.email}
            value={email}
            onChange={setEmail}
            type="email"
            autoComplete="email"
            required
            error={emailErr}
          />
          <FormField
            label={t.common.password}
            value={password}
            onChange={setPassword}
            type="password"
            autoComplete="new-password"
            required
            error={passwordErr}
          />
          <FormField
            label={t.common.passwordRepeat}
            value={passwordRepeat}
            onChange={setPasswordRepeat}
            type="password"
            autoComplete="new-password"
            required
            error={repeatErr}
          />
          <Button appearance="primary" type="submit" disabled={busy}>
            {busy ? t.common.loading : t.register.submit}
          </Button>
        </div>
      </form>
      <span>
        {t.register.haveAccount}{" "}
        <Link to="/login">{t.register.login}</Link>
      </span>
    </AuthLayout>
  );
}