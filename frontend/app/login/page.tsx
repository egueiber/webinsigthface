"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { login, setupNeeded, setupAdmin, setToken, setUsuarioLocal } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, LogIn, UserPlus, Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function LoginPage() {
  const router = useRouter();

  const [modo, setModo]         = useState<"carregando" | "login" | "setup">("carregando");
  const [nome, setNome]         = useState("");
  const [usuario, setUsuario]   = useState("");
  const [senha, setSenha]       = useState("");
  const [confirma, setConfirma] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  // Verifica se ja existe algum usuario cadastrado
  useEffect(() => {
    setupNeeded()
      .then(res => setModo(res.setup_needed ? "setup" : "login"))
      .catch(() => setModo("login"));
  }, []);

  async function entrar() {
    if (!usuario.trim() || !senha) {
      setError("Informe usuário e senha.");
      return;
    }
    setLoading(true); setError("");
    try {
      const res = await login({ login: usuario.trim(), senha });
      setToken(res.access_token);
      setUsuarioLocal(res.usuario);
      toast.success(`Bem-vindo, ${res.usuario.nome}!`);
      router.push("/dashboard");
    } catch (e: any) {
      setError(String(e.message ?? e));
    } finally {
      setLoading(false);
    }
  }

  async function criarAdmin() {
    if (!nome.trim())        { setError("Informe o nome."); return; }
    if (!usuario.trim())     { setError("Informe o login."); return; }
    if (senha.length < 6)    { setError("A senha deve ter pelo menos 6 caracteres."); return; }
    if (senha !== confirma)  { setError("As senhas não conferem."); return; }

    setLoading(true); setError("");
    try {
      await setupAdmin({ nome: nome.trim(), login: usuario.trim(), senha });
      toast.success("Administrador criado! Faça login para continuar.");
      setModo("login");
      setSenha(""); setConfirma(""); setNome("");
    } catch (e: any) {
      setError(String(e.message ?? e));
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !loading) {
      modo === "setup" ? criarAdmin() : entrar();
    }
  }

  if (modo === "carregando") {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#f4f7f5" }}>
        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: "#f4f7f5" }}>
      <div className="w-full max-w-sm space-y-6">
        {/* Marca */}
        <div className="text-center space-y-1">
          <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: "#2d7a50" }}>
            Health Track
          </p>
          <p className="text-sm text-zinc-500">Unimed · UEPG</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {modo === "setup" ? "Criar administrador" : "Entrar no sistema"}
            </CardTitle>
            {modo === "setup" && (
              <p className="text-xs text-zinc-500 mt-1">
                Nenhum usuário cadastrado ainda. Crie o primeiro administrador para começar.
              </p>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-xs">{error}</AlertDescription>
              </Alert>
            )}

            {modo === "setup" && (
              <div className="space-y-1.5">
                <Label>Nome completo</Label>
                <Input value={nome} onChange={e => setNome(e.target.value)}
                  onKeyDown={onKeyDown} placeholder="Nome completo" autoFocus />
              </div>
            )}

            <div className="space-y-1.5">
              <Label>Usuário</Label>
              <Input value={usuario} onChange={e => setUsuario(e.target.value)}
                onKeyDown={onKeyDown} placeholder="Nome de usuário"
                autoFocus={modo === "login"} autoComplete="username" />
            </div>

            <div className="space-y-1.5">
              <Label>Senha</Label>
              <Input type="password" value={senha} onChange={e => setSenha(e.target.value)}
                onKeyDown={onKeyDown} placeholder="••••••"
                autoComplete={modo === "setup" ? "new-password" : "current-password"} />
              {modo === "setup" && (
                <p className="text-xs text-zinc-400">Mínimo de 6 caracteres.</p>
              )}
            </div>

            {modo === "setup" && (
              <div className="space-y-1.5">
                <Label>Confirmar senha</Label>
                <Input type="password" value={confirma} onChange={e => setConfirma(e.target.value)}
                  onKeyDown={onKeyDown} placeholder="••••••" autoComplete="new-password" />
              </div>
            )}

            <Button
              onClick={modo === "setup" ? criarAdmin : entrar}
              disabled={loading}
              className="w-full"
              style={{ background: "#2d7a50" }}
            >
              {loading ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Aguarde...</>
              ) : modo === "setup" ? (
                <><UserPlus className="mr-2 h-4 w-4" />Criar administrador</>
              ) : (
                <><LogIn className="mr-2 h-4 w-4" />Entrar</>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
