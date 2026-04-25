"use client";

import { useEffect, useState } from "react";
import { Moon, Sun, Monitor } from "lucide-react";

type Theme = "light" | "dark" | "system";
const KEY = "sf.theme";

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const effective = theme === "system" ? (prefersDark ? "dark" : "light") : theme;
  root.classList.toggle("dark", effective === "dark");
  root.dataset.theme = effective;
}

// Lazy initialiser — runs once on mount, in the browser only. Avoids the
// React-19 set-state-in-effect lint rule that fires on the obvious
// useEffect+setState pattern. SSR returns the same default ("dark") that
// the inline boot script in layout.tsx applies, so hydration matches.
function readStoredTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  return (localStorage.getItem(KEY) as Theme | null) ?? "dark";
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(readStoredTheme);

  useEffect(() => {
    // If the user's choice is "system", follow OS changes live. This effect
    // only subscribes — onChange mutates the DOM via applyTheme, not React
    // state, so it's free of the set-state-in-effect rule.
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      if ((localStorage.getItem(KEY) as Theme | null) === "system") applyTheme("system");
    };
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  function pick(next: Theme) {
    setTheme(next);
    localStorage.setItem(KEY, next);
    applyTheme(next);
  }

  return (
    <div
      role="radiogroup"
      aria-label="Theme"
      className="inline-flex rounded-md border border-border bg-background/40 p-0.5"
    >
      <Btn label="Light"  active={theme === "light"}  onClick={() => pick("light")}  icon={<Sun className="h-3 w-3" />} />
      <Btn label="System" active={theme === "system"} onClick={() => pick("system")} icon={<Monitor className="h-3 w-3" />} />
      <Btn label="Dark"   active={theme === "dark"}   onClick={() => pick("dark")}   icon={<Moon className="h-3 w-3" />} />
    </div>
  );
}

function Btn({
  label,
  active,
  onClick,
  icon,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={active}
      title={label}
      onClick={onClick}
      className={`inline-flex items-center justify-center rounded px-1.5 py-1 text-[11px] transition-colors ${
        active
          ? "bg-primary/15 text-primary"
          : "text-muted-foreground hover:text-foreground hover:bg-accent"
      }`}
    >
      {icon}
    </button>
  );
}
