"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import "./globals.css";

const NAV_ITEMS = [
  {
    href: "/dashboard",
    label: "Command Center",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
    color: "text-zinc-400",
    activeColor: "text-white",
  },
  {
    href: "/scout",
    label: "ScoutBot",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
        <line x1="8" y1="11" x2="14" y2="11" />
        <line x1="11" y1="8" x2="11" y2="14" />
      </svg>
    ),
    color: "text-amber-500/70",
    activeColor: "text-amber-400",
    dotColor: "bg-amber-400",
  },
  {
    href: "/content",
    label: "ContentBot",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 20h9" />
        <path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838.838-2.872a2 2 0 0 1 .506-.855z" />
      </svg>
    ),
    color: "text-blue-500/70",
    activeColor: "text-blue-400",
    dotColor: "bg-blue-400",
  },
  {
    href: "/community",
    label: "CommunityBot",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
    color: "text-emerald-500/70",
    activeColor: "text-emerald-400",
    dotColor: "bg-emerald-400",
  },
  {
    href: "/analytics",
    label: "Analytics",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 3v18h18" />
        <path d="M18 17V9" />
        <path d="M13 17V5" />
        <path d="M8 17v-3" />
      </svg>
    ),
    color: "text-purple-500/70",
    activeColor: "text-purple-400",
    dotColor: "bg-purple-400",
  },
];

function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-[220px] flex flex-col bg-[#0a0a0c] border-r border-white/[0.06] relative overflow-hidden">
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />

      {/* Logo */}
      <div className="relative px-5 pt-6 pb-5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <span className="text-sm font-bold text-white font-mono">S</span>
          </div>
          <div>
            <h1 className="text-[15px] font-semibold tracking-tight text-white">sox.bot</h1>
            <p className="text-[10px] text-zinc-500 font-medium tracking-wider uppercase">Mission Control</p>
          </div>
        </div>
      </div>

      {/* Status indicator */}
      <div className="relative mx-4 mb-5 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.05]">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-dot" />
          <span className="text-[11px] text-zinc-400 font-medium">4 bots operational</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="relative flex-1 px-3 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                group flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium
                transition-all duration-150 relative
                ${isActive
                  ? `bg-white/[0.06] ${item.activeColor} shadow-sm`
                  : `text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.03]`
                }
              `}
            >
              {isActive && (
                <div
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[60%] rounded-r-full"
                  style={{ backgroundColor: item.dotColor ? item.dotColor.replace('bg-', '') : '#fff' }}
                />
              )}
              <span className={`transition-colors ${isActive ? item.activeColor : item.color}`}>
                {item.icon}
              </span>
              <span>{item.label}</span>
              {item.dotColor && isActive && (
                <div className={`ml-auto w-1.5 h-1.5 rounded-full ${item.dotColor}`} />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="relative p-4 mt-auto">
        <div className="px-3 py-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
          <p className="text-[10px] text-zinc-600 font-medium uppercase tracking-wider mb-1">Powered by</p>
          <p className="text-[12px] text-zinc-400 font-medium">SoxAI Gateway</p>
          <p className="text-[10px] text-zinc-600 mt-0.5">Multi-model AI engine</p>
        </div>
      </div>
    </aside>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 bg-grid overflow-auto">{children}</main>
      </body>
    </html>
  );
}
