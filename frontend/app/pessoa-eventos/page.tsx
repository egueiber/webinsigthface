"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { getPessoaEventos, deletePessoaEvento } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Plus, Search, Pencil, Trash2, AlertCircle, ChevronUp, ChevronDown, ChevronsUpDown, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function fmt(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

// O backend devolve tb_pessoa_evento como tupla posicional (sem RealDictCursor).
// Ordem de list_person_events(): idpessoaevento, nomePessoa, nomeevento,
// datahoraentrada, datahoraprevistasaida, datahoraefetivasaida, eventocancelado, idpessoa, idevento
function parseItem(p: any) {
  if (Array.isArray(p)) {
    return {
      id: p[0], nome_pessoa: p[1], nome_evento: p[2],
      entrada: p[3], saida_prevista: p[4], saida_efetiva: p[5], cancelado: p[6],
      pessoa_id: p[7]
    };
  }
  return {
    id: p.id ?? p.idpessoaevento,
    nome_pessoa: p.nome_pessoa ?? p.nomePessoa,
    nome_evento: p.nome_evento ?? p.nomeevento,
    entrada: p.entrada ?? p.datahoraentrada,
    saida_prevista: p.saida_prevista ?? p.datahoraprevistasaida,
    saida_efetiva: p.saida_efetiva ?? p.datahoraefetivasaida,
    cancelado: p.cancelado ?? p.eventocancelado,
    pessoa_id: p.pessoa_id ?? p.idpessoa
  };
}

type SortDir = "asc" | "desc";
function SortIcon({ field, sf, sd }: { field: string; sf: string; sd: SortDir }) {
  if (sf !== field) return <ChevronsUpDown className="ml-1 h-3 w-3 inline opacity-40" />;
  return sd === "asc" ? <ChevronUp className="ml-1 h-3 w-3 inline" /> : <ChevronDown className="ml-1 h-3 w-3 inline" />;
}

function PessoaEventosContent() {
  const searchParams = useSearchParams();
  const pessoaIdParam = searchParams.get("pessoa");
  const readOnly = !!pessoaIdParam;
  const pessoaId = pessoaIdParam ? parseInt(pessoaIdParam, 10) : null;

  const [items,        setItems]        = useState<any[]>([]);
  const [filtro,       setFiltro]       = useState("");
  const [campoBusca,   setCampoBusca]   = useState("nome_pessoa");
  const [filtroStatus, setFiltroStatus] = useState("todos");
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState("");
  const [sf, setSf] = useState("entrada");
  const [sd, setSd] = useState<SortDir>("desc");

  async function carregar() {
    setLoading(true); setError("");
    try {
      const data = await getPessoaEventos();
      let parsedData = (data ?? []).map(parseItem);
      
      // Filter by pessoaId if readOnly mode is active
      if (pessoaId) {
        parsedData = parsedData.filter(p => p.pessoa_id === pessoaId);
      }
      
      setItems(parsedData);
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  useEffect(() => { carregar(); }, [pessoaIdParam]);

  function toggleSort(field: string) {
    if (sf === field) setSd(d => d === "asc" ? "desc" : "asc");
    else { setSf(field); setSd("asc"); }
  }

  const filtered = items
    .filter(p => {
      const val = (p[campoBusca] ?? "").toString().toLowerCase();
      return val.includes(filtro.toLowerCase());
    })
    .filter(p => {
      if (filtroStatus === "andamento") return !p.cancelado && !p.saida_efetiva;
      if (filtroStatus === "concluido") return !!p.saida_efetiva;
      if (filtroStatus === "cancelado") return p.cancelado;
      return true;
    });

  const sorted = [...filtered].sort((a, b) => {
    const av = a[sf] ?? "";
    const bv = b[sf] ?? "";
    const cmp = String(av).localeCompare(String(bv), "pt-BR");
    return sd === "asc" ? cmp : -cmp;
  });

  async function excluir(id: number, nome: string) {
    try {
      await deletePessoaEvento(id);
      toast.success(`Registro de "${nome}" excluído.`);
      carregar();
    } catch (e: any) { toast.error(String(e.message ?? e)); }
  }

  const th = "cursor-pointer select-none hover:bg-zinc-50";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {readOnly && (
            <Button variant="ghost" size="icon" asChild title="Voltar para Pessoas">
              <Link href="/pessoas"><ArrowLeft className="h-5 w-5" /></Link>
            </Button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-zinc-800">Pessoa — Eventos</h1>
            <p className="text-sm text-zinc-500 mt-1">Associe pessoas a eventos para alimentar o Dashboard.</p>
          </div>
        </div>
        {!readOnly && (
          <Button asChild><Link href="/pessoa-eventos/novo"><Plus className="mr-2 h-4 w-4" />Novo Registro</Link></Button>
        )}
      </div>

      <div className="flex gap-2 flex-wrap">
        {!readOnly && (
          <Select value={campoBusca} onValueChange={setCampoBusca}>
            <SelectTrigger className="w-44"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="nome_pessoa">Pessoa</SelectItem>
              <SelectItem value="nome_evento">Evento</SelectItem>
            </SelectContent>
          </Select>
        )}
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input value={filtro} onChange={e => setFiltro(e.target.value)} placeholder={`Buscar por ${readOnly ? "evento" : campoBusca === "nome_pessoa" ? "pessoa" : "evento"}...`} className="pl-9" />
        </div>
        <Select value={filtroStatus} onValueChange={setFiltroStatus}>
          <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos</SelectItem>
            <SelectItem value="andamento">Em andamento</SelectItem>
            <SelectItem value="concluido">Concluídos</SelectItem>
            <SelectItem value="cancelado">Cancelados</SelectItem>
          </SelectContent>
        </Select>
        {filtro && <Button variant="ghost" onClick={() => setFiltro("")}>Limpar</Button>}
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              {!readOnly && <TableHead className={th} onClick={() => toggleSort("nome_pessoa")}>Pessoa <SortIcon field="nome_pessoa" sf={sf} sd={sd} /></TableHead>}
              <TableHead className={th} onClick={() => toggleSort("nome_evento")}>Evento <SortIcon field="nome_evento" sf={sf} sd={sd} /></TableHead>
              <TableHead className={`text-center ${th}`} onClick={() => toggleSort("entrada")}>Entrada <SortIcon field="entrada" sf={sf} sd={sd} /></TableHead>
              <TableHead className="text-center">Saída prevista</TableHead>
              <TableHead className="text-center">Saída efetiva</TableHead>
              <TableHead className="text-center">Status</TableHead>
              {!readOnly && <TableHead className="w-24 text-right">Ações</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={readOnly ? 6 : 7} className="text-center py-10 text-zinc-400">Carregando...</TableCell></TableRow>
            ) : sorted.length === 0 ? (
              <TableRow><TableCell colSpan={readOnly ? 6 : 7} className="text-center py-10 text-zinc-400">Nenhum registro encontrado.</TableCell></TableRow>
            ) : sorted.map((p) => {
              const status = p.cancelado ? "destructive" : p.saida_efetiva ? "default" : "secondary";
              const statusLabel = p.cancelado ? "Cancelado" : p.saida_efetiva ? "Concluído" : "Em andamento";
              return (
                <TableRow key={p.id}>
                  {!readOnly && <TableCell className="font-medium">{p.nome_pessoa}</TableCell>}
                  <TableCell className="text-zinc-600">{p.nome_evento}</TableCell>
                  <TableCell className="text-center text-xs font-mono">{fmt(p.entrada)}</TableCell>
                  <TableCell className="text-center text-xs font-mono">{fmt(p.saida_prevista)}</TableCell>
                  <TableCell className="text-center text-xs font-mono">{fmt(p.saida_efetiva)}</TableCell>
                  <TableCell className="text-center"><Badge variant={status as any}>{statusLabel}</Badge></TableCell>
                  {!readOnly && (
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" asChild><Link href={`/pessoa-eventos/${p.id}`}><Pencil className="h-4 w-4" /></Link></Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild><Button variant="ghost" size="icon" className="text-red-500 hover:text-red-600 hover:bg-red-50"><Trash2 className="h-4 w-4" /></Button></AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader><AlertDialogTitle>Confirmar exclusão</AlertDialogTitle><AlertDialogDescription>Excluir o registro de <strong>{p.nome_pessoa}</strong> no evento <strong>{p.nome_evento}</strong>?</AlertDialogDescription></AlertDialogHeader>
                            <AlertDialogFooter><AlertDialogCancel>Cancelar</AlertDialogCancel><AlertDialogAction className="bg-red-600 hover:bg-red-700" onClick={() => excluir(p.id, p.nome_pessoa)}>Excluir</AlertDialogAction></AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
      <p className="text-xs text-zinc-400">{sorted.length} registro(s) encontrado(s)</p>
    </div>
  );
}

export default function PessoaEventosPage() {
  return (
    <Suspense fallback={<div>Carregando eventos...</div>}>
      <PessoaEventosContent />
    </Suspense>
  );
}
