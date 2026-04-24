// Canonical MITRE ATT&CK Enterprise tactics (kill-chain order).
// Used to render the heatmap even for tactics with zero alerts.
export const MITRE_TACTICS: readonly string[] = [
  "Reconnaissance",
  "Resource Development",
  "Initial Access",
  "Execution",
  "Persistence",
  "Privilege Escalation",
  "Defense Evasion",
  "Credential Access",
  "Discovery",
  "Lateral Movement",
  "Collection",
  "Command and Control",
  "Exfiltration",
  "Impact",
];

// Technique ID → human-readable name. Not exhaustive — covers techniques we
// actually expect to see from Wazuh rules + Cowrie-derived alerts.
// MITRE has 200+ techniques; adding more as they show up in data is cheap.
export const TECHNIQUE_NAMES: Record<string, string> = {
  T1046: "Network Service Discovery",
  T1078: "Valid Accounts",
  T1082: "System Information Discovery",
  T1098: "Account Manipulation",
  T1110: "Brute Force",
  "T1110.001": "Password Guessing",
  "T1110.002": "Password Cracking",
  "T1110.003": "Password Spraying",
  "T1110.004": "Credential Stuffing",
  T1190: "Exploit Public-Facing Application",
  T1505: "Server Software Component",
  T1518: "Software Discovery",
  T1537: "Transfer Data to Cloud Account",
  T1543: "Create or Modify System Process",
  T1546: "Event Triggered Execution",
  T1548: "Abuse Elevation Control Mechanism",
  T1562: "Impair Defenses",
  T1566: "Phishing",
  T1571: "Non-Standard Port",
  T1595: "Active Scanning",
  T1610: "Deploy Container",
};

export function techniqueName(id: string): string {
  return TECHNIQUE_NAMES[id] ?? id;
}

// Color scale for heatmap cells — cold grey → hot red.
// Bands chosen so even 1-alert cells pop against zero-count tactics.
export function heatColor(count: number, max: number): string {
  if (count === 0) return "bg-muted/30 text-muted-foreground";
  const ratio = max > 0 ? count / max : 0;
  if (ratio > 0.66) return "bg-red-500/80 text-white";
  if (ratio > 0.33) return "bg-orange-500/70 text-white";
  if (ratio > 0.1) return "bg-yellow-500/60 text-foreground";
  return "bg-primary/30 text-foreground";
}
