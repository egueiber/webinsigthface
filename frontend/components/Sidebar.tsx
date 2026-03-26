"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Users, Camera, MapPin,
  CalendarDays, Film, Settings, Map, UserSearch,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Dashboard",          href: "/dashboard",               icon: LayoutDashboard },
  { label: "Pessoas",            href: "/pessoas",                 icon: Users },
  { label: "Câmeras",            href: "/cameras",                 icon: Camera },
  { label: "Localizações",       href: "/localizacoes",            icon: MapPin },
  { label: "Eventos",            href: "/eventos",                 icon: CalendarDays },
  { label: "Cenários",           href: "/cenarios",                icon: Film },
  { label: "Acomp. Área",        href: "/acompanhamento-area",     icon: Map },
  { label: "Acomp. Pessoa",      href: "/acompanhamento-pessoa",   icon: UserSearch },
  { label: "Parâmetros",         href: "/parametros",              icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 bg-zinc-900 text-white flex flex-col shrink-0">
      <div className="px-5 py-5 border-b border-zinc-700">
        <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Health Track</p>
        <p className="text-sm text-zinc-300 mt-0.5">Unimed · UEPG</p>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ label, href, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link key={href} href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                active ? "bg-blue-600 text-white" : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
              )}>
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
