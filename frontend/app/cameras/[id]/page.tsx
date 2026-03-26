"use client";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { getCamera, createCamera, updateCamera, getLocalizacoes } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Save, AlertCircle } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function CameraFormPage() {
  const router = useRouter();
  const params = useParams();
  const id     = params?.id as string;
  const isNew  = id === "novo";

  const [nome,              setNome]              = useState("");
  const [localizacaoId,     setLocalizacaoId]     = useState("");
  const [andar,             setAndar]             = useState("0");
  const [nrsala,            setNrsala]            = useState("0");
  const [notaIgnorar,       setNotaIgnorar]       = useState("0.7");
  const [notaIdentificacao, setNotaIdentificacao] = useState("0.7");
  const [localizacoes,      setLocalizacoes]      = useState<any[]>([]);
  const [loading,           setLoading]           = useState(false);
  const [error,             setError]             = useState("");

  useEffect(() => {
    getLocalizacoes().then(setLocalizacoes).catch(() => {});
    if (!isNew) {
      getCamera(Number(id)).then(data => {
        setNome(data.nome ?? "");
        setLocalizacaoId(String(data.idlocalizacao ?? ""));
        setAndar(String(data.andar ?? 0));
        setNrsala(String(data.nrsala ?? 0));
        setNotaIgnorar(String(data.notaparaignorar ?? 0.7));
        setNotaIdentificacao(String(data.notaidentificacao ?? 0.7));
      }).catch(e => setError(e.message));
    }
  }, [id]);

  async function salvar() {
    if (!nome.trim() || !localizacaoId) { setError("Preencha o Nome e selecione uma Localização."); return; }
    setLoading(true); setError("");
    try {
      const payload = {
        nome, idlocalizacao: Number(localizacaoId),
        andar: Number(andar), nrsala: Number(nrsala),
        notaparaignorar: Number(notaIgnorar),
        notaidentificacao: Number(notaIdentificacao),
      };
      if (isNew) await createCamera(payload);
      else await updateCamera(Number(id), payload);
      toast.success("Câmera salva com sucesso!");
      router.push("/cameras");
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/cameras"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">{isNew ? "Nova Câmera" : "Editar Câmera"}</h1>
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      <Card>
        <CardHeader><CardTitle className="text-base">Dados da Câmera</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <Label>Nome da Câmera <span className="text-red-500">*</span></Label>
            <Input value={nome} onChange={e => setNome(e.target.value)} placeholder="Ex: Câmera Recepção" />
          </div>

          <div className="space-y-1.5">
            <Label>Localização <span className="text-red-500">*</span></Label>
            <Select value={localizacaoId} onValueChange={setLocalizacaoId}>
              <SelectTrigger><SelectValue placeholder="Selecione..." /></SelectTrigger>
              <SelectContent>
                {localizacoes.map((l: any) => (
                  <SelectItem key={l.id} value={String(l.id)}>{l.nome}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Andar</Label>
              <Input type="number" value={andar} onChange={e => setAndar(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Nº Sala Próxima</Label>
              <Input type="number" value={nrsala} onChange={e => setNrsala(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Nota para Ignorar <span className="text-xs text-zinc-400">(0.0 a 1.0)</span></Label>
              <Input type="number" step="0.05" value={notaIgnorar} onChange={e => setNotaIgnorar(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Nota de Identificação <span className="text-xs text-zinc-400">(0.0 a 1.0)</span></Label>
              <Input type="number" step="0.05" value={notaIdentificacao} onChange={e => setNotaIdentificacao(e.target.value)} />
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
