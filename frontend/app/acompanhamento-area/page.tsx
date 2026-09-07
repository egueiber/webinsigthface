"use client";
import { useState, useEffect } from "react";
import { getLocalizacoes, getAreaTracking, getToken } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AlertCircle, X, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
function today() { return new Date().toISOString().slice(0, 10); }

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
  const [mapaUrl,    setMapaUrl]    = useState<string | null>(null);

  // Estados de Zoom/Pan para o modal
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

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

  async function buscar() {
    if (!locId) { setError("Selecione uma localização."); return; }
    setLoading(true); setError(""); setDeteccoes([]); setPessoas([]); setSelecionada(null); setTooltip(null);
    try {
      const dados = await getAreaTracking(Number(locId), data);
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
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  const listaAtiva = selecionada ? selecionada.deteccoes : deteccoes;

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-zinc-800">Acompanhamento por Área</h1>

      <Card><CardContent className="pt-5">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="space-y-1.5 min-w-48">
            <p className="text-sm font-medium text-zinc-700">Localização</p>
            <Select value={locId} onValueChange={v => { setLocId(v); const l = localizacoes.find(x => String(x.id)===v); if(l) setLocNome(l.nome); }}>
              <SelectTrigger><SelectValue placeholder="Selecione..." /></SelectTrigger>
              <SelectContent>{localizacoes.map(l => <SelectItem key={l.id} value={String(l.id)}>{l.nome}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <p className="text-sm font-medium text-zinc-700">Data</p>
            <input type="date" value={data} onChange={e => setData(e.target.value)}
              className="flex h-9 rounded-md border border-zinc-200 bg-white px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-900" />
          </div>
          <Button onClick={buscar} disabled={loading}>{loading ? "Buscando..." : "Buscar"}</Button>
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
                              <button onClick={() => { setFrameErro(""); setFrameModal(d); }}
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

      {/* Modal de frame de detecção */}
      <Dialog open={!!frameModal} onOpenChange={(open) => { 
        if (!open) { setFrameModal(null); setFrameErro(""); setZoom(1); setPan({x:0, y:0}); }
      }}>
        <DialogContent 
          className="select-none" 
          style={{ 
            maxWidth: `min(90vw, ${672 + (zoom - 1) * 300}px)`, 
            transition: 'max-width 0.15s ease-out' 
          }}
        >
          <DialogHeader>
            <DialogTitle>Frame de Detecção — {frameModal?.nome}</DialogTitle>
          </DialogHeader>
          {frameModal && (
            <div className="space-y-3">
              {frameErro ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="text-xs">{frameErro}</AlertDescription>
                </Alert>
              ) : (
                <div className="relative group">
                  <div 
                    className="w-full rounded-lg border border-zinc-200 bg-black/5 overflow-hidden cursor-move touch-none"
                    style={{
                      height: `min(75vh, ${400 + (zoom - 1) * 200}px)`,
                      transition: isDragging ? 'none' : 'height 0.15s ease-out'
                    }}
                    onWheel={(e) => {
                      e.preventDefault();
                      setZoom(z => Math.min(Math.max(1, z - e.deltaY * 0.01), 6));
                    }}
                    onMouseDown={(e) => {
                      setIsDragging(true);
                      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
                    }}
                    onMouseMove={(e) => {
                      if (!isDragging) return;
                      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
                    }}
                    onMouseUp={() => setIsDragging(false)}
                    onMouseLeave={() => setIsDragging(false)}
                  >
                    <img
                      src={frameUrl(frameModal)}
                      alt={`Frame de ${frameModal.nome}`}
                      className="w-full h-full object-contain pointer-events-none"
                      style={{
                        transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
                        transition: isDragging ? 'none' : 'transform 0.1s ease-out',
                        transformOrigin: 'center center'
                      }}
                      draggable={false}
                      onError={() => setFrameErro("Não foi possível carregar o frame. O arquivo pode não estar disponível no servidor.")}
                    />
                  </div>
                  <div className="absolute bottom-3 right-3 flex items-center bg-white/90 backdrop-blur-sm rounded-lg shadow-md border border-zinc-200 overflow-hidden opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => setZoom(z => Math.min(z + 0.5, 6))} className="p-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 transition-colors" title="Aproximar"><ZoomIn size={18}/></button>
                    <button onClick={() => setZoom(z => Math.max(z - 0.5, 1))} className="p-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 border-l border-zinc-200 transition-colors" title="Afastar"><ZoomOut size={18}/></button>
                    <button onClick={() => { setZoom(1); setPan({x:0, y:0}); }} className="p-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 border-l border-zinc-200 transition-colors" title="Restaurar zoom"><RotateCcw size={18}/></button>
                  </div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-2 text-xs text-zinc-600">
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
