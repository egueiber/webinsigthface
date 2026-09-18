"use client";
import { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { getPessoas, getEventos, getEvento, getPessoaEvento, createPessoaEvento, updatePessoaEvento } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { ArrowLeft, Save, AlertCircle, Search, X } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

function parsePessoa(p: any) {
  if (Array.isArray(p)) return { id: p[0], nome: p[1] };
  return { id: p.idPessoa ?? p.id, nome: p.nomePessoa ?? p.nome ?? p.name };
}
function parseEvento(e: any) {
  if (Array.isArray(e)) return { id: e[0], nome: e[1], duracao: e[2] };
  return { id: e.idevento ?? e.id, nome: e.nomeevento ?? e.nome ?? e.name, duracao: e.eventoduracao ?? e.duracao ?? e.duration };
}

function pad(n: number) { return String(n).padStart(2, "0"); }

// O input <datetime-local> e o banco (timestamp without time zone) trabalham em
// hora local "crua", sem fuso. Nunca passar por .toISOString() aqui — isso
// converteria pra UTC e desloca 3h (fuso de Paraná).
function toISO(val: string): string | null { return val ? `${val}:00` : null; }

function toLocal(value: string | Date | null): string {
  if (!value) return "";
  const d = typeof value === "string" ? new Date(value) : value;
  if (isNaN(d.getTime())) return "";
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function PessoaEventoForm() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const id    = params?.id as string;
  const isNew = id === "novo";
  const pessoaPre = searchParams?.get("pessoa") ?? "";

  const [pessoaId,      setPessoaId]      = useState("");
  const [buscaPessoa,   setBuscaPessoa]   = useState("");   // texto digitado na barra
  const [listaAberta,   setListaAberta]   = useState(false);
  const [destaque,      setDestaque]      = useState(0);    // item destacado pelo teclado
  const buscaRef = useRef<HTMLDivElement>(null);
  const [eventoId,      setEventoId]      = useState("");
  const [entrada,       setEntrada]       = useState("");
  const [saidaPrevista, setSaidaPrevista] = useState("");
  const [saidaEfetiva,  setSaidaEfetiva]  = useState("");
  const [cancelado,     setCancelado]     = useState(false);
  const [pessoas,       setPessoas]       = useState<any[]>([]);
  const [eventos,       setEventos]       = useState<any[]>([]);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState("");

  // Calcula saída prevista automaticamente ao mudar evento ou entrada
  async function calcularSaidaPrevista(evId: string, entradaVal: string) {
    if (!evId || !entradaVal) return;
    try {
      const ev = await getEvento(Number(evId));
      const dur = ev.eventoduracao ?? ev.duracao ?? ev.duration;
      if (dur && dur > 0) {
        const entradaDt = new Date(entradaVal);
        entradaDt.setMinutes(entradaDt.getMinutes() + Number(dur));
        setSaidaPrevista(toLocal(entradaDt));
      }
    } catch {}
  }

  useEffect(() => {
    getPessoas().then(ps => setPessoas(ps.map(parsePessoa))).catch(() => {});
    getEventos().then(es => setEventos(es.map(parseEvento))).catch(() => {});

    if (!isNew) {
      getPessoaEvento(Number(id))
        .then(data => {
          setPessoaId(String(data.person_id ?? ""));
          setEventoId(String(data.event_id ?? ""));
          setEntrada(toLocal(data.entry_datetime));
          setSaidaPrevista(toLocal(data.expected_exit_datetime));
          setSaidaEfetiva(toLocal(data.actual_exit_datetime));
          setCancelado(data.event_cancelled ?? false);
        })
        .catch(e => setError(String(e.message ?? e)));
    } else {
      setEntrada(toLocal(new Date()));
      if (pessoaPre) setPessoaId(pessoaPre);
    }
  }, [id]);

  // Quando o ID vem de fora (edição ou ?pessoa=), preenche o nome na barra.
  // Roda também quando a lista termina de carregar, que pode ser depois.
  useEffect(() => {
    if (!pessoaId || pessoas.length === 0) return;
    const p = pessoas.find(x => String(x.id) === String(pessoaId));
    if (p) setBuscaPessoa(p.nome);
  }, [pessoaId, pessoas]);

  // Fecha a lista ao clicar fora
  useEffect(() => {
    function onClickFora(ev: MouseEvent) {
      if (buscaRef.current && !buscaRef.current.contains(ev.target as Node)) setListaAberta(false);
    }
    document.addEventListener("mousedown", onClickFora);
    return () => document.removeEventListener("mousedown", onClickFora);
  }, []);

  const pessoaSelecionada = pessoas.find(p => String(p.id) === String(pessoaId));

  // Filtro no front: a lista completa já foi carregada uma vez.
  const pessoasFiltradas = buscaPessoa.trim() === "" || pessoaSelecionada?.nome === buscaPessoa
    ? pessoas
    : pessoas.filter(p => (p.nome ?? "").toLowerCase().includes(buscaPessoa.toLowerCase()));

  function handleBuscaChange(valor: string) {
    setBuscaPessoa(valor);
    setListaAberta(true);
    setDestaque(0);
    // Digitar invalida a seleção anterior: sem escolher um item da lista,
    // não há ID e o formulário não deixa salvar.
    if (pessoaId) setPessoaId("");
  }

  function selecionarPessoa(p: any) {
    setPessoaId(String(p.id));
    setBuscaPessoa(p.nome);
    setListaAberta(false);
  }

  function limparPessoa() {
    setPessoaId("");
    setBuscaPessoa("");
    setListaAberta(false);
  }

  function handleBuscaKeyDown(e: React.KeyboardEvent) {
    if (!listaAberta && (e.key === "ArrowDown" || e.key === "Enter")) { setListaAberta(true); return; }
    if (e.key === "ArrowDown") { e.preventDefault(); setDestaque(d => Math.min(d + 1, pessoasFiltradas.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setDestaque(d => Math.max(d - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); const p = pessoasFiltradas[destaque]; if (p) selecionarPessoa(p); }
    else if (e.key === "Escape") { setListaAberta(false); }
  }

  function handleEventoChange(evId: string) {
    setEventoId(evId);
    calcularSaidaPrevista(evId, entrada);
  }

  function handleEntradaChange(val: string) {
    setEntrada(val);
    calcularSaidaPrevista(eventoId, val);
  }

  async function salvar() {
    if (!pessoaId && buscaPessoa.trim()) {
      setError("Selecione uma pessoa da lista de resultados.");
      return;
    }
    if (!pessoaId || !eventoId || !entrada) {
      setError("Pessoa, Evento e Data/Hora de Entrada são obrigatórios.");
      return;
    }
    setLoading(true); setError("");
    try {
      const payload = {
        person_id: Number(pessoaId),
        event_id: Number(eventoId),
        entry_datetime: toISO(entrada)!,
        event_cancelled: cancelado,
        expected_exit_datetime: saidaPrevista ? toISO(saidaPrevista)! : undefined,
        actual_exit_datetime: saidaEfetiva ? toISO(saidaEfetiva)! : undefined,
      };
      if (isNew) await createPessoaEvento(payload);
      else await updatePessoaEvento(Number(id), payload);
      toast.success("Registro salvo com sucesso!");
      router.push(pessoaPre ? "/pessoas" : "/pessoa-eventos");
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  const dtClass = "flex h-9 w-full rounded-md border border-zinc-200 bg-white px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-900";

  return (
    <div className="space-y-6 max-w-lg">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href={pessoaPre ? "/pessoas" : "/pessoa-eventos"}><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">{isNew ? "Novo Registro" : "Editar Registro"}</h1>
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      <Card>
        <CardHeader><CardTitle className="text-base">Dados do Evento</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5" ref={buscaRef}>
            <Label>Pessoa <span className="text-red-500">*</span></Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none" />
              <Input
                value={buscaPessoa}
                onChange={e => handleBuscaChange(e.target.value)}
                onFocus={() => setListaAberta(true)}
                onKeyDown={handleBuscaKeyDown}
                placeholder="Digite para buscar..."
                className={`pl-9 ${pessoaId ? "pr-9" : ""}`}
                autoComplete="off"
              />
              {pessoaId && (
                <button type="button" onClick={limparPessoa}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600">
                  <X className="h-4 w-4" />
                </button>
              )}

              {listaAberta && (
                <div className="absolute z-50 mt-1 w-full max-h-56 overflow-y-auto rounded-md border border-zinc-200 bg-white shadow-md">
                  {pessoasFiltradas.length === 0 ? (
                    <div className="px-3 py-2 text-sm text-zinc-400">Nenhuma pessoa encontrada.</div>
                  ) : pessoasFiltradas.map((p, i) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => selecionarPessoa(p)}
                      onMouseEnter={() => setDestaque(i)}
                      className={`w-full text-left px-3 py-2 text-sm ${i === destaque ? "bg-zinc-100" : "hover:bg-zinc-50"} ${String(p.id) === String(pessoaId) ? "font-medium" : ""}`}>
                      {p.nome}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {!pessoaId && buscaPessoa.trim() !== "" && (
              <p className="text-xs text-amber-600">Selecione uma pessoa da lista.</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>Evento <span className="text-red-500">*</span></Label>
            <Select value={eventoId} onValueChange={handleEventoChange}>
              <SelectTrigger><SelectValue placeholder="Selecione..." /></SelectTrigger>
              <SelectContent>{eventos.map(e => <SelectItem key={e.id} value={String(e.id)}>{e.nome}{e.duracao ? ` (${e.duracao} min)` : ""}</SelectItem>)}</SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>Data/hora de entrada <span className="text-red-500">*</span></Label>
            <input type="datetime-local" value={entrada} onChange={e => handleEntradaChange(e.target.value)} className={dtClass} />
          </div>

          <div className="space-y-1.5">
            <Label>Data/hora de saída prevista</Label>
            <input type="datetime-local" value={saidaPrevista} onChange={e => setSaidaPrevista(e.target.value)} className={dtClass} />
            <p className="text-xs text-zinc-400">Calculada automaticamente a partir da duração do evento. Pode ser ajustada manualmente.</p>
          </div>

          <div className="space-y-1.5">
            <Label>Data/hora de saída efetiva</Label>
            <input type="datetime-local" value={saidaEfetiva} onChange={e => setSaidaEfetiva(e.target.value)} className={dtClass} />
            <p className="text-xs text-zinc-400">Preencha quando o atendimento for concluído.</p>
          </div>

          <div className="flex items-center gap-2">
            <Checkbox id="cancelado" checked={cancelado} onCheckedChange={v => setCancelado(!!v)} />
            <Label htmlFor="cancelado" className="cursor-pointer">Evento cancelado</Label>
          </div>

          <Button onClick={salvar} disabled={loading}>
            <Save className="mr-2 h-4 w-4" />{loading ? "Salvando..." : "Salvar"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

export default function PessoaEventoFormPage() {
  return (
    <Suspense fallback={<div>Carregando...</div>}>
      <PessoaEventoForm />
    </Suspense>
  );
}
