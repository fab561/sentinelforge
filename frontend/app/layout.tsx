import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SentinelForge — SOC Dashboard",
  description: "SOC Automation Platform",
};

// Inline boot script — runs synchronously before paint so we never flash
// the wrong theme. Reads the user's saved preference (default: dark, the
// SOC look most analysts expect) and applies the .dark class up front.
const themeScript = `
  (function () {
    try {
      var t = localStorage.getItem('sf.theme') || 'dark';
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      var dark = t === 'dark' || (t === 'system' && prefersDark);
      document.documentElement.classList.toggle('dark', dark);
      document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    } catch (_) {
      document.documentElement.classList.add('dark');
    }
  })();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      // The inline themeScript flips classList + data-theme on <html> before
      // React hydrates so we don't FOUC. That guarantees a server/client mismatch
      // on those exact attributes — suppressHydrationWarning silences the
      // expected diff (it only suppresses on the <html> tag itself, not children).
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="flex h-full bg-background text-foreground">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
