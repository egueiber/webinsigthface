"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { getCenarios, deleteCenario } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Plus, Search, Pencil, Trash2, AlertCircle, ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";
import { toast } from "sonner";

function parseCenario(c: any) {
  if (Array.isArray(c)) return { id: c[0], descricao: c[1], idparametro: c[2], ativo: c[3], padrao: c[4] };
  return { id: c.idcenario ?? c.id, descricao: c.descricaocenario ?? c.descricao ?? c.description, idparametro: c.idparametro ?? c.parameter_id, ativo: c.ativo ?? c.active, padrao: c.padrao ?? c.default };
}

type SortDir = "asc" | "desc";

function SortIcon({ field, sf, sd }: { field: string; sf: string; sd: SortDir }) {
  if (sf !== field) return <ChevronsUpDown className="ml-1 h-3 w-3 inline opacity-40" />;
  return sd === "asc" ? <ChevronUp className="ml-1 h-3 w-3 inline" /> : <ChevronDown className="ml-1 h-3 w-3 inline" />;
}

export default function CenariosPage() {
  const [items,      setItems]      = useState<any[]>([]);
  const [filtro,     setFiltro]     = useState("");
  const [campoBusca, setCampoBusca] = useState("descricao");
  const [filtroStatus, setFiltroStatus] = useState("todos");
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState("");
  const [sf, setSf] = useState("descricao");
  const [sd, setSd] = useState<SortDir>("asc");

  async function carregar(valor = "") {
    setLoading(true); setError("");
    try {
      const desc = campoBusca === "descricao" ? valor : "";
      setItems((await getCenarios(desc)).map(parseCenario));
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  useEffect(() => { carregar(); }, []);

  function toggleSort(field: string) {
    if (sf === field) setSd(d => d === "asc" ? "desc" : "asc");
    else { setSf(field); setSd("asc"); }
  }

  const filtered = items.filter(c => {
    if (filtroStatus === "ativo") return c.ativo;
    if (filtroStatus === "inativo") return !c.ativo;
    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
    const cmp = sf === "id" ? Number(a.id) - Number(b.id) : String(a.descricao ?? "").localeCompare(String(b.descricao ?? ""), "pt-BR");
    return sd === "asc" ? cmp : -cmp;
  });

  async function excluir(id: number, desc: string) {
    try { await deleteCenario(id); toast.success(`Cenário "${desc}" excluído.`); carregar(filtro); }
    catch (e: any) { toast.error("Erro: " + String(e.message ?? e)); }
  }

  const th = "cursor-pointer select-none hover:bg-zinc-50";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-800">Gerenciar Cenários</h1>
        <Button asChild><Link href="/cenarios/novo"><Plus className="mr-2 h-4 w-4" />Novo Cenário</Link></Button>
      </div>
      <div className="flex gap-2 flex-wrap">
        <Select value={campoBusca} onValueChange={setCampoBusca}>
          <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="descricao">Descrição</SelectItem>
          </SelectContent>
        </Select>
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input value={filtro} onChange={e => setFiltro(e.target.value)} onKeyDown={e => e.key === "Enter" && carregar(filtro)} placeholder="Buscar por descrição..." className="pl-9" />
        </div>
        <Select value={filtroStatus} onValueChange={setFiltroStatus}>
          <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos</SelectItem>
            <SelectItem value="ativo">Ativos</SelectItem>
            <SelectItem value="inativo">Inativos</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={() => carregar(filtro)}>Buscar</Button>
        {filtro && <Button variant="ghost" onClick={() => { setFiltro(""); carregar(""); }}>Limpar</Button>}
      </div>
      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}
      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className={`w-16 ${th}`} onClick={() => toggleSort("id")}>ID <SortIcon field="id" sf={sf} sd={sd} /></TableHead>
              <TableHead className={th} onClick={() => toggleSort("descricao")}>Descrição <SortIcon field="descricao" sf={sf} sd={sd} /></TableHead>
              <TableHead className="text-center">Status</TableHead>
              <TableHead className="w-24 text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={4} className="text-center py-10 text-zinc-400">Carregando...</TableCell></TableRow>
            ) : sorted.length === 0 ? (
              <TableRow><TableCell colSpan={4} className="text-center py-10 text-zinc-400">Nenhum cenário encontrado.</TableCell></TableRow>
            ) : sorted.map((c) => (
              <TableRow key={c.id}>
                <TableCell className="text-zinc-400 font-mono text-xs">{c.id}</TableCell>
                <TableCell className="font-medium">{c.descricao}</TableCell>
                <TableCell className="text-center">
                  <div className="flex justify-center gap-2">
                    {c.ativo ? <Badge variant="default">Ativo</Badge> : <Badge variant="secondary">Inativo</Badge>}
                    {c.padrao && <Badge variant="outline">Padrão</Badge>}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" size="icon" asChild><Link href={`/cenarios/${c.id}`}><Pencil className="h-4 w-4" /></Link></Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild><Button variant="ghost" size="icon" className="text-red-500 hover:text-red-600 hover:bg-red-50"><Trash2 className="h-4 w-4" /></Button></AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader><AlertDialogTitle>Confirmar exclusão</AlertDialogTitle><AlertDialogDescription>Excluir <strong>{c.descricao}</strong>?</AlertDialogDescription></AlertDialogHeader>
                        <AlertDialogFooter><AlertDialogCancel>Cancelar</AlertDialogCancel><AlertDialogAction className="bg-red-600 hover:bg-red-700" onClick={() => excluir(c.id, c.descricao)}>Excluir</AlertDialogAction></AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <p className="text-xs text-zinc-400">{sorted.length} registro(s) encontrado(s)</p>
    </div>
  );
}
