"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getToken, getMe, logout as limparSessao } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import { Loader2 } from "lucide-react";

// Rotas que nao exigem login
const ROTAS_PUBLICAS = ["/login"];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router   = useRouter();
  const [status, setStatus] = useState<"verificando" | "ok" | "publico">("verificando");

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
      .then(() => setStatus("ok"))
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
        {children}
      </main>
    </div>
  );
}
