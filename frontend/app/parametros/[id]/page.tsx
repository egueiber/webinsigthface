"use client";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { getParametro, createParametro, updateParametro, getUsuarioLocal } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, Save, AlertCircle, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

const defaults = {
  nome: "", fotos: "", mapas: "", videos_a_processar: "",
  videos_processados: "", video_marcoes: "",
  intervalo_frames: "15", escala_imagem: "1.0",
  tolerancia: "0.6", modelo_deteccao: "hog",
  gerar_marcoes: false, finalizaraoidentificartodos: false,
  biodoc_api_url: "", biodoc_api_token: "",
};

export default function ParametroFormPage() {
  const router = useRouter();
  const params = useParams();
  const id     = params?.id as string;
  const isNew  = id === "novo";

  const [form,    setForm]    = useState(defaults);
  const [loading, setLoading] = useState(false);
  const [carregando, setCarregando] = useState(!isNew);
  const [error,   setError]   = useState("");
  const [souAdmin, setSouAdmin] = useState(false);

  useEffect(() => {
    setSouAdmin(getUsuarioLocal()?.papel === "admin");
  }, []);

  useEffect(() => {
    if (!isNew) {
      setCarregando(true);
      getParametro(Number(id))
        .then(data => {
          // O backend devolve os campos em ingles (name, photos_path, ...).
          // Aceita tambem os nomes em portugues, por seguranca.
          setForm({
            nome:               data.name ?? data.nome ?? "",
            fotos:              data.photos_path ?? data.fotos ?? "",
            mapas:              data.maps_path ?? data.mapas ?? "",
            videos_a_processar: data.videos_to_process_path ?? data.videos_a_processar ?? "",
            videos_processados: data.processed_videos_path ?? data.videos_processados ?? "",
            video_marcoes:      data.video_markers_path ?? data.video_marcoes ?? "",
            intervalo_frames:   String(data.frame_interval ?? data.intervalo_frames ?? 15),
            escala_imagem:      String(data.image_scale ?? data.escala_imagem ?? 1.0),
            tolerancia:         String(data.recognition_tolerance ?? data.tolerancia ?? 0.6),
            modelo_deteccao:    data.detection_model ?? data.modelo_deteccao ?? "hog",
            gerar_marcoes:      data.generate_markers ?? data.gerar_marcoes ?? false,
            finalizaraoidentificartodos:
              data.finish_when_all_identified ?? data.finalizaraoidentificartodos ?? false,
            biodoc_api_url:     data.biodoc_api_url ?? "",
            biodoc_api_token:   data.biodoc_api_token ?? "",
          });
        })
        .catch(e => setError(String(e.message ?? e)))
        .finally(() => setCarregando(false));
    }
  }, [id]);

  function set(key: string, value: any) {
    setForm(f => ({ ...f, [key]: value }));
  }

  async function salvar() {
    if (!form.nome.trim()) { setError("O nome do parâmetro é obrigatório."); return; }
    setLoading(true); setError("");
    try {
      const payload = {
        ...form,
        intervalo_frames: Number(form.intervalo_frames),
        escala_imagem: parseFloat(form.escala_imagem),
        tolerancia: parseFloat(form.tolerancia),
      };
      if (isNew) await createParametro(payload);
      else await updateParametro(Number(id), payload);
      toast.success("Parâmetros salvos com sucesso!");
      router.push("/parametros");
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  const PathField = ({ label, field }: { label: string; field: string }) => (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <Input value={(form as any)[field]} onChange={e => set(field, e.target.value)}
        className="font-mono text-sm" placeholder="Ex: C:\pasta\" />
    </div>
  );

  if (carregando) {
    return (
      <div className="space-y-6 max-w-2xl">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/parametros"><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <h1 className="text-2xl font-bold text-zinc-800">Editar Parâmetro</h1>
        </div>
        <div className="flex items-center justify-center py-20 text-zinc-400 text-sm">
          Carregando parâmetros...
        </div>
      </div>
    );
  }

  if (!souAdmin) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-zinc-400 gap-3">
        <ShieldAlert className="h-10 w-10" />
        <p className="text-sm">Esta área é restrita a administradores.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/parametros"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">{isNew ? "Novo Parâmetro" : "Editar Parâmetro"}</h1>
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      <Card>
        <CardHeader><CardTitle className="text-base">Identificação</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-1.5">
            <Label>Nome do Parâmetro <span className="text-red-500">*</span></Label>
            <Input value={form.nome} onChange={e => set("nome", e.target.value)} placeholder="Ex: Configuração Principal" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Caminhos de Pastas</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <PathField label="Fotos dos Clientes"      field="fotos" />
          <PathField label="Mapas das Câmeras"        field="mapas" />
          <PathField label="Vídeos a Processar"       field="videos_a_processar" />
          <PathField label="Vídeos Processados"       field="videos_processados" />
          <PathField label="Vídeos com Marcações"     field="video_marcoes" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Reconhecimento Facial</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Intervalo de Frames</Label>
              <Input type="number" value={form.intervalo_frames} onChange={e => set("intervalo_frames", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Escala da Imagem</Label>
              <Input type="number" step="0.1" value={form.escala_imagem} onChange={e => set("escala_imagem", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Tolerância <span className="text-xs text-zinc-400">(0.0 a 1.0)</span></Label>
              <Input type="number" step="0.05" value={form.tolerancia} onChange={e => set("tolerancia", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Modelo de Detecção</Label>
              <Select value={form.modelo_deteccao} onValueChange={v => set("modelo_deteccao", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="hog">hog (CPU)</SelectItem>
                  <SelectItem value="cnn">cnn (GPU)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Checkbox id="gerar" checked={form.gerar_marcoes}
                onCheckedChange={v => set("gerar_marcoes", !!v)} />
              <Label htmlFor="gerar" className="cursor-pointer">Gerar vídeo com marcações</Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox id="finalizar" checked={form.finalizaraoidentificartodos}
                onCheckedChange={v => set("finalizaraoidentificartodos", !!v)} />
              <Label htmlFor="finalizar" className="cursor-pointer">
                Finalizar ao identificar todos com eventos ativos
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Integração Biodoc</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="biodoc-url">URL da API</Label>
            <Input id="biodoc-url" name="biodoc-url" autoComplete="off"
              value={form.biodoc_api_url} onChange={e => set("biodoc_api_url", e.target.value)}
              className="font-mono text-sm" placeholder="Ex: https://api.sandbox.biodoc.com.br/api" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="biodoc-token">Token de Acesso</Label>
            <Input id="biodoc-token" name="biodoc-token" type="password" autoComplete="new-password"
              value={form.biodoc_api_token} onChange={e => set("biodoc_api_token", e.target.value)}
              className="font-mono text-sm" placeholder="Token fornecido pela Biodoc" />
            <p className="text-xs text-zinc-400">
              Usado para buscar fotos biométricas dos beneficiários. Fornecido pela Biodoc à Unimed.
            </p>
          </div>
        </CardContent>
      </Card>

      <Button onClick={salvar} disabled={loading} size="lg">
        <Save className="mr-2 h-4 w-4" />{loading ? "Salvando..." : "Salvar Parâmetros"}
      </Button>
    </div>
  );
}
