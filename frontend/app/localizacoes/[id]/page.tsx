"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { getLocalizacao, createLocalizacao, updateLocalizacao, uploadMapaLocalizacao } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Save, AlertCircle, Upload, ImageIcon, Check } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function LocalizacaoFormPage() {
  const router = useRouter();
  const params = useParams();
  const id     = params?.id as string;
  const isNew  = id === "novo";

  const [nome,        setNome]        = useState("");
  const [mapaPath,    setMapaPath]    = useState("");
  const [mapaPreview, setMapaPreview] = useState<string | null>(null);
  const [pid,         setPid]         = useState<number | null>(isNew ? null : Number(id));
  const [dadosSalvos, setDadosSalvos] = useState(!isNew);
  const [uploading,   setUploading]   = useState(false);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isNew) {
      getLocalizacao(Number(id))
        .then(data => {
          setNome(data.nome ?? data.name ?? data.nomelocalizacao ?? "");
          const path = data.mapa_path ?? data.map_path ?? data.mapacamera ?? "";
          setMapaPath(path);
          if (path) setMapaPreview(`${API}/media/frame?path=${encodeURIComponent(path)}`);
        })
        .catch(e => setError(String(e.message ?? e)));
    }
  }, [id]);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!pid) {
      toast.warning("Salve os dados da localização primeiro, depois faça o upload do mapa.");
      return;
    }
    setUploading(true);
    try {
      const data = await uploadMapaLocalizacao(pid, file);
      setMapaPath(data.path);
      setMapaPreview(`${API}/media/frame?path=${encodeURIComponent(data.path)}&t=${Date.now()}`);
      toast.success("Mapa enviado com sucesso!");
    } catch (e: any) { toast.error(String(e.message ?? e)); }
    finally { setUploading(false); e.target.value = ""; }
  }

  async function salvar() {
    if (!nome.trim()) { setError("O nome da localização é obrigatório."); return; }
    setLoading(true); setError("");
    try {
      if (isNew && !pid) {
        const res = await createLocalizacao({ nome, mapa_path: mapaPath });
        const newId = res?.id ?? null;
        if (newId) setPid(newId);
        setDadosSalvos(true);
        toast.success("Dados salvos! Agora você já pode adicionar o mapa.");
      } else {
        await updateLocalizacao(pid!, { nome, mapa_path: mapaPath });
        setDadosSalvos(true);
        toast.success("Localização atualizada com sucesso!");
      }
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/localizacoes"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">
          {isNew && !dadosSalvos ? "Nova Localização" : (nome || "Editar Localização")}
        </h1>
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      <Card>
        <CardHeader><CardTitle className="text-base">Dados da Localização</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <Label>Nome da Localização <span className="text-red-500">*</span></Label>
            <Input value={nome} onChange={e => setNome(e.target.value)} placeholder="Ex: Ala Norte - 2º Andar" />
          </div>

          <div className="flex gap-2">
            <Button onClick={salvar} disabled={loading}>
              <Save className="mr-2 h-4 w-4" />{loading ? "Salvando..." : "Salvar dados"}
            </Button>
            {dadosSalvos && (
              <Button variant="outline" onClick={() => router.push("/localizacoes")}>
                <Check className="mr-2 h-4 w-4" />Concluir
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Imagem do Mapa</CardTitle>
          {!pid && <p className="text-xs text-zinc-400 mt-1">Salve os dados da localização primeiro para adicionar o mapa.</p>}
        </CardHeader>
        <CardContent className="space-y-1.5">
          {mapaPreview ? (
            <div className="space-y-2">
              <img src={mapaPreview} alt="Mapa" className="w-full rounded-lg border border-zinc-200 max-h-48 object-contain bg-zinc-50" onError={() => setMapaPreview(null)} />
              <Button variant="outline" size="sm" onClick={() => fileRef.current?.click()} disabled={uploading || !pid}>
                <Upload className="mr-2 h-4 w-4" />{uploading ? "Enviando..." : "Trocar imagem"}
              </Button>
            </div>
          ) : (
            <div
              onClick={() => pid && fileRef.current?.click()}
              className={`flex flex-col items-center justify-center gap-2 h-32 rounded-lg border-2 border-dashed border-zinc-200 bg-zinc-50 text-zinc-400 text-sm ${pid ? "cursor-pointer hover:border-zinc-300 hover:bg-zinc-100" : "opacity-50 cursor-not-allowed"}`}>
              <ImageIcon className="h-8 w-8" />
              <span>{pid ? (uploading ? "Enviando..." : "Clique para selecionar uma imagem") : "Salve os dados primeiro"}</span>
              <span className="text-xs">JPG, PNG ou WebP</span>
            </div>
          )}
          <input ref={fileRef} type="file" accept=".jpg,.jpeg,.png,.webp" className="hidden" onChange={handleFileChange} disabled={!pid || uploading} />
          {mapaPath && <p className="text-xs text-zinc-400 font-mono truncate">{mapaPath}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
