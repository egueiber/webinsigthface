"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard, Users, Camera, MapPin,
  CalendarDays, Film, Settings, Map, UserSearch, UserCheck, LogOut, ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getUsuarioLocal, logout } from "@/lib/api";
import { toast } from "sonner";

const navItems = [
  { label: "Dashboard",          href: "/dashboard",               icon: LayoutDashboard },
  { label: "Pessoas",            href: "/pessoas",                 icon: Users },
  { label: "Câmeras",            href: "/cameras",                 icon: Camera },
  { label: "Localizações",       href: "/localizacoes",            icon: MapPin },
  { label: "Eventos",            href: "/eventos",                 icon: CalendarDays },
  { label: "Cenários",           href: "/cenarios",                icon: Film },
  { label: "Pessoa — Eventos",   href: "/pessoa-eventos",          icon: UserCheck },
  { label: "Acomp. Área",        href: "/acompanhamento-area",     icon: Map },
  { label: "Acomp. Pessoa",      href: "/acompanhamento-pessoa",   icon: UserSearch },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router   = useRouter();
  const [usuario, setUsuario] = useState<any>(null);

  useEffect(() => {
    setUsuario(getUsuarioLocal());
  }, []);

  function sair() {
    logout();
    toast.success("Sessão encerrada.");
    router.replace("/login");
  }

  const isAdmin = usuario?.papel === "admin";

  const itensCompletos = isAdmin
    ? [...navItems, { label: "Parâmetros", href: "/parametros", icon: Settings }, { label: "Usuários", href: "/usuarios", icon: ShieldCheck }]
    : navItems;

  return (
    <aside className="w-56 flex flex-col shrink-0" style={{ background: "#1a4731" }}>
      <div className="px-5 py-5 border-b" style={{ borderColor: "#255c40" }}>
        <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: "#7fbf99" }}>Health Track</p>
        <p className="text-sm mt-0.5" style={{ color: "#e8f5ee" }}>Unimed · UEPG</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {itensCompletos.map(({ label, href, icon: Icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link key={href} href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                active ? "text-white" : "hover:text-white"
              )}
              style={{
                background: active ? "#2d7a50" : "transparent",
                color: active ? "#ffffff" : "#a8d5bc",
              }}>
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Rodape: usuario logado + sair */}
      <div className="px-3 py-3 border-t" style={{ borderColor: "#255c40" }}>
        {usuario && (
          <div className="px-2 pb-2">
            <p className="text-sm font-medium truncate" style={{ color: "#e8f5ee" }}>
              {usuario.nome}
            </p>
            <p className="text-xs" style={{ color: "#7fbf99" }}>
              {usuario.papel === "admin" ? "Administrador" : "Usuário"}
            </p>
          </div>
        )}
        <button
          onClick={sair}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors hover:bg-white/10"
          style={{ color: "#a8d5bc" }}
        >
          <LogOut size={16} />
          Sair
        </button>
      </div>
    </aside>
  );
}
