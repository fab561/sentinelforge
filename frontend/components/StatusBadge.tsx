import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const styles: Record<string, string> = {
  // Alert status
  new:         "bg-blue-500/15 text-blue-400 border-blue-500/30",
  in_progress: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  resolved:    "bg-green-500/15 text-green-400 border-green-500/30",
  closed:      "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
  // Verdict
  malicious:   "bg-red-500/15 text-red-400 border-red-500/30",
  suspicious:  "bg-orange-500/15 text-orange-400 border-orange-500/30",
  benign:      "bg-green-500/15 text-green-400 border-green-500/30",
  pending:     "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
  // Case status
  open:        "bg-blue-500/15 text-blue-400 border-blue-500/30",
  // Wazuh agent
  active:      "bg-green-500/15 text-green-400 border-green-500/30",
  disconnected:"bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
};

export function StatusBadge({ status }: { status: string }) {
  const s = status?.toLowerCase() ?? "";
  return (
    <Badge
      variant="outline"
      className={cn(
        "capitalize text-[10px] font-medium tracking-wide",
        styles[s] ?? "bg-zinc-500/15 text-zinc-400 border-zinc-500/30"
      )}
    >
      {s.replace("_", " ")}
    </Badge>
  );
}
