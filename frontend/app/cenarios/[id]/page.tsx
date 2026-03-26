"use client";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { getCenario, createCenario, updateCenario, getParametros } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { ArrowLeft, Save, AlertCircle } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function CenarioFormPage() {
  const router = useRouter();
  const params = useParams();
  const id     = params?.id as string;
  const isNew  = id === "novo";

  const [descricao,   setDescricao]   = useState("");
  const [parametroId, setParametroId] = useState("");
  const [ativo,       setAtivo]       = useState(true);
  const [padrao,      setPadrao]      = useState(false);
  const [parametros,  setParametros]  = useState<any[]>([]);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState("");

  useEffect(() => {
    getParametros().then(setParametros).catch(() => {});
    if (!isNew) {
      getCenario(Number(id)).then(data => {
        setDescricao(data.descricao ?? "");
        setParametroId(String(data.idparametro ?? ""));
        setAtivo(data.ativo ?? true);
        setPadrao(data.padrao ?? false);
      }).catch(e => setError(e.message));
    }
  }, [id]);

  async function salvar() {
    if (!descricao.trim()) { setError("A descrição é obrigatória."); return; }
    if (!parametroId) { setError("Selecione um parâmetro."); return; }
    setLoading(true); setError("");
    try {
      const payload = { descricao, idparametro: Number(parametroId), ativo, padrao };
      if (isNew) await createCenario(payload);
      else await updateCenario(Number(id), payload);
      toast.success("Cenário salvo com sucesso!");
      router.push("/cenarios");
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/cenarios"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">{isNew ? "Novo Cenário" : "Editar Cenário"}</h1>
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      <Card>
        <CardHeader><CardTitle className="text-base">Dados do Cenário</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <Label>Descrição <span className="text-red-500">*</span></Label>
            <Input value={descricao} onChange={e => setDescricao(e.target.value)} placeholder="Ex: Cenário Principal" />
          </div>

          <div className="space-y-1.5">
            <Label>Parâmetro <span className="text-red-500">*</span></Label>
            <Select value={parametroId} onValueChange={setParametroId}>
              <SelectTrigger><SelectValue placeholder="Selecione..." /></SelectTrigger>
              <SelectContent>
                {parametros.map((p: any) => (
                  <SelectItem key={p.id} value={String(p.id)}>{p.nome}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <Checkbox id="ativo" checked={ativo} onCheckedChange={v => setAtivo(!!v)} />
              <Label htmlFor="ativo" className="cursor-pointer">Ativo</Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox id="padrao" checked={padrao} onCheckedChange={v => setPadrao(!!v)} />
              <Label htmlFor="padrao" className="cursor-pointer">Padrão</Label>
            </div>
          </div>

          <Button onClick={salvar} disabled={loading}>
            <Save className="mr-2 h-4 w-4" />{loading ? "Salvando..." : "Salvar"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
