"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { getPessoas, deletePessoa, getPessoaEventos, updatePessoaEvento } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Plus, Search, Pencil, Trash2, AlertCircle, ChevronUp, ChevronDown, ChevronsUpDown, CalendarPlus, LogOut, List } from "lucide-react";
import { toast } from "sonner";

function parsePessoa(p: any) {
  if (Array.isArray(p)) return { id: p[0], nome: p[1], documento: p[2] };
  return { id: p.idPessoa ?? p.id, nome: p.nomePessoa ?? p.nome ?? p.name, documento: p.documentoPessoa ?? p.documento ?? p.document };
}

function pad(n: number) { return String(n).padStart(2, "0"); }
// Hora local "crua", sem passar por UTC (o banco usa timestamp without time zone).
function toLocal(value: string | Date | null): string {
  if (!value) return "";
  const d = typeof value === "string" ? new Date(value) : value;
  if (isNaN(d.getTime())) return "";
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function toISO(val: string): string | null { return val ? `${val}:00` : null; }
function fmt(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

type SortField = "id" | "nome" | "documento";
type SortDir = "asc" | "desc" | null;

function SortIcon({ field, sortField, sortDir }: { field: string; sortField: string; sortDir: SortDir }) {
  if (sortField !== field) return <ChevronsUpDown className="ml-1 h-3 w-3 inline opacity-40" />;
  return sortDir === "asc" ? <ChevronUp className="ml-1 h-3 w-3 inline" /> : <ChevronDown className="ml-1 h-3 w-3 inline" />;
}

export default function PessoasPage() {
  const [pessoas,   setPessoas]   = useState<any[]>([]);
  const [abertos,   setAbertos]   = useState<Record<number, any>>({}); // pessoa_id -> evento em andamento
  const [filtro,    setFiltro]    = useState("");
  const [campoBusca, setCampoBusca] = useState("nome");
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState("");
  const [sortField, setSortField] = useState<SortField>("nome");
  const [sortDir,   setSortDir]   = useState<SortDir>("asc");

  // Modal de encerramento
  const [encerrando,  setEncerrando]  = useState<any>(null); // { pessoa, evento }
  const [modoSaida,   setModoSaida]   = useState<"agora" | "manual">("agora");
  const [saidaManual, setSaidaManual] = useState("");
  const [salvandoEnc, setSalvandoEnc] = useState(false);

  async function carregar(valor = "") {
    setLoading(true); setError("");
    try {
      const nome = campoBusca === "nome" ? valor : "";
      const doc  = campoBusca === "documento" ? valor : "";
      const res  = await getPessoas(nome);
      let data   = res.map(parsePessoa);
      if (doc) data = data.filter(p => (p.documento ?? "").toLowerCase().includes(doc.toLowerCase()));
      setPessoas(data);
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  // Carrega os pessoa-eventos para saber quem tem entrada em aberto.
  // Falha aqui não quebra a listagem: só deixa os botões de encerrar desabilitados.
  async function carregarAbertos() {
    try {
      const evts = await getPessoaEventos();
      const map: Record<number, any> = {};
      for (const e of evts ?? []) {
        if (!e.saida_efetiva && !e.cancelado && e.pessoa_id != null) {
          // list_person_events já vem ordenado por entrada DESC: fica o mais recente
          if (!map[e.pessoa_id]) map[e.pessoa_id] = e;
        }
      }
      setAbertos(map);
    } catch { setAbertos({}); }
  }

  useEffect(() => { carregar(); carregarAbertos(); }, []);

  function toggleSort(field: SortField) {
    if (sortField === field) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortField(field); setSortDir("asc"); }
  }

  const sorted = [...pessoas].sort((a, b) => {
    if (!sortDir) return 0;
    const av = sortField === "id" ? a.id : (a[sortField] ?? "");
    const bv = sortField === "id" ? b.id : (b[sortField] ?? "");
    const cmp = sortField === "id" ? Number(av) - Number(bv) : String(av).localeCompare(String(bv), "pt-BR");
    return sortDir === "asc" ? cmp : -cmp;
  });

  async function excluir(id: number, nome: string) {
    try { await deletePessoa(id); toast.success(`"${nome}" excluído.`); carregar(filtro); carregarAbertos(); }
    catch (e: any) { toast.error("Erro: " + String(e.message ?? e)); }
  }

  function abrirEncerrar(pessoa: any) {
    const evento = abertos[pessoa.id];
    if (!evento) return;
    setEncerrando({ pessoa, evento });
    setModoSaida("agora");
    setSaidaManual(toLocal(new Date()));
  }

  async function confirmarEncerrar() {
    if (!encerrando) return;
    const { evento } = encerrando;
    const saida = modoSaida === "agora" ? toISO(toLocal(new Date())) : toISO(saidaManual);
    if (!saida) { toast.error("Informe a data/hora de saída."); return; }
    if (evento.entrada && new Date(saida) < new Date(evento.entrada)) {
      toast.error("A saída não pode ser anterior à entrada.");
      return;
    }
    setSalvandoEnc(true);
    try {
      // O UPDATE do backend reescreve todos os campos, então os originais
      // precisam ser reenviados junto — senão entrada/saída prevista somem.
      await updatePessoaEvento(evento.id, {
        person_id: evento.pessoa_id,
        event_id: evento.evento_id,
        entry_datetime: evento.entrada,
        expected_exit_datetime: evento.saida_prevista ?? undefined,
        actual_exit_datetime: saida,
        event_cancelled: evento.cancelado ?? false,
      });
      toast.success(`Entrada de "${encerrando.pessoa.nome}" encerrada.`);
      setEncerrando(null);
      carregarAbertos();
    } catch (e: any) { toast.error(String(e.message ?? e)); }
    finally { setSalvandoEnc(false); }
  }

  const thClass = "cursor-pointer select-none hover:bg-zinc-50";
  const dtClass = "flex h-9 w-full rounded-md border border-zinc-200 bg-white px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-900";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-800">Gerenciar Pessoas</h1>
        <Button asChild><Link href="/pessoas/novo"><Plus className="mr-2 h-4 w-4" />Novo Cadastro</Link></Button>
      </div>
      <div className="flex gap-2 flex-wrap">
        <Select value={campoBusca} onValueChange={setCampoBusca}>
          <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="nome">Nome</SelectItem>
            <SelectItem value="documento">Documento</SelectItem>
          </SelectContent>
        </Select>
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input value={filtro} onChange={e => setFiltro(e.target.value)}
            onKeyDown={e => e.key === "Enter" && carregar(filtro)}
            placeholder={`Buscar por ${campoBusca}...`} className="pl-9" />
        </div>
        <Button variant="outline" onClick={() => carregar(filtro)}>Buscar</Button>
        {filtro && <Button variant="ghost" onClick={() => { setFiltro(""); carregar(""); }}>Limpar</Button>}
      </div>
      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}
      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className={`w-16 ${thClass}`} onClick={() => toggleSort("id")}>ID <SortIcon field="id" sortField={sortField} sortDir={sortDir} /></TableHead>
              <TableHead className={thClass} onClick={() => toggleSort("nome")}>Nome Completo <SortIcon field="nome" sortField={sortField} sortDir={sortDir} /></TableHead>
              <TableHead className={thClass} onClick={() => toggleSort("documento")}>Documento <SortIcon field="documento" sortField={sortField} sortDir={sortDir} /></TableHead>
              <TableHead className="w-40 text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={4} className="text-center py-10 text-zinc-400">Carregando...</TableCell></TableRow>
            ) : sorted.length === 0 ? (
              <TableRow><TableCell colSpan={4} className="text-center py-10 text-zinc-400">Nenhuma pessoa encontrada.</TableCell></TableRow>
            ) : sorted.map((p) => {
              const emAberto = abertos[p.id];
              return (
                <TableRow key={p.id}>
                  <TableCell className="text-zinc-400 font-mono text-xs">{p.id}</TableCell>
                  <TableCell className="font-medium">{p.nome}</TableCell>
                  <TableCell className="text-zinc-600">{p.documento}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="icon" asChild title="Visualizar eventos">
                        <Link href={`/pessoa-eventos?pessoa=${p.id}`}><List className="h-4 w-4" /></Link>
                      </Button>
                      <Button variant="ghost" size="icon" asChild title="Registrar evento">
                        <Link href={`/pessoa-eventos/novo?pessoa=${p.id}`}><CalendarPlus className="h-4 w-4" /></Link>
                      </Button>
                      <Button variant="ghost" size="icon" disabled={!emAberto}
                        onClick={() => abrirEncerrar(p)}
                        title={emAberto ? `Encerrar entrada (${emAberto.nome_evento})` : "Sem evento em andamento"}>
                        <LogOut className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" asChild title="Editar"><Link href={`/pessoas/${p.id}`}><Pencil className="h-4 w-4" /></Link></Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild><Button variant="ghost" size="icon" className="text-red-500 hover:text-red-600 hover:bg-red-50" title="Excluir"><Trash2 className="h-4 w-4" /></Button></AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader><AlertDialogTitle>Confirmar exclusão</AlertDialogTitle><AlertDialogDescription>Excluir <strong>{p.nome}</strong>? Todos os dados serão apagados permanentemente.</AlertDialogDescription></AlertDialogHeader>
                          <AlertDialogFooter><AlertDialogCancel>Cancelar</AlertDialogCancel><AlertDialogAction className="bg-red-600 hover:bg-red-700" onClick={() => excluir(p.id, p.nome)}>Excluir</AlertDialogAction></AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
      <p className="text-xs text-zinc-400">{sorted.length} registro(s) encontrado(s)</p>

      <Dialog open={!!encerrando} onOpenChange={o => !o && setEncerrando(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Encerrar entrada</DialogTitle>
            <DialogDescription>
              {encerrando && (
                <>
                  <strong>{encerrando.pessoa.nome}</strong> — {encerrando.evento.nome_evento}
                  <br />
                  <span className="text-xs">Entrada: {fmt(encerrando.evento.entrada)}</span>
                </>
              )}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer text-sm">
                <input type="radio" checked={modoSaida === "agora"} onChange={() => setModoSaida("agora")} />
                Usar data/hora atual
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-sm">
                <input type="radio" checked={modoSaida === "manual"} onChange={() => setModoSaida("manual")} />
                Definir manualmente
              </label>
            </div>

            {modoSaida === "manual" && (
              <div className="space-y-1.5">
                <Label>Data/hora de saída</Label>
                <input type="datetime-local" value={saidaManual} onChange={e => setSaidaManual(e.target.value)} className={dtClass} />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEncerrando(null)}>Cancelar</Button>
            <Button onClick={confirmarEncerrar} disabled={salvandoEnc}>
              {salvandoEnc ? "Encerrando..." : "Encerrar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
