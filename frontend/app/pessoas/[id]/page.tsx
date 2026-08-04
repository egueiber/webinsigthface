"use client";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { getPessoa, createPessoa, updatePessoa, getFotosPessoa, uploadFotoPessoa, deleteFotoPessoa, vincularBiodoc } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowLeft, Save, AlertCircle, Upload, Trash2, Check, IdCard, Search } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function PessoaFormPage() {
  const router = useRouter();
  const params = useParams();
  const id    = params?.id as string;
  const isNew = id === "novo";

  const [nome,         setNome]         = useState("");
  const [documento,    setDocumento]    = useState("");
  const [carteirinha,  setCarteirinha]  = useState("");
  const [fotosExist,   setFotosExist]   = useState<string[]>([]);
  const [folderPath,   setFolderPath]   = useState("");
  const [pid,          setPid]          = useState<number | null>(isNew ? null : Number(id));
  const [dadosSalvos,  setDadosSalvos]  = useState(!isNew);
  const [loading,      setLoading]      = useState(false);
  const [uploading,    setUploading]    = useState(false);
  const [buscandoBio,  setBuscandoBio]  = useState(false);
  const [error,        setError]        = useState("");

  useEffect(() => {
    if (!isNew) {
      getPessoa(Number(id))
        .then(data => {
          setNome(data.name ?? data.nome ?? "");
          setDocumento(data.document ?? data.documento ?? "");
          setCarteirinha(data.biodoc_card ?? "");
          carregarFotos(Number(id));
        })
        .catch(e => setError(String(e.message ?? e)));
    }
  }, [id]);

  async function carregarFotos(personId: number) {
    try {
      const data = await getFotosPessoa(personId);
      setFotosExist(data.photos ?? []);
      setFolderPath(data.folder_path ?? "");
    } catch (e: any) { setError(String(e.message ?? e)); }
  }

  async function salvar() {
    if (!nome.trim())      { setError("O nome é obrigatório."); return; }
    if (!documento.trim()) { setError("O documento é obrigatório."); return; }
    setLoading(true); setError("");
    try {
      if (isNew && !pid) {
        const res = await createPessoa({ nome, documento, carteirinha });
        const newId = res?.id ?? res?.person_id ?? null;
        if (newId) { setPid(newId); await carregarFotos(newId); }
        setDadosSalvos(true);
        toast.success("Dados salvos! Agora adicione as fotos.");
      } else {
        await updatePessoa(pid!, { nome, documento, carteirinha });
        setDadosSalvos(true);
        toast.success("Dados atualizados com sucesso!");
      }
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  // ── Biodoc ────────────────────────────────────────────────────────────────
  async function buscarFotoBiodoc() {
    if (!carteirinha.trim()) { toast.warning("Informe o número da carteirinha primeiro."); return; }
    if (!pid) { toast.warning("Salve os dados cadastrais antes de buscar a foto."); return; }
    setBuscandoBio(true);
    try {
      const data = await vincularBiodoc(pid, carteirinha);
      toast.success(`Foto da Biodoc vinculada! (${data.biodoc_name ?? "beneficiário"})`);
      carregarFotos(pid);
    } catch (e: any) {
      toast.error(String(e.message ?? e));
    } finally {
      setBuscandoBio(false);
    }
  }

  // ── Upload de arquivo ─────────────────────────────────────────────────────
  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (!files.length || !pid) return;
    setUploading(true);
    let ok = 0;
    for (const file of files) {
      try {
        await uploadFotoPessoa(pid, file);
        ok++;
      } catch (e: any) { toast.error(`Erro ao enviar ${file.name}: ${String(e.message ?? e)}`); }
    }
    if (ok > 0) { toast.success(`${ok} foto(s) enviada(s)!`); carregarFotos(pid); }
    setUploading(false);
    e.target.value = "";
  }

  async function excluirFoto(filename: string) {
    if (!pid) return;
    try {
      await deleteFotoPessoa(pid, filename);
      toast.success("Foto removida.");
      carregarFotos(pid);
    } catch (e: any) { toast.error(String(e.message ?? e)); }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/pessoas"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">{isNew && !dadosSalvos ? "Nova Pessoa" : nome || "Editar Pessoa"}</h1>
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      {/* Dados cadastrais */}
      <Card>
        <CardHeader><CardTitle className="text-base">Dados Cadastrais</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label>Nome Completo <span className="text-red-500">*</span></Label>
            <Input value={nome} onChange={e => setNome(e.target.value)} placeholder="Ex: João da Silva" />
          </div>
          <div className="space-y-1.5">
            <Label>Documento <span className="text-red-500">*</span></Label>
            <Input value={documento} onChange={e => setDocumento(e.target.value)} placeholder="CPF, RG ou matrícula" />
          </div>
          <div className="space-y-1.5">
            <Label className="flex items-center gap-1.5"><IdCard className="h-3.5 w-3.5" />Carteirinha (Biodoc)</Label>
            <Input value={carteirinha} onChange={e => setCarteirinha(e.target.value)} placeholder="Número da carteirinha do beneficiário" className="font-mono" />
            <p className="text-xs text-zinc-400">Usada para buscar a foto biométrica cadastrada na Biodoc.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={salvar} disabled={loading}>
              <Save className="mr-2 h-4 w-4" />{loading ? "Salvando..." : "Salvar dados"}
            </Button>
            {dadosSalvos && (
              <Button variant="outline" onClick={() => router.push("/pessoas")}>
                <Check className="mr-2 h-4 w-4" />Concluir
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Fotos */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Fotos para Reconhecimento</CardTitle>
          {!dadosSalvos && <p className="text-xs text-zinc-400 mt-1">Salve os dados cadastrais primeiro para adicionar fotos.</p>}
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="biodoc">
            <TabsList className="mb-4">
              <TabsTrigger value="biodoc"><IdCard className="mr-2 h-4 w-4" />Biodoc</TabsTrigger>
              <TabsTrigger value="upload"><Upload className="mr-2 h-4 w-4" />Upload</TabsTrigger>
            </TabsList>

            {/* ── Biodoc ── */}
            <TabsContent value="biodoc" className="space-y-4">
              {!dadosSalvos ? (
                <p className="text-sm text-zinc-400">Salve os dados cadastrais primeiro.</p>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-zinc-600">
                    Busca automaticamente a foto cadastrada na Biodoc usando o número da carteirinha informado nos dados cadastrais.
                  </p>
                  <div className="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 flex items-center justify-between">
                    <div className="text-sm">
                      <span className="text-zinc-500">Carteirinha:</span>{" "}
                      <span className="font-mono font-medium">{carteirinha || "não informada"}</span>
                    </div>
                    <Button onClick={buscarFotoBiodoc} disabled={buscandoBio || !carteirinha.trim()}>
                      <Search className="mr-2 h-4 w-4" />{buscandoBio ? "Buscando..." : "Buscar foto da Biodoc"}
                    </Button>
                  </div>
                  <p className="text-xs text-zinc-400">
                    A foto retornada será salva automaticamente e usada pelo motor de reconhecimento.
                  </p>
                </div>
              )}
            </TabsContent>

            {/* ── Upload ── */}
            <TabsContent value="upload" className="space-y-4">
              <div
                className={`flex flex-col items-center justify-center gap-2 h-28 rounded-lg border-2 border-dashed border-zinc-200 bg-zinc-50 text-zinc-400 text-sm transition-colors ${dadosSalvos ? "cursor-pointer hover:border-zinc-300 hover:bg-zinc-100" : "opacity-50 cursor-not-allowed"}`}
                onClick={() => dadosSalvos && document.getElementById("foto-upload")?.click()}>
                <Upload className="h-6 w-6" />
                <span>{dadosSalvos ? "Clique para selecionar imagens" : "Salve os dados primeiro"}</span>
                <span className="text-xs">JPG, PNG ou WebP — múltiplas fotos aceitas</span>
              </div>
              <input id="foto-upload" type="file" accept=".jpg,.jpeg,.png,.webp" multiple className="hidden"
                onChange={handleFileUpload} disabled={!dadosSalvos || uploading} />
              {uploading && <p className="text-xs text-zinc-500">Enviando fotos...</p>}
            </TabsContent>
          </Tabs>

          {/* Fotos cadastradas (comum a todas as abas) */}
          {dadosSalvos && fotosExist.length > 0 && (
            <div className="space-y-2 mt-6 pt-4 border-t border-zinc-100">
              <p className="text-sm font-medium text-zinc-600">Fotos cadastradas ({fotosExist.length})</p>
              <div className="grid grid-cols-4 gap-2">
                {fotosExist.map((f, i) => (
                  <div key={i} className="relative group rounded-lg overflow-hidden border border-zinc-200 bg-zinc-50 aspect-square">
                    <img src={`${API}/media/frame?path=${encodeURIComponent(folderPath)}/${encodeURIComponent(f)}`}
                      alt={f} className="w-full h-full object-cover"
                      onError={e => { (e.target as HTMLImageElement).style.opacity = "0.2"; }} />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Button variant="destructive" size="icon" className="h-7 w-7" onClick={() => excluirFoto(f)}>
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                    {f.startsWith("biodoc_") && (
                      <span className="absolute top-1 left-1 bg-green-600 text-white text-xs px-1.5 py-0.5 rounded">Biodoc</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
