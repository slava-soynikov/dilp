import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Body1,
  Button,
  Dialog,
  DialogActions,
  DialogBody,
  DialogContent,
  DialogSurface,
  DialogTitle,
  Dropdown,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  Option,
  Spinner,
  Title2,
  Title3,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { AppShell } from "../components/AppShell";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { tenantsApi, schoolsApi, type School, type Tenant } from "../api/tenants";
import { t } from "../i18n/ru";

const useStyles = makeStyles({
  section: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding("24px"),
    marginBottom: "16px",
  },
  sectionHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "12px",
  },
  list: { display: "flex", flexDirection: "column", rowGap: "8px" },
  row: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.padding("8px", "12px"),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
  },
  rowMeta: { color: tokens.colorNeutralForeground2, fontSize: "12px" },
});

export default function OrganizationPage() {
  const s = useStyles();
  const [tenants, setTenants] = useState<Tenant[] | null>(null);
  const [schools, setSchools] = useState<School[] | null>(null);
  const [err, setErr] = useState<string>();

  const [openCreateT, setOpenCreateT] = useState(false);
  const [openCreateS, setOpenCreateS] = useState(false);
  const [deleteT, setDeleteT] = useState<Tenant | null>(null);
  const [deleteS, setDeleteS] = useState<School | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setErr(undefined);
    try {
      const [ts, ss] = await Promise.all([tenantsApi.list(), schoolsApi.list()]);
      setTenants(ts);
      setSchools(ss);
    } catch {
      setErr(t.common.networkError);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const tenantsById = useMemo(
    () => Object.fromEntries((tenants || []).map((x) => [x.id, x])),
    [tenants]
  );

  return (
    <AppShell>
      <Title2 style={{ marginBottom: 16 }}>{t.org.title}</Title2>
      {err && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}

      <div className={s.section}>
        <div className={s.sectionHeader}>
          <Title3>{t.org.tenantsTitle}</Title3>
          <Button appearance="primary" onClick={() => setOpenCreateT(true)}>
            {t.org.addTenant}
          </Button>
        </div>
        {tenants === null ? (
          <Spinner label={t.common.loading} />
        ) : tenants.length === 0 ? (
          <Body1>{t.org.empty}</Body1>
        ) : (
          <div className={s.list}>
            {tenants.map((tn) => (
              <div key={tn.id} className={s.row}>
                <div>
                  <div>{tn.name}</div>
                  <div className={s.rowMeta}>{tn.id}</div>
                </div>
                <Button onClick={() => setDeleteT(tn)}>{t.org.delete}</Button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className={s.section}>
        <div className={s.sectionHeader}>
          <Title3>{t.org.schoolsTitle}</Title3>
          <Button
            appearance="primary"
            onClick={() => setOpenCreateS(true)}
            disabled={(tenants || []).length === 0}
          >
            {t.org.addSchool}
          </Button>
        </div>
        {schools === null ? (
          <Spinner label={t.common.loading} />
        ) : schools.length === 0 ? (
          <Body1>{t.org.empty}</Body1>
        ) : (
          <div className={s.list}>
            {schools.map((sch) => (
              <div key={sch.id} className={s.row}>
                <div>
                  <div>{sch.name}</div>
                  <div className={s.rowMeta}>
                    {tenantsById[sch.tenant_id]?.name || t.org.notInTenant} ·{" "}
                    {sch.id}
                  </div>
                </div>
                <Button onClick={() => setDeleteS(sch)}>{t.org.delete}</Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {openCreateT && (
        <CreateTenantDialog
          onClose={() => setOpenCreateT(false)}
          onDone={() => {
            setOpenCreateT(false);
            load();
          }}
        />
      )}

      {openCreateS && tenants && (
        <CreateSchoolDialog
          tenants={tenants}
          onClose={() => setOpenCreateS(false)}
          onDone={() => {
            setOpenCreateS(false);
            load();
          }}
        />
      )}

      <ConfirmDialog
        open={deleteT !== null}
        title={t.org.confirmDeleteTenant}
        body={t.org.confirmDeleteTenantBody}
        destructive
        busy={busy}
        onConfirm={async () => {
          if (!deleteT) return;
          setBusy(true);
          try {
            await tenantsApi.remove(deleteT.id);
          } finally {
            setBusy(false);
            setDeleteT(null);
            load();
          }
        }}
        onCancel={() => setDeleteT(null)}
      />

      <ConfirmDialog
        open={deleteS !== null}
        title={t.org.confirmDeleteSchool}
        body={t.org.confirmDeleteSchoolBody}
        destructive
        busy={busy}
        onConfirm={async () => {
          if (!deleteS) return;
          setBusy(true);
          try {
            await schoolsApi.remove(deleteS.id);
          } finally {
            setBusy(false);
            setDeleteS(null);
            load();
          }
        }}
        onCancel={() => setDeleteS(null)}
      />
    </AppShell>
  );
}

function CreateTenantDialog({
  onClose,
  onDone,
}: {
  onClose: () => void;
  onDone: () => void;
}) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string>();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    try {
      await tenantsApi.create(name.trim());
      onDone();
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
            <DialogTitle>{t.org.addTenant}</DialogTitle>
            <DialogContent>
              {err && (
                <MessageBar intent="error" style={{ marginBottom: 12 }}>
                  <MessageBarBody>{err}</MessageBarBody>
                </MessageBar>
              )}
              <Field label={t.org.tenantName} required>
                <Input value={name} onChange={(_, d) => setName(d.value)} />
              </Field>
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

function CreateSchoolDialog({
  tenants,
  onClose,
  onDone,
}: {
  tenants: Tenant[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [tenantId, setTenantId] = useState(tenants[0]?.id || "");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string>();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!tenantId || !name.trim()) return;
    setBusy(true);
    try {
      await schoolsApi.create(tenantId, name.trim());
      onDone();
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
            <DialogTitle>{t.org.addSchool}</DialogTitle>
            <DialogContent>
              {err && (
                <MessageBar intent="error" style={{ marginBottom: 12 }}>
                  <MessageBarBody>{err}</MessageBarBody>
                </MessageBar>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <Field label={t.org.tenantSelect} required>
                  <Dropdown
                    value={tenants.find((x) => x.id === tenantId)?.name || ""}
                    selectedOptions={[tenantId]}
                    onOptionSelect={(_, d) => setTenantId(String(d.optionValue || ""))}
                  >
                    {tenants.map((tn) => (
                      <Option key={tn.id} value={tn.id} text={tn.name}>
                        {tn.name}
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
                <Field label={t.org.schoolName} required>
                  <Input value={name} onChange={(_, d) => setName(d.value)} />
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