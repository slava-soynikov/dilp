import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  MessageBar,
  MessageBarBody,
  Spinner,
} from "@fluentui/react-components";
import { AuthLayout } from "../components/AuthLayout";
import { authApi } from "../api/auth";
import { t } from "../i18n/ru";

type State = "loading" | "success" | "invalid" | "missing";

export default function VerifyEmailPage() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [state, setState] = useState<State>(token ? "loading" : "missing");

  useEffect(() => {
    if (!token) return;
    authApi
      .verifyEmail(token)
      .then(() => setState("success"))
      .catch(() => setState("invalid"));
  }, [token]);

  return (
    <AuthLayout title={t.verify.title}>
      {state === "loading" && <Spinner label={t.verify.pending} />}
      {state === "success" && (
        <>
          <MessageBar intent="success">
            <MessageBarBody>{t.verify.success}</MessageBarBody>
          </MessageBar>
          <Link to="/login">{t.verify.toLogin}</Link>
        </>
      )}
      {state === "invalid" && (
        <>
          <MessageBar intent="error">
            <MessageBarBody>{t.verify.invalid}</MessageBarBody>
          </MessageBar>
          <Link to="/login">{t.verify.toLogin}</Link>
        </>
      )}
      {state === "missing" && (
        <MessageBar intent="warning">
          <MessageBarBody>{t.verify.missing}</MessageBarBody>
        </MessageBar>
      )}
    </AuthLayout>
  );
}