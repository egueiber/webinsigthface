"use client";
import { useState, useEffect } from "react";
import { getPessoas, getPersonPath } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { AlertCircle } from "lucide-react";

function today()     { return new Date().toISOString().slice(0, 10); }
function yesterday() { const d = new Date(); d.setDate(d.getDate()-1); return d.toISOString().slice(0,10); }

interface Passo {
  ordem: number; horario: string; camera: string;
  andar: number; sala: number; video_path: string; segundo_marcacao: number;
}

export default function AcompanhamentoPessoaPage() {
  const [pessoas,    setPessoas]    = useState<any[]>([]);
  const [pessoaId,   setPessoaId]   = useState("");
  const [dataInicio, setDataInicio] = useState(yesterday());
  const [dataFim,    setDataFim]    = useState(today());
  const [identified, setIdentified] = useState(true);
  const [caminho,    setCaminho]    = useState<Passo[]>([]);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState("");

  useEffect(() => {
    getPessoas().then(locs => {
      const parsed = locs.map((p: any) => Array.isArray(p)
        ? { id: p[0], nome: p[1] }
        : { id: p.idPessoa ?? p.id, nome: p.nomePessoa ?? p.nome ?? p.name });
      setPessoas(parsed);
    }).catch(() => {});
  }, []);

  async function buscar() {
    if (!pessoaId) { setError("Selecione uma pessoa."); return; }
    setLoading(true); setError(""); setCaminho([]);
    try {
      const dados = await getPersonPath(Number(pessoaId), dataInicio, dataFim, identified);
      if (dados.length === 0) {
        setError("Nenhum registro encontrado. Verifique se o motor de reconhecimento processou vídeos para essa pessoa no período selecionado.");
        return;
      }
      setCaminho(dados);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  const pessoa = pessoas.find(p => String(p.id) === pessoaId);

  const camerasUnicas = caminho.reduce((acc, p) => {
    const key = `${p.andar}-${p.camera}`;
    const existing = acc.find(c => c.key === key);
    if (!existing) acc.push({ key, camera: p.camera, andar: p.andar, sala: p.sala, passagens: 1 });
    else existing.passagens++;
    return acc;
  }, [] as {key:string;camera:string;andar:number;sala:number;passagens:number}[]);

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-zinc-800">Acompanhamento por Pessoa</h1>

      <Card><CardContent className="pt-5">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="space-y-1.5 min-w-48">
            <p className="text-sm font-medium text-zinc-700">Pessoa</p>
            <Select value={pessoaId} onValueChange={setPessoaId}>
              <SelectTrigger><SelectValue placeholder="Selecione..." /></SelectTrigger>
              <SelectContent>{pessoas.map(p => <SelectItem key={p.id} value={String(p.id)}>{p.nome}</SelectItem>)}</SelectContent>
            </Select>
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
                  Caminhamento — {pessoa?.nome}
                  <span className="ml-2 text-zinc-400 font-normal">({caminho.length} passagem(ns))</span>
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
                      return (
                        <div key={i} className="relative flex gap-4 items-start pl-2">
                          <div className={`relative z-10 flex items-center justify-center rounded-full shrink-0 mt-3 ${isFirst || isLast ? "w-5 h-5" : "w-3 h-3 ml-1"}`}
                            style={{background: isFirst ? "#3b82f6" : isLast ? "#22c55e" : mudouCamera ? "#8b5cf6" : "#e2e8f0",border: isFirst||isLast ? "2px solid white" : "2px solid #cbd5e1",boxShadow: isFirst||isLast ? `0 0 0 3px ${isFirst?"#bfdbfe":"#bbf7d0"}` : "none"}} />
                          <div className={`flex-1 rounded-lg border px-3 py-2 mb-1 ${mudouCamera ? "border-purple-200 bg-purple-50" : "border-zinc-100 bg-white"}`}>
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium text-zinc-800">{p.camera}</span>
                              <span className="text-xs font-mono text-zinc-400">{p.horario}</span>
                            </div>
                            <div className="flex gap-3 mt-0.5 text-xs text-zinc-500">
                              {p.andar !== 0 && <span>Andar {p.andar}</span>}
                              {p.sala  !== 0 && <span>Sala {p.sala}</span>}
                              {mudouCamera && <span className="text-purple-500 font-medium">nova câmera</span>}
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
                    <TableHead className="text-center">Horário</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>
                    {caminho.map((p, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-xs text-zinc-400 py-2">{p.ordem}</TableCell>
                        <TableCell className="text-xs font-medium py-2">{p.camera}</TableCell>
                        <TableCell className="text-center text-xs font-mono py-2">{p.horario}</TableCell>
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
          <p className="text-sm">Selecione uma pessoa e o período e clique em Gerar caminhamento.</p>
        </div>
      )}
    </div>
  );
}
