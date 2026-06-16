import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { FluentProvider } from "@fluentui/react-components";
import { warmDarkTheme, warmLightTheme } from "./fluentTheme";

type ThemeMode = "light" | "dark";

type Ctx = {
  mode: ThemeMode;
  toggle: () => void;
};

const ThemeCtx = createContext<Ctx | null>(null);
const STORAGE_KEY = "dilp.theme";

function detectInitial(): ThemeMode {
  if (typeof window === "undefined") return "light";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(detectInitial);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", mode);
    localStorage.setItem(STORAGE_KEY, mode);
  }, [mode]);

  const value = useMemo(
    () => ({ mode, toggle: () => setMode((m) => (m === "light" ? "dark" : "light")) }),
    [mode]
  );

  return (
    <ThemeCtx.Provider value={value}>
      <FluentProvider theme={mode === "light" ? warmLightTheme : warmDarkTheme}>
        {children}
      </FluentProvider>
    </ThemeCtx.Provider>
  );
}

export function useTheme(): Ctx {
  const v = useContext(ThemeCtx);
  if (!v) throw new Error("useTheme outside ThemeProvider");
  return v;
}
