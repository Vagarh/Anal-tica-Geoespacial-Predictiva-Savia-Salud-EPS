"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Map, BarChart3, Brain, Activity } from "lucide-react";
import clsx from "clsx";

const NAV = [
  { href: "/",           label: "Resumen",        icon: LayoutDashboard },
  { href: "/modelo",     label: "Evaluación Modelo", icon: Brain },
  { href: "/riesgo",     label: "Mapa de Riesgo",  icon: Map },
  { href: "/prestadores",label: "Red IPS",         icon: Activity },
  { href: "/features",   label: "Features SHAP",   icon: BarChart3 },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed top-0 left-0 h-screen w-[240px] bg-brand-900 flex flex-col z-50 shadow-2xl">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center flex-shrink-0">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
              <circle cx="12" cy="9" r="2.5"/>
            </svg>
          </div>
          <div>
            <p className="text-white font-bold text-sm leading-tight">Savia Salud EPS</p>
            <p className="text-white/40 text-xs">Analítica Geoespacial</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                active
                  ? "bg-brand-500 text-white shadow-lg"
                  : "text-white/60 hover:text-white hover:bg-white/10"
              )}
            >
              <Icon size={17} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-white/10">
        <p className="text-white/30 text-xs">v3 · 2026-05-05</p>
        <p className="text-white/20 text-xs mt-0.5">Solo lectura · Ley 1581</p>
      </div>
    </aside>
  );
}
