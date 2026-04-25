"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  AlertTriangle,
  FolderOpen,
  Shield,
  Cpu,
  Crosshair,
  ScrollText,
  ShieldAlert,
  Workflow,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard",  label: "Dashboard", icon: LayoutDashboard },
  { href: "/alerts",     label: "Alerts",    icon: AlertTriangle },
  { href: "/cases",      label: "Cases",     icon: FolderOpen },
  { href: "/rules",      label: "Rules",     icon: Shield },
  { href: "/playbooks",  label: "Playbooks", icon: Workflow },
  { href: "/mitre",      label: "MITRE",     icon: Crosshair },
  { href: "/agents",     label: "Agents",    icon: Cpu },
  { href: "/audit",      label: "Audit Log", icon: ScrollText },
];

export function Sidebar() {
  const path = usePathname();

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-border bg-sidebar">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 border-b border-border px-4">
        <ShieldAlert className="h-5 w-5 text-primary" />
        <span className="text-sm font-semibold tracking-wide text-foreground">
          SentinelForge
        </span>
      </div>

      {/* Nav links */}
      <nav className="flex flex-1 flex-col gap-0.5 p-2 pt-3">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = path === href || path.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-primary/15 text-primary font-medium"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-3 text-xs text-muted-foreground">
        Module 4 — SOC Dashboard
      </div>
    </aside>
  );
}
