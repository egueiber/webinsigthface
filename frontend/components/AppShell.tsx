"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getToken, getMe, logout as limparSessao } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import { Loader2, ShieldAlert } from "lucide-react";

// Rotas que nao exigem login
const ROTAS_PUBLICAS = ["/login"];

// Rotas (e todas as sub-rotas, ex: /cameras/6) restritas a administradores
const ROTAS_ADMIN = ["/pessoas", "/cameras", "/localizacoes", "/eventos", "/cenarios", "/parametros", "/usuarios", "/pessoa-eventos"];

function isRotaAdmin(pathname: string) {
  return ROTAS_ADMIN.some(r => pathname === r || pathname.startsWith(r + "/"));
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router   = useRouter();
  const [status, setStatus] = useState<"verificando" | "ok" | "publico">("verificando");
  const [isAdmin, setIsAdmin] = useState(false);

  const isPublica = ROTAS_PUBLICAS.includes(pathname);

  useEffect(() => {
    if (isPublica) {
      setStatus("publico");
      return;
    }

    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    // Valida o token no backend (pode ter expirado)
    getMe()
      .then((usuario) => {
        setIsAdmin(usuario?.papel === "admin");
        setStatus("ok");
      })
      .catch(() => {
        limparSessao();
        router.replace("/login");
      });
  }, [pathname, isPublica, router]);

  // Tela de login: sem sidebar
  if (isPublica) {
    return <>{children}</>;
  }

  // Verificando sessao
  if (status !== "ok") {
    return (
      <div className="h-screen flex items-center justify-center bg-zinc-50">
        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
      </div>
    );
  }

  // Sistema autenticado
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        {isRotaAdmin(pathname) && !isAdmin ? (
          <div className="flex flex-col items-center justify-center py-20 text-zinc-400 gap-3">
            <ShieldAlert className="h-10 w-10" />
            <p className="text-sm">Esta área é restrita a administradores.</p>
          </div>
        ) : children}
      </main>
    </div>
  );
}
