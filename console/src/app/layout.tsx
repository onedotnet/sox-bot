import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "sox.bot",
  description: "AI-powered community operations",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-zinc-950 text-zinc-100 flex min-h-screen">
        <aside className="w-56 bg-zinc-900 border-r border-zinc-800 p-4">
          <h2 className="text-lg font-bold text-green-400 mb-6">sox.bot</h2>
          <nav className="space-y-2">
            <Link href="/dashboard" className="block px-3 py-2 rounded hover:bg-zinc-800 text-zinc-300">
              Dashboard
            </Link>
            <Link href="/scout" className="block px-3 py-2 rounded hover:bg-zinc-800 text-zinc-300">
              ScoutBot
            </Link>
            <Link href="/content" className="block px-3 py-2 rounded hover:bg-zinc-800 text-zinc-300">
              Content
            </Link>
            <Link href="/community" className="block px-3 py-2 rounded hover:bg-zinc-800 text-zinc-300">
              Community
            </Link>
          </nav>
        </aside>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
