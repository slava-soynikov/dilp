import { useCallback, useEffect, useState } from "react";
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
import { curriculumApi, type Programme } from "../api/programmes";
import { t } from "../i18n/ru";

const useStyles = makeStyles({
  intro: { marginBottom: "16px" },
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow4,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.padding("16px"),
    marginBottom: "16px",
  },
  meta: { color: tokens.colorNeutralForeground2, fontSize: "12px" },
  moduleBlock: {
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.padding("12px"),
    marginTop: "8px",
  },
  lessonRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.padding("6px", "8px"),
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    backgroundColor: tokens.colorNeutralBackground1,
    marginTop: "6px",
  },
});

export default function CurriculumPage() {
  const s = useStyles();
  const navigate = useNavigate();
  const [programmes, setProgrammes] = useState<Programme[] | null>(null);
  const [err, setErr] = useState<string>();

  const load = useCallback(async () => {
    setErr(undefined);
    try {
      const c = await curriculumApi.me();
      setProgrammes(c.programmes);
    } catch {
      setErr(t.common.networkError);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <AppShell>
      <Title2>{t.curriculum.title}</Title2>
      <Body1 className={s.intro}>{t.curriculum.intro}</Body1>

      {err && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{err}</MessageBarBody>
        </MessageBar>
      )}

      {programmes === null ? (
        <Spinner label={t.common.loading} />
      ) : programmes.length === 0 ? (
        <Body1>{t.curriculum.empty}</Body1>
      ) : (
        programmes.map((p) => (
          <div key={p.id} className={s.card}>
            <Title3>{p.name}</Title3>
            <div className={s.meta}>
              {t.curriculum.language}: {p.language}
            </div>
            {p.modules
              .slice()
              .sort((a, b) => a.order_index - b.order_index)
              .map((m) => (
                <div key={m.id} className={s.moduleBlock}>
                  <div style={{ fontWeight: 600 }}>
                    #{m.order_index} · {m.title}
                  </div>
                  {m.lessons.length === 0 ? (
                    <Body1 style={{ marginTop: 6 }}>
                      {t.programmes.lessons.empty}
                    </Body1>
                  ) : (
                    m.lessons
                      .slice()
                      .sort((a, b) => a.order_index - b.order_index)
                      .map((l) => (
                        <div key={l.id} className={s.lessonRow}>
                          <div>
                            #{l.order_index} · {l.title}
                          </div>
                          <Button
                            appearance="primary"
                            onClick={() => navigate(`/lessons/${l.id}`)}
                          >
                            {t.curriculum.open}
                          </Button>
                        </div>
                      ))
                  )}
                </div>
              ))}
          </div>
        ))
      )}
    </AppShell>
  );
}
