"use client";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { getCenario, createCenario, updateCenario, getParametros, getCamerasDisponiveis, getCamerasCenario, addCameraCenario, removeCameraCenario } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { ArrowLeft, Save, AlertCircle, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

function parseParam(p: any) {
  if (Array.isArray(p)) return { id: p[0], nome: p[1] };
  return { id: p.idParametro ?? p.id, nome: p.nomeparametro ?? p.nome ?? p.name };
}
function parseCamera(c: any) {
  if (Array.isArray(c)) return { idcenariocamera: c[0], id: c[1], nome: c[2] };
  return { idcenariocamera: c.idcenariocamera, id: c.idCamera ?? c.id, nome: c.nomeCamera ?? c.nome ?? c.name };
}
function parseCameraDisp(c: any) {
  if (Array.isArray(c)) return { id: c[0], nome: c[1] };
  return { id: c.idCamera ?? c.id, nome: c.nomeCamera ?? c.nome ?? c.name };
}

export default function CenarioFormPage() {
  const router = useRouter();
  const params = useParams();
  const id    = params?.id as string;
  const isNew = id === "novo";

  const [descricao,   setDescricao]   = useState("");
  const [parametroId, setParametroId] = useState("");
  const [ativo,       setAtivo]       = useState(true);
  const [padrao,      setPadrao]      = useState(false);
  const [parametros,  setParametros]  = useState<any[]>([]);
  const [cameras,     setCameras]     = useState<any[]>([]);
  const [camerasDisp, setCamerasDisp] = useState<any[]>([]);
  const [cameraAdd,   setCameraAdd]   = useState("");
  const [cenarioId,   setCenarioId]   = useState<number | null>(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState("");

  async function loadCameras(sid: number) {
    try {
      const data = await getCamerasCenario(sid);
      setCameras(data.map(parseCamera));
    } catch (e: any) { setError(String(e.message ?? e)); }
  }

  async function loadCamerasDisp() {
    try {
      const data = await getCamerasDisponiveis();
      setCamerasDisp(data.map(parseCameraDisp));
    } catch (e: any) { setError(String(e.message ?? e)); }
  }

  useEffect(() => {
    getParametros().then(ps => setParametros(ps.map(parseParam))).catch(() => {});
    loadCamerasDisp();
    if (!isNew) {
      const sid = Number(id);
      setCenarioId(sid);
      getCenario(sid).then(data => {
        setDescricao(data.descricao ?? data.descricaocenario ?? data.description ?? "");
        setParametroId(String(data.idparametro ?? data.parameter_id ?? ""));
        setAtivo(data.ativo ?? data.active ?? true);
        setPadrao(data.padrao ?? data.default ?? false);
      }).catch(e => setError(String(e.message ?? e)));
      loadCameras(sid);
    }
  }, [id]);

  async function salvar() {
    if (!descricao.trim()) { setError("A descrição é obrigatória."); return; }
    if (!parametroId) { setError("Selecione um parâmetro."); return; }
    setLoading(true); setError("");
    try {
      const payload = { descricao, idparametro: Number(parametroId), ativo, padrao };
      let sid = cenarioId;
      if (isNew) {
        const res = await createCenario(payload);
        sid = res.id ?? res.idcenario ?? res.scenario_id;
        if (sid) { setCenarioId(sid); toast.success("Cenário criado! Agora adicione as câmeras."); }
        else { toast.success("Cenário criado!"); router.push("/cenarios"); }
      } else {
        await updateCenario(Number(id), payload);
        toast.success("Cenário atualizado com sucesso!");
        router.push("/cenarios");
      }
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  async function adicionarCamera() {
    if (!cameraAdd || !cenarioId) return;
    try {
      await addCameraCenario(cenarioId, Number(cameraAdd));
      toast.success("Câmera adicionada!");
      setCameraAdd("");
      loadCameras(cenarioId);
    } catch (e: any) { toast.error(String(e.message ?? e)); }
  }

  async function removerCamera(idcenariocamera: number, nomeCam: string) {
    if (!cenarioId) return;
    try {
      await removeCameraCenario(cenarioId, idcenariocamera);
      toast.success(`Câmera "${nomeCam}" removida.`);
      loadCameras(cenarioId);
    } catch (e: any) { toast.error(String(e.message ?? e)); }
  }

  const camerasNaoCadastradas = camerasDisp.filter(cd => !cameras.find(c => c.id === cd.id));

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/cenarios"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">{isNew && !cenarioId ? "Novo Cenário" : "Editar Cenário"}</h1>
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
              <SelectContent>{parametros.map(p => <SelectItem key={p.id} value={String(p.id)}>{p.nome}</SelectItem>)}</SelectContent>
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
            <Save className="mr-2 h-4 w-4" />{loading ? "Salvando..." : isNew && !cenarioId ? "Salvar e adicionar câmeras" : "Salvar"}
          </Button>
        </CardContent>
      </Card>

      {cenarioId && (
        <Card>
          <CardHeader><CardTitle className="text-base">Câmeras do Cenário</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Select value={cameraAdd} onValueChange={setCameraAdd}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder={camerasNaoCadastradas.length === 0 ? "Todas as câmeras já foram adicionadas" : "Selecione uma câmera..."} />
                </SelectTrigger>
                <SelectContent>
                  {camerasNaoCadastradas.map(c => <SelectItem key={c.id} value={String(c.id)}>{c.nome}</SelectItem>)}
                </SelectContent>
              </Select>
              <Button onClick={adicionarCamera} disabled={!cameraAdd}>
                <Plus className="mr-2 h-4 w-4" />Adicionar
              </Button>
            </div>
            {cameras.length === 0 ? (
              <p className="text-sm text-center py-4 text-zinc-400">Nenhuma câmera adicionada ao cenário ainda.</p>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Câmera</TableHead>
                      <TableHead className="w-16 text-right">Remover</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {cameras.map(c => (
                      <TableRow key={c.idcenariocamera}>
                        <TableCell className="font-medium">{c.nome}</TableCell>
                        <TableCell className="text-right">
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="ghost" size="icon" className="text-red-500 hover:text-red-600 hover:bg-red-50"><Trash2 className="h-4 w-4" /></Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader><AlertDialogTitle>Remover câmera</AlertDialogTitle><AlertDialogDescription>Remover <strong>{c.nome}</strong> deste cenário?</AlertDialogDescription></AlertDialogHeader>
                              <AlertDialogFooter><AlertDialogCancel>Cancelar</AlertDialogCancel><AlertDialogAction className="bg-red-600 hover:bg-red-700" onClick={() => removerCamera(c.idcenariocamera, c.nome)}>Remover</AlertDialogAction></AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
