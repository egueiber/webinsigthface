"use client";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { getLocalizacao, createLocalizacao, updateLocalizacao } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Save, AlertCircle } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function LocalizacaoFormPage() {
  const router = useRouter();
  const params = useParams();
  const id     = params?.id as string;
  const isNew  = id === "novo";

  const [nome,     setNome]     = useState("");
  const [mapaPath, setMapaPath] = useState("");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");

  useEffect(() => {
    if (!isNew) {
      getLocalizacao(Number(id))
        .then(data => {
          setNome(data.nome ?? data.nomelocalizacao ?? data.name ?? "");
          setMapaPath(data.mapa_path ?? data.mapacamera ?? "");
        })
        .catch(e => setError(String(e.message ?? e)));
    }
  }, [id]);

  async function salvar() {
    if (!nome.trim()) { setError("O nome da localização é obrigatório."); return; }
    setLoading(true); setError("");
    try {
      const payload = { nome, mapa_path: mapaPath };
      if (isNew) await createLocalizacao(payload);
      else await updateLocalizacao(Number(id), payload);
      toast.success("Localização salva com sucesso!");
      router.push("/localizacoes");
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/localizacoes"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">{isNew ? "Nova Localização" : "Editar Localização"}</h1>
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      <Card>
        <CardHeader><CardTitle className="text-base">Dados da Localização</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <Label>Nome da Localização <span className="text-red-500">*</span></Label>
            <Input value={nome} onChange={e => setNome(e.target.value)} placeholder="Ex: Ala Norte - 2º Andar" />
          </div>
          <div className="space-y-1.5">
            <Label>Caminho da Imagem (Mapa)</Label>
            <Input value={mapaPath} onChange={e => setMapaPath(e.target.value)}
              placeholder="Ex: /app/data/mapas/ala_norte.png" className="font-mono text-sm" />
            <p className="text-xs text-zinc-400">Caminho do arquivo de mapa dentro do servidor Docker.</p>
          </div>
          <Button onClick={salvar} disabled={loading}>
            <Save className="mr-2 h-4 w-4" />{loading ? "Salvando..." : "Salvar"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
