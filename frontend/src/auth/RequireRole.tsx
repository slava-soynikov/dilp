import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { Spinner } from "@fluentui/react-components";
import { useAuth } from "./AuthContext";
import { t } from "../i18n/ru";

export function RequireRole({
  role,
  anyOf,
  children,
}: {
  role?: string;
  anyOf?: string[];
  children: ReactNode;
}) {
  const { me, loadingMe, hasRole } = useAuth();
  if (loadingMe || !me) {
    return <Spinner label={t.common.loading} />;
  }
  const allowed =
    (role !== undefined && hasRole(role)) ||
    (anyOf !== undefined && anyOf.some((r) => hasRole(r)));
  if (!allowed) return <Navigate to="/" replace />;
  return <>{children}</>;
}