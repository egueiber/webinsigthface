"use client";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { getEvento, createEvento, updateEvento } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Save, AlertCircle } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function EventoFormPage() {
  const router = useRouter();
  const params = useParams();
  const id     = params?.id as string;
  const isNew  = id === "novo";

  const [nome,    setNome]    = useState("");
  const [duracao, setDuracao] = useState("");
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  useEffect(() => {
    if (!isNew) {
      getEvento(Number(id))
        .then(data => { setNome(data.nome ?? ""); setDuracao(data.duracao != null ? String(data.duracao) : ""); })
        .catch(e => setError(e.message));
    }
  }, [id]);

  async function salvar() {
    if (!nome.trim()) { setError("O nome do evento é obrigatório."); return; }
    if (duracao && isNaN(Number(duracao))) { setError("A duração deve ser um número inteiro."); return; }
    setLoading(true); setError("");
    try {
      const payload = { nome, duracao: duracao ? Number(duracao) : null };
      if (isNew) await createEvento(payload);
      else await updateEvento(Number(id), payload);
      toast.success("Evento salvo com sucesso!");
      router.push("/eventos");
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/eventos"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">{isNew ? "Novo Evento" : "Editar Evento"}</h1>
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      <Card>
        <CardHeader><CardTitle className="text-base">Dados do Evento</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <Label>Nome do Evento <span className="text-red-500">*</span></Label>
            <Input value={nome} onChange={e => setNome(e.target.value)} placeholder="Ex: Consulta Médica" />
          </div>
          <div className="space-y-1.5">
            <Label>Duração (minutos)</Label>
            <Input type="number" value={duracao} onChange={e => setDuracao(e.target.value)}
              placeholder="Ex: 30" className="w-40" />
          </div>

          <Button onClick={salvar} disabled={loading}>
            <Save className="mr-2 h-4 w-4" />{loading ? "Salvando..." : "Salvar"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
