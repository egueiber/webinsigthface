"use client";
import { useState, useEffect, useRef } from "react";
import { getLocalizacoes, getAreaTracking, getToken } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AlertCircle } from "lucide-react";
import { FrameViewer } from "@/components/FrameViewer";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
function today() { return new Date().toISOString().slice(0, 10); }

// Controle do tamanho da janela de frame (modal)
const FRAME_MAX_VW = 95;      // largura quando 100% "maximizado"
const FRAME_MAX_VH = 92;      // altura quando 100% "maximizado"
const FRAME_BASE_SCALE = 70;  // janela inicia com 70% do maximizado

interface Deteccao {
  nome: string; horario: string; data_hora?: string; tempo_marcacao: string;
  nota_comparacao: number; nota_ignorar: number; nota_identificacao: number;
  video_path: string; segundo_marcacao: number;
  pasta_pessoa: string; datahora_ao_vivo: string;
}
interface PessoaAgrupada {
  nome: string; deteccoes: Deteccao[]; primeira: string; ultima: string;
  melhorNota: number; notaIgnorar: number; notaIdentificacao: number;
}

function corNota(nota: number, ignorar: number, identificacao: number) {
  if (nota >= identificacao) return { bg: "#22c55e", border: "#16a34a" };
  if (nota <= ignorar)       return { bg: "#ef4444", border: "#dc2626" };
  return                            { bg: "#f59e0b", border: "#d97706" };
}

const CORES   = ["#3b82f6","#8b5cf6","#ec4899","#14b8a6","#f97316","#06b6d4","#84cc16","#f43f5e","#a855f7","#0ea5e9"];
const OFFSETS = [[50,50],[25,30],[75,30],[25,70],[75,70],[15,50],[85,50],[50,15],[50,82],[38,42]];

// Monta a URL do frame da detecção (mesmo endpoint da tela de Acomp. Pessoa,
// que gera o frame a partir do vídeo de marcação + pasta da pessoa).
function frameUrl(d: Deteccao) {
  const qs = new URLSearchParams({
    video_path: d.video_path,
    person_folder: d.pasta_pessoa,
    datahora_ao_vivo: d.datahora_ao_vivo,
  });
  return `${API}/media/detection-frame?${qs}`;
}
// O frame só existe se tivermos o caminho do vídeo e a pasta da pessoa.
function temFrame(d: Deteccao) {
  return Boolean(d.video_path && d.pasta_pessoa);
}

export default function AcompanhamentoAreaPage() {
  const [localizacoes, setLocalizacoes] = useState<any[]>([]);
  const [locId,  setLocId]    = useState("");
  const [locNome,setLocNome]  = useState("");
  const [data,   setData]     = useState(today());
  const [deteccoes,  setDeteccoes]  = useState<Deteccao[]>([]);
  const [pessoas,    setPessoas]    = useState<PessoaAgrupada[]>([]);
  const [selecionada,setSelecionada]= useState<PessoaAgrupada | null>(null);
  const [tooltip,    setTooltip]    = useState<{x:number;y:number;p:PessoaAgrupada}|null>(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState("");
  const [frameModal, setFrameModal] = useState<Deteccao | null>(null);
  const [frameErro,  setFrameErro]  = useState("");
  // Tamanho/estado da janela de frame
  const [frameScale, setFrameScale] = useState(FRAME_BASE_SCALE);
  const [frameFullscreen, setFrameFullscreen] = useState(false);
  const [mapaUrl,    setMapaUrl]    = useState<string | null>(null);

  useEffect(() => {
    getLocalizacoes().then(locs => {
      const parsed = locs.map((l: any) => Array.isArray(l)
        ? { id: l[0], nome: l[1] }
        : { id: l.idlocalizacao ?? l.id, nome: l.nomelocalizacao ?? l.nome ?? l.name });
      setLocalizacoes(parsed);
      if (parsed[0]) { setLocId(String(parsed[0].id)); setLocNome(parsed[0].nome); }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!locId) {
      setMapaUrl(null);
      return;
    }
    const token = getToken();
    fetch(`${API}/locations/${locId}/mapa`, {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
    })
      .then(res => {
        if (!res.ok) throw new Error("Sem mapa");
        return res.blob();
      })
      .then(blob => setMapaUrl(URL.createObjectURL(blob)))
      .catch(() => setMapaUrl(null));
  }, [locId]);

  const buscaAtual = useRef(0);

  async function buscar(id: string = locId) {
    if (!id) { setError("Selecione uma localização."); return; }
    const reqId = ++buscaAtual.current;
    setLoading(true); setError(""); setDeteccoes([]); setPessoas([]); setSelecionada(null); setTooltip(null);
    try {
      const dados = await getAreaTracking(Number(id), data);
      if (reqId !== buscaAtual.current) return; // resposta de uma busca anterior
      setDeteccoes(dados);
      if (dados.length === 0) { setError("Nenhuma detecção encontrada para essa localização e data."); return; }
      const mapa: Record<string, PessoaAgrupada> = {};
      for (const d of dados) {
        if (!mapa[d.nome]) mapa[d.nome] = { nome: d.nome, deteccoes: [], primeira: d.horario, ultima: d.horario, melhorNota: 0, notaIgnorar: d.nota_ignorar, notaIdentificacao: d.nota_identificacao };
        mapa[d.nome].deteccoes.push(d);
        if (d.horario < mapa[d.nome].primeira) mapa[d.nome].primeira = d.horario;
        if (d.horario > mapa[d.nome].ultima)   mapa[d.nome].ultima   = d.horario;
        if (d.nota_comparacao > mapa[d.nome].melhorNota) mapa[d.nome].melhorNota = d.nota_comparacao;
      }
      setPessoas(Object.values(mapa));
    } catch (e: any) { if (reqId === buscaAtual.current) setError(String(e.message ?? e)); }
    finally { if (reqId === buscaAtual.current) setLoading(false); }
  }

  function abrirFrame(p: Deteccao) {
    setFrameErro("");
    setFrameScale(FRAME_BASE_SCALE);
    setFrameFullscreen(false);
    setFrameModal(p);
  }

  const listaAtiva = selecionada ? selecionada.deteccoes : deteccoes;

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-zinc-800">Acompanhamento por Área</h1>

      <Card><CardContent className="pt-5">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="space-y-1.5 min-w-48">
            <p className="text-sm font-medium text-zinc-700">Localização</p>
            <Select value={locId} onValueChange={v => { setLocId(v); const l = localizacoes.find(x => String(x.id)===v); if(l) setLocNome(l.nome); buscar(v); }}>
              <SelectTrigger><SelectValue placeholder="Selecione..." /></SelectTrigger>
              <SelectContent>{localizacoes.map(l => <SelectItem key={l.id} value={String(l.id)}>{l.nome}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <p className="text-sm font-medium text-zinc-700">Data</p>
            <input type="date" value={data} onChange={e => setData(e.target.value)}
              className="flex h-9 rounded-md border border-zinc-200 bg-white px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-900" />
          </div>
          <Button onClick={() => buscar()} disabled={loading}>{loading ? "Buscando..." : "Buscar"}</Button>
        </div>
      </CardContent></Card>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      {pessoas.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-zinc-600">
                  {locNome} — {data.split("-").reverse().join("/")}
                  <span className="ml-2 text-zinc-400 font-normal">({pessoas.length} pessoa(s))</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative w-full rounded-lg border-2 border-dashed border-zinc-200 bg-zinc-50" style={{height:340}}
                  onClick={() => { setTooltip(null); setSelecionada(null); }}>
                  {mapaUrl ? (
                    <div className="absolute inset-0 bg-contain bg-center bg-no-repeat rounded-lg opacity-80" style={{backgroundImage: `url(${mapaUrl})`}} />
                  ) : (
                    <div className="absolute inset-0 opacity-10" style={{backgroundImage:"linear-gradient(#94a3b8 1px,transparent 1px),linear-gradient(90deg,#94a3b8 1px,transparent 1px)",backgroundSize:"40px 40px"}} />
                  )}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <p className="text-zinc-200 text-4xl font-bold select-none">{locNome}</p>
                  </div>
                  {pessoas.map((p, i) => {
                    const [px, py] = OFFSETS[i % OFFSETS.length];
                    const cor = corNota(p.melhorNota, p.notaIgnorar, p.notaIdentificacao);
                    const isSel = selecionada?.nome === p.nome;
                    return (
                      <div key={p.nome} className="absolute cursor-pointer transition-transform hover:scale-110 z-10"
                        style={{left:`${px}%`,top:`${py}%`,transform:"translate(-50%,-50%)"}}
                        onClick={e => { e.stopPropagation(); setSelecionada(p); setTooltip({x:px,y:py,p}); }}>
                        <div className="flex items-center justify-center rounded-full text-white text-sm font-bold shadow-lg"
                          style={{width:isSel?44:36,height:isSel?44:36,background:CORES[i%CORES.length],border:`3px solid ${cor.border}`,outline:isSel?`3px solid ${CORES[i%CORES.length]}`:"none",outlineOffset:2}}>
                          {p.nome.charAt(0).toUpperCase()}
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white" style={{background:cor.bg}} />
                      </div>
                    );
                  })}
                  {tooltip && (
                    <div className="absolute z-20 bg-white border border-zinc-200 rounded-lg shadow-lg p-3 text-xs min-w-40"
                      style={{left:tooltip.x>70?undefined:`${tooltip.x}%`,right:tooltip.x>70?`${100-tooltip.x}%`:undefined,top:tooltip.y>60?undefined:`${tooltip.y+7}%`,bottom:tooltip.y>60?`${100-tooltip.y+7}%`:undefined}}
                      onClick={e => e.stopPropagation()}>
                      <p className="font-semibold text-zinc-800 mb-1">{tooltip.p.nome}</p>
                      <p className="text-zinc-500">{tooltip.p.deteccoes.length} detecção(ões)</p>
                      <p className="text-zinc-500">Primeira: {tooltip.p.primeira}</p>
                      <p className="text-zinc-500">Última: {tooltip.p.ultima}</p>
                      <p className="text-zinc-500">Melhor nota: {tooltip.p.melhorNota.toFixed(2)}</p>
                    </div>
                  )}
                </div>
                <div className="flex gap-4 mt-3 text-xs text-zinc-500">
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500 inline-block"/>Identificado</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-yellow-500 inline-block"/>Incerto</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500 inline-block"/>Não identificado</span>
                </div>
              </CardContent>
            </Card>
          </div>
          <div className="col-span-1">
            <Card className="h-full">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-zinc-600">
                  {selecionada ? selecionada.nome : "Todas as detecções"}
                  {selecionada && <button className="ml-2 text-xs text-blue-500 underline" onClick={() => { setSelecionada(null); setTooltip(null); }}>ver todas</button>}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0 overflow-auto" style={{maxHeight:380}}>
                <Table>
                  <TableHeader><TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead className="text-center">Horário</TableHead>
                    <TableHead className="text-center">Nota</TableHead>
                    <TableHead className="text-center w-16">Frame</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>
                    {listaAtiva.map((d, i) => {
                      const cor = corNota(d.nota_comparacao, d.nota_ignorar, d.nota_identificacao);
                      return (
                        <TableRow key={i}>
                          <TableCell className="text-xs font-medium py-2">{d.nome}</TableCell>
                          <TableCell className="text-center text-xs font-mono py-2">{d.horario}</TableCell>
                          <TableCell className="text-center py-2">
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium"
                              style={{background:cor.bg+"20",color:cor.border}}>
                              {d.nota_comparacao.toFixed(2)}
                            </span>
                          </TableCell>
                          <TableCell className="text-center py-2">
                            {temFrame(d) ? (
                              <button onClick={() => abrirFrame(d)}
                                className="text-xs text-blue-500 underline hover:text-blue-700">
                                Ver
                              </button>
                            ) : <span className="text-xs text-zinc-300">—</span>}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {!loading && pessoas.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-zinc-400">
          <p className="text-sm">Selecione uma localização e data e clique em Buscar.</p>
        </div>
      )}

      {/* Modal de frame de detecção — tamanho da janela controlado por frameScale */}
      <Dialog open={!!frameModal} onOpenChange={() => { setFrameModal(null); setFrameErro(""); }}>
        <DialogContent
          className="flex flex-col p-0 gap-0 sm:max-w-none"
          style={{
            width: `${(FRAME_MAX_VW * frameScale) / 100}vw`,
            height: `${(FRAME_MAX_VH * frameScale) / 100}vh`,
            maxWidth: `${FRAME_MAX_VW}vw`,
            maxHeight: `${FRAME_MAX_VH}vh`,
            transition: "width 0.15s ease-out, height 0.15s ease-out",
          }}
        >
          <DialogHeader className="px-6 pt-6 pb-2 shrink-0">
            <DialogTitle>Frame da Detecção — {frameModal?.nome}</DialogTitle>
          </DialogHeader>
          {frameModal && (
            <div className="flex flex-col flex-1 min-h-0 px-6 pb-6 gap-3">
              {frameErro ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="text-xs">{frameErro}</AlertDescription>
                </Alert>
              ) : (
                <div className="flex-1 min-h-0">
                  <FrameViewer
                    src={frameUrl(frameModal)}
                    alt={`Frame ${frameModal.nome}`}
                    onError={() => setFrameErro("Não foi possível carregar o frame. O arquivo pode não estar disponível no servidor.")}
                    scale={frameScale}
                    baseScale={FRAME_BASE_SCALE}
                    onScaleChange={setFrameScale}
                    fullscreen={frameFullscreen}
                    onFullscreenChange={setFrameFullscreen}
                  />
                </div>
              )}
              <div className="grid grid-cols-2 gap-2 text-xs text-zinc-600 shrink-0">
                <span><strong>Nome:</strong> {frameModal.nome}</span>
                <span><strong>Horário:</strong> {frameModal.horario}</span>
                <span><strong>Nota:</strong> {frameModal.nota_comparacao.toFixed(2)}</span>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
