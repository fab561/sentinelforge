import { Badge } from "@/components/ui/badge";
import type { Severity } from "@/lib/types";
import { cn } from "@/lib/utils";

const styles: Record<Severity, string> = {
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
  high:     "bg-orange-500/15 text-orange-400 border-orange-500/30",
  medium:   "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  low:      "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
};

export function SeverityBadge({ severity }: { severity: string }) {
  const s = (severity?.toLowerCase() ?? "low") as Severity;
  return (
    <Badge
      variant="outline"
      className={cn("uppercase text-[10px] font-semibold tracking-wider", styles[s] ?? styles.low)}
    >
      {s}
    </Badge>
  );
}
