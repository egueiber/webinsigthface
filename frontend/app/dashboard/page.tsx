"use client";
import { useState, useEffect } from "react";
import { getDashboardIndicators, getDelayedPersons, getLocalizacoes } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Users, Clock, UserCheck, AlertCircle } from "lucide-react";

function parseLoc(l: any) {
  if (Array.isArray(l)) return { id: l[0], nome: l[1] };
  return { id: l.idlocalizacao ?? l.id, nome: l.nomelocalizacao ?? l.nome ?? l.name };
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

  // Backend retorna: total_served, average_time, total_present
  const stats = [
    { label: "Pessoas Atendidas",       value: indicadores?.total_served    ?? indicadores?.total_atendidos  ?? "—", icon: UserCheck },
    { label: "Tempo Médio Atendimento", value: indicadores?.average_time    ?? indicadores?.tempo_medio      ?? "—", icon: Clock     },
    { label: "Pessoas Presentes",       value: indicadores?.total_present   ?? indicadores?.total_presentes  ?? "—", icon: Users     },
  ];

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
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={3} className="text-center py-10 text-zinc-400">Carregando...</TableCell></TableRow>
              ) : atrasados.length === 0 ? (
                <TableRow><TableCell colSpan={3} className="text-center py-10 text-zinc-400">Nenhuma pessoa com atraso no período.</TableCell></TableRow>
              ) : atrasados.map((p: any, i: number) => (
                <TableRow key={i}>
                  <TableCell className="font-medium">{p.name ?? p.nome}</TableCell>
                  <TableCell className="text-center text-orange-600 font-mono">{p.delay_time ?? p.tempo_atraso}</TableCell>
                  <TableCell className="text-center">{p.last_location ?? p.localizacao}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
