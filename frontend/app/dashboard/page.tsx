"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { getDashboardIndicators, getDelayedPersons, getLocalizacoes, updatePessoaEvento, getUsuarioLocal } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Users, Clock, UserCheck, AlertCircle, LogOut } from "lucide-react";
import { toast } from "sonner";

function parseLoc(l: any) {
  if (Array.isArray(l)) return { id: l[0], nome: l[1] };
  return { id: l.idlocalizacao ?? l.id, nome: l.nomelocalizacao ?? l.nome ?? l.name };
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

export default function DashboardPage() {
  const today     = new Date().toISOString().split("T")[0];
  const yesterday = new Date(Date.now() - 86400000).toISOString().split("T")[0];

  const [dataInicio,    setDataInicio]    = useState(yesterday);
  const [dataFim,       setDataFim]       = useState(today);
  const [localizacaoId, setLocalizacaoId] = useState("todas");
  const [localizacoes,  setLocalizacoes]  = useState<any[]>([]);
  const [indicadores,   setIndicadores]   = useState<any>(null);
  const [atrasados,     setAtrasados]     = useState<any[]>([]);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState("");
  const [souAdmin,      setSouAdmin]      = useState(false);

  // Modal de encerramento (mesma lógica da tela de Pessoas)
  const [encerrando,  setEncerrando]  = useState<any>(null);
  const [modoSaida,   setModoSaida]   = useState<"agora" | "manual">("agora");
  const [saidaManual, setSaidaManual] = useState("");
  const [salvandoEnc, setSalvandoEnc] = useState(false);

  useEffect(() => {
    setSouAdmin(getUsuarioLocal()?.papel === "admin");
  }, []);

  useEffect(() => {
    getLocalizacoes()
      .then(locs => setLocalizacoes(locs.map(parseLoc)))
      .catch(() => {});
    buscar();
  }, []);

  async function buscar() {
    setLoading(true); setError("");
    const locId = localizacaoId !== "todas" ? localizacaoId : undefined;
    try {
      const [ind, atr] = await Promise.all([
        getDashboardIndicators({ data_inicio: dataInicio, data_fim: dataFim, localizacao_id: locId }),
        getDelayedPersons({ data_inicio: dataInicio, data_fim: dataFim, localizacao_id: locId }),
      ]);
      setIndicadores(ind);
      setAtrasados(atr);
    } catch (e: any) {
      setError(String(e.message ?? e));
    } finally {
      setLoading(false);
    }
  }

  function abrirEncerrar(pessoa: any) {
    if (!pessoa.evento_id) return;
    setEncerrando(pessoa);
    setModoSaida("agora");
    setSaidaManual(toLocal(new Date()));
  }

  async function confirmarEncerrar() {
    if (!encerrando) return;
    const saida = modoSaida === "agora" ? toISO(toLocal(new Date())) : toISO(saidaManual);
    if (!saida) { toast.error("Informe a data/hora de saída."); return; }
    if (encerrando.entrada && new Date(saida) < new Date(encerrando.entrada)) {
      toast.error("A saída não pode ser anterior à entrada.");
      return;
    }
    setSalvandoEnc(true);
    try {
      // O UPDATE do backend reescreve todos os campos, então os originais
      // precisam ser reenviados junto — senão entrada/saída prevista somem.
      await updatePessoaEvento(encerrando.evento_id, {
        person_id: encerrando.id,
        event_id: encerrando.tipo_evento_id,
        entry_datetime: encerrando.entrada,
        expected_exit_datetime: encerrando.saida_prevista ?? undefined,
        actual_exit_datetime: saida,
        event_cancelled: false,
      });
      toast.success(`Entrada de "${encerrando.name ?? encerrando.nome}" encerrada.`);
      setEncerrando(null);
      buscar();
    } catch (e: any) { toast.error(String(e.message ?? e)); }
    finally { setSalvandoEnc(false); }
  }

  const stats = [
    { label: "Pessoas Atendidas",       value: indicadores?.total_served    ?? indicadores?.total_atendidos  ?? "—", icon: UserCheck },
    { label: "Tempo Médio Atendimento", value: indicadores?.average_time    ?? indicadores?.tempo_medio      ?? "—", icon: Clock     },
    { label: "Pessoas Presentes",       value: indicadores?.total_present   ?? indicadores?.total_presentes  ?? "—", icon: Users     },
  ];

  const dtClass = "flex h-9 w-full rounded-md border border-zinc-200 bg-white px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-900";

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-zinc-800">Dashboard</h1>

      <Card>
        <CardContent className="pt-5">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-1.5">
              <Label>Data Início</Label>
              <Input type="date" value={dataInicio} onChange={e => setDataInicio(e.target.value)} className="w-40" />
            </div>
            <div className="space-y-1.5">
              <Label>Data Fim</Label>
              <Input type="date" value={dataFim} onChange={e => setDataFim(e.target.value)} className="w-40" />
            </div>
            <div className="space-y-1.5 min-w-40">
              <Label>Localização</Label>
              <Select value={localizacaoId} onValueChange={setLocalizacaoId}>
                <SelectTrigger><SelectValue placeholder="Todas" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="todas">Todas</SelectItem>
                  {localizacoes.map((l) => (
                    <SelectItem key={l.id} value={String(l.id)}>{l.nome}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={buscar} disabled={loading}>
              {loading ? "Carregando..." : "Atualizar"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {stats.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zinc-500">{label}</CardTitle>
              <Icon className="h-4 w-4 text-zinc-400" />
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-zinc-800">{loading ? "..." : String(value)}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pessoas com Atraso no Atendimento</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead className="text-center">Tempo de Atraso</TableHead>
                <TableHead className="text-center">Última Localização</TableHead>
                {souAdmin && <TableHead className="text-center w-24">Ações</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={souAdmin ? 4 : 3} className="text-center py-10 text-zinc-400">Carregando...</TableCell></TableRow>
              ) : atrasados.length === 0 ? (
                <TableRow><TableCell colSpan={souAdmin ? 4 : 3} className="text-center py-10 text-zinc-400">Nenhuma pessoa com atraso no período.</TableCell></TableRow>
              ) : atrasados.map((p: any, i: number) => {
                const nome = p.name ?? p.nome;
                return (
                  <TableRow key={i}>
                    <TableCell className="font-medium">
                      {p.id ? (
                        <Link
                          href={`/acompanhamento-pessoa?pessoa=${p.id}&nome=${encodeURIComponent(nome ?? "")}`}
                          className="text-emerald-700 hover:underline"
                        >
                          {nome}
                        </Link>
                      ) : nome}
                    </TableCell>
                    <TableCell className="text-center text-orange-600 font-mono">{p.delay_time ?? p.tempo_atraso}</TableCell>
                    <TableCell className="text-center">{p.last_location ?? p.localizacao}</TableCell>
                    {souAdmin && (
                      <TableCell className="text-center">
                        <Button
                          variant="ghost" size="icon"
                          disabled={!p.evento_id}
                          onClick={() => abrirEncerrar(p)}
                          title={p.evento_id ? "Encerrar entrada" : "Sem evento em andamento"}
                        >
                          <LogOut className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={!!encerrando} onOpenChange={o => !o && setEncerrando(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Encerrar entrada</DialogTitle>
            <DialogDescription>
              {encerrando && (
                <>
                  <strong>{encerrando.name ?? encerrando.nome}</strong>
                  <br />
                  <span className="text-xs">Entrada: {fmt(encerrando.entrada)}</span>
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
