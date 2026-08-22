"use client";
import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { getPessoas, getPersonPath } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { AlertCircle, Search, X, Check, Maximize2 } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
function today()     { return new Date().toISOString().slice(0, 10); }
function yesterday() { const d = new Date(); d.setDate(d.getDate()-1); return d.toISOString().slice(0,10); }

interface Passo {
  ordem: number;
  horario: string;
  data: string;
  data_hora: string;
  camera: string;
  andar: number;
  sala: number;
  video_path: string;
  segundo_marcacao: number;
  pasta_pessoa: string;
  datahora_ao_vivo: string;
}

function parsePessoa(p: any) {
  return Array.isArray(p)
    ? { id: p[0], nome: p[1] }
    : { id: p.idPessoa ?? p.id, nome: p.nomePessoa ?? p.nome ?? p.name };
}

// Monta a URL do frame da deteccao
function frameUrl(p: Passo) {
  const qs = new URLSearchParams({
    video_path: p.video_path,
    person_folder: p.pasta_pessoa,
    datahora_ao_vivo: p.datahora_ao_vivo,
  });
  return `${API}/media/detection-frame?${qs}`;
}

// O frame so existe se tivermos o caminho do video e a pasta da pessoa
function temFrame(p: Passo) {
  return Boolean(p.video_path && p.pasta_pessoa);
}

export default function AcompanhamentoPessoaPage() {
  const searchParams = useSearchParams();
  const [pessoaId,   setPessoaId]   = useState("");
  const [pessoaNome, setPessoaNome] = useState("");
  const [dataInicio, setDataInicio] = useState(yesterday());
  const [dataFim,    setDataFim]    = useState(today());
  const [identified, setIdentified] = useState(true);
  const [caminho,    setCaminho]    = useState<Passo[]>([]);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState("");
  const [frameModal, setFrameModal] = useState<Passo | null>(null);
  const [frameErro,  setFrameErro]  = useState("");
  const [frameCheio, setFrameCheio] = useState(false);

  // Busca de pessoa (autocomplete)
  const [termo,       setTermo]       = useState("");
  const [resultados,  setResultados]  = useState<any[]>([]);
  const [buscandoP,   setBuscandoP]   = useState(false);
  const [showResults, setShowResults] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const boxRef      = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) {
        setShowResults(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (pessoaId && termo === pessoaNome) return;
    if (!termo.trim()) { setResultados([]); return; }

    debounceRef.current = setTimeout(async () => {
      setBuscandoP(true);
      try {
        const res = await getPessoas(termo.trim());
        setResultados(res.map(parsePessoa));
        setShowResults(true);
      } catch { setResultados([]); }
      finally { setBuscandoP(false); }
    }, 300);

    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [termo]);

  function selecionarPessoa(p: any) {
    setPessoaId(String(p.id));
    setPessoaNome(p.nome);
    setTermo(p.nome);
    setShowResults(false);
  }

  function limparPessoa() {
    setPessoaId(""); setPessoaNome(""); setTermo(""); setResultados([]);
  }

  // Chegando do Dashboard (ou outro link) com ?pessoa=ID&nome=Fulano:
  // pré-seleciona a pessoa e já dispara o caminhamento, sem o usuário
  // precisar buscar de novo. Roda uma vez, na montagem.
  useEffect(() => {
    const pid = searchParams.get("pessoa");
    if (!pid) return;
    const pnome = searchParams.get("nome") ?? "";
    setPessoaId(pid);
    setPessoaNome(pnome);
    setTermo(pnome);
    (async () => {
      setLoading(true); setError(""); setCaminho([]);
      try {
        const dados = await getPersonPath(Number(pid), dataInicio, dataFim, identified);
        if (!dados || dados.length === 0) {
          setError("Nenhum registro encontrado para os filtros selecionados.");
          return;
        }
        setCaminho(dados);
      } catch (e: any) { setError(String(e.message ?? e)); }
      finally { setLoading(false); }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function buscar() {
    if (!pessoaId) { setError("Selecione uma pessoa."); return; }
    setLoading(true); setError(""); setCaminho([]);
    try {
      const dados = await getPersonPath(Number(pessoaId), dataInicio, dataFim, identified);
      if (dados.length === 0) { setError("Nenhum registro encontrado para os filtros selecionados."); return; }
      setCaminho(dados);
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  function abrirFrame(p: Passo) {
    setFrameErro("");
    setFrameCheio(false);
    setFrameModal(p);
  }

  // Fecha a tela cheia com Esc (sem fechar o modal inteiro).
  useEffect(() => {
    if (!frameCheio) return;
    function onKey(e: KeyboardEvent) { if (e.key === "Escape") setFrameCheio(false); }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [frameCheio]);

  const camerasUnicas = caminho.reduce((acc, p) => {
    const key = `${p.andar}-${p.camera}`;
    const existing = acc.find(c => c.key === key);
    if (!existing) acc.push({ key, camera: p.camera, andar: p.andar, sala: p.sala, passagens: 1 });
    else existing.passagens++;
    return acc;
  }, [] as {key:string;camera:string;andar:number;sala:number;passagens:number}[]);

  // Datas distintas no resultado (para o resumo)
  const datasUnicas = Array.from(new Set(caminho.map(p => p.data).filter(Boolean)));

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-zinc-800">Acompanhamento por Pessoa</h1>

      <Card><CardContent className="pt-5">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="space-y-1.5 min-w-64" ref={boxRef}>
            <p className="text-sm font-medium text-zinc-700">Pessoa</p>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
              <Input
                value={termo}
                onChange={e => { setTermo(e.target.value); if (pessoaId) { setPessoaId(""); setPessoaNome(""); } }}
                onFocus={() => { if (resultados.length > 0) setShowResults(true); }}
                placeholder="Digite o nome da pessoa..."
                className="pl-9 pr-9"
              />
              {pessoaId ? (
                <Check className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-green-600" />
              ) : termo ? (
                <button onClick={limparPessoa} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600">
                  <X className="h-4 w-4" />
                </button>
              ) : null}

              {showResults && (
                <div className="absolute z-30 mt-1 w-full bg-white border border-zinc-200 rounded-md shadow-lg max-h-60 overflow-auto">
                  {buscandoP ? (
                    <div className="px-3 py-2 text-sm text-zinc-400">Buscando...</div>
                  ) : resultados.length === 0 ? (
                    <div className="px-3 py-2 text-sm text-zinc-400">Nenhuma pessoa encontrada.</div>
                  ) : (
                    resultados.map(p => (
                      <button key={p.id} onClick={() => selecionarPessoa(p)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-zinc-100 transition-colors">
                        {p.nome}
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-1.5">
            <p className="text-sm font-medium text-zinc-700">Data início</p>
            <input type="date" value={dataInicio} onChange={e => setDataInicio(e.target.value)}
              className="flex h-9 rounded-md border border-zinc-200 bg-white px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-900" />
          </div>
          <div className="space-y-1.5">
            <p className="text-sm font-medium text-zinc-700">Data fim</p>
            <input type="date" value={dataFim} onChange={e => setDataFim(e.target.value)}
              className="flex h-9 rounded-md border border-zinc-200 bg-white px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-900" />
          </div>
          <div className="flex items-center gap-2 pb-1">
            <Checkbox id="identified" checked={identified} onCheckedChange={v => setIdentified(!!v)} />
            <Label htmlFor="identified" className="cursor-pointer text-sm">Somente identificadas</Label>
          </div>
          <Button onClick={buscar} disabled={loading}>{loading ? "Buscando..." : "Gerar caminhamento"}</Button>
        </div>
      </CardContent></Card>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      {caminho.length > 0 && (
        <div className="grid grid-cols-5 gap-4">
          <div className="col-span-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-zinc-600">
                  Caminhamento — {pessoaNome}
                  <span className="ml-2 text-zinc-400 font-normal">
                    ({caminho.length} passagem(ns)
                    {datasUnicas.length > 1 ? ` em ${datasUnicas.length} dias` : ""})
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative">
                  <div className="absolute left-5 top-4 bottom-4 w-0.5 bg-zinc-200" />
                  <div className="space-y-0">
                    {caminho.map((p, i) => {
                      const isFirst = i === 0;
                      const isLast  = i === caminho.length - 1;
                      const mudouCamera = i > 0 && caminho[i-1].camera !== p.camera;
                      const mudouDia = i > 0 && caminho[i-1].data !== p.data;
                      return (
                        <div key={i}>
                          {/* Separador quando muda o dia */}
                          {mudouDia && (
                            <div className="flex items-center gap-2 my-2 pl-2">
                              <div className="h-px flex-1 bg-zinc-200" />
                              <span className="text-xs font-medium text-zinc-500 bg-zinc-100 px-2 py-0.5 rounded">
                                {p.data}
                              </span>
                              <div className="h-px flex-1 bg-zinc-200" />
                            </div>
                          )}
                          <div className="relative flex gap-4 items-start pl-2">
                            <div className={`relative z-10 flex items-center justify-center rounded-full shrink-0 mt-3 ${isFirst || isLast ? "w-5 h-5" : "w-3 h-3 ml-1"}`}
                              style={{background: isFirst ? "#3b82f6" : isLast ? "#22c55e" : mudouCamera ? "#8b5cf6" : "#e2e8f0",border: isFirst||isLast ? "2px solid white" : "2px solid #cbd5e1",boxShadow: isFirst||isLast ? `0 0 0 3px ${isFirst?"#bfdbfe":"#bbf7d0"}` : "none"}} />
                            <div className={`flex-1 rounded-lg border px-3 py-2 mb-1 ${mudouCamera ? "border-purple-200 bg-purple-50" : "border-zinc-100 bg-white"}`}>
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-zinc-800">{p.camera}</span>
                                <div className="flex items-center gap-2">
                                  <span className="text-xs font-mono text-zinc-400">{p.data_hora}</span>
                                  {temFrame(p) && (
                                    <button onClick={() => abrirFrame(p)}
                                      className="text-xs text-blue-500 underline hover:text-blue-700">
                                      Ver frame
                                    </button>
                                  )}
                                </div>
                              </div>
                              <div className="flex gap-3 mt-0.5 text-xs text-zinc-500">
                                {p.andar !== 0 && <span>Andar {p.andar}</span>}
                                {p.sala  !== 0 && <span>Sala {p.sala}</span>}
                                {mudouCamera && <span className="text-purple-500 font-medium">nova câmera</span>}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
                {camerasUnicas.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-zinc-100">
                    <p className="text-xs font-medium text-zinc-500 mb-2">Câmeras visitadas ({camerasUnicas.length})</p>
                    <div className="flex flex-wrap gap-2">
                      {camerasUnicas.map(c => (
                        <span key={c.key} className="inline-flex items-center gap-1 px-2 py-1 bg-zinc-100 rounded-md text-xs text-zinc-700">
                          {c.camera}
                          <span className="bg-zinc-300 text-zinc-600 rounded-full w-4 h-4 flex items-center justify-center text-xs">{c.passagens}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
          <div className="col-span-2">
            <Card className="h-full">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-zinc-600">Registros detalhados</CardTitle>
              </CardHeader>
              <CardContent className="p-0 overflow-auto" style={{maxHeight:500}}>
                <Table>
                  <TableHeader><TableRow>
                    <TableHead className="w-6">#</TableHead>
                    <TableHead>Câmera</TableHead>
                    <TableHead className="text-center">Data / Hora</TableHead>
                    <TableHead className="text-center w-16">Frame</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>
                    {caminho.map((p, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-xs text-zinc-400 py-2">{p.ordem}</TableCell>
                        <TableCell className="text-xs font-medium py-2">{p.camera}</TableCell>
                        <TableCell className="text-center py-2">
                          <div className="text-xs font-mono leading-tight">
                            <div className="text-zinc-500">{p.data}</div>
                            <div className="text-zinc-800">{p.horario}</div>
                          </div>
                        </TableCell>
                        <TableCell className="text-center py-2">
                          {temFrame(p) ? (
                            <button onClick={() => abrirFrame(p)}
                              className="text-xs text-blue-500 underline hover:text-blue-700">
                              Ver
                            </button>
                          ) : <span className="text-xs text-zinc-300">—</span>}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {!loading && caminho.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-zinc-400">
          <p className="text-sm">Busque uma pessoa e o período e clique em Gerar caminhamento.</p>
        </div>
      )}

      {/* Modal de frame de deteccao */}
      <Dialog open={!!frameModal} onOpenChange={() => { setFrameModal(null); setFrameErro(""); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Frame da Detecção — {frameModal?.camera}</DialogTitle>
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
                  <img
                    src={frameUrl(frameModal)}
                    alt={`Frame ${frameModal.camera}`}
                    className="w-full rounded-lg border border-zinc-200 cursor-zoom-in"
                    onClick={() => setFrameCheio(true)}
                    onError={() => setFrameErro("Não foi possível carregar o frame. O arquivo pode não estar disponível no servidor.")}
                  />
                  {/* Botão translúcido de zoom (tela cheia) */}
                  <button
                    type="button"
                    onClick={() => setFrameCheio(true)}
                    title="Ampliar (tela cheia)"
                    className="absolute top-2 right-2 flex items-center justify-center h-9 w-9 rounded-full bg-black/40 text-white backdrop-blur-sm hover:bg-black/60 transition-colors"
                  >
                    <Maximize2 className="h-4 w-4" />
                  </button>
                </div>
              )}
              <div className="grid grid-cols-2 gap-2 text-xs text-zinc-600">
                <span><strong>Câmera:</strong> {frameModal.camera}</span>
                <span><strong>Data/Hora:</strong> {frameModal.data_hora}</span>
                {frameModal.andar !== 0 && <span><strong>Andar:</strong> {frameModal.andar}</span>}
                {frameModal.sala  !== 0 && <span><strong>Sala:</strong> {frameModal.sala}</span>}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Overlay de tela cheia: clicar em qualquer lugar (ou Esc) fecha */}
      {frameCheio && frameModal && !frameErro && (
        <div
          className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-4 cursor-zoom-out"
          onClick={() => setFrameCheio(false)}
        >
          <img
            src={frameUrl(frameModal)}
            alt={`Frame ${frameModal.camera}`}
            className="max-w-full max-h-full object-contain select-none"
          />
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setFrameCheio(false); }}
            title="Fechar (Esc)"
            className="absolute top-4 right-4 flex items-center justify-center h-11 w-11 rounded-full bg-white/15 text-white backdrop-blur-sm hover:bg-white/30 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
      )}
    </div>
  );
}
