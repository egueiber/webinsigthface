"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { getLocalizacoes, deleteLocalizacao } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Plus, Search, Pencil, Trash2, AlertCircle, ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";
import { toast } from "sonner";

function parseLoc(l: any) {
  if (Array.isArray(l)) return { id: l[0], nome: l[1] };
  return { id: l.idlocalizacao ?? l.id, nome: l.nomelocalizacao ?? l.nome ?? l.name };
}

type SortDir = "asc" | "desc";

function SortIcon({ field, sf, sd }: { field: string; sf: string; sd: SortDir }) {
  if (sf !== field) return <ChevronsUpDown className="ml-1 h-3 w-3 inline opacity-40" />;
  return sd === "asc" ? <ChevronUp className="ml-1 h-3 w-3 inline" /> : <ChevronDown className="ml-1 h-3 w-3 inline" />;
}

export default function LocalizacoesPage() {
  const [items,   setItems]   = useState<any[]>([]);
  const [filtro,  setFiltro]  = useState("");
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");
  const [sf, setSf] = useState("nome");
  const [sd, setSd] = useState<SortDir>("asc");

  async function carregar(nome = "") {
    setLoading(true); setError("");
    try { setItems((await getLocalizacoes(nome)).map(parseLoc)); }
    catch (e: any) { setError(String(e.message ?? e)); }
    finally { setLoading(false); }
  }

  useEffect(() => { carregar(); }, []);

  function toggleSort(field: string) {
    if (sf === field) setSd(d => d === "asc" ? "desc" : "asc");
    else { setSf(field); setSd("asc"); }
  }

  const sorted = [...items].sort((a, b) => {
    const cmp = sf === "id" ? Number(a.id) - Number(b.id) : String(a.nome).localeCompare(String(b.nome), "pt-BR");
    return sd === "asc" ? cmp : -cmp;
  });

  async function excluir(id: number, nome: string) {
    try { await deleteLocalizacao(id); toast.success(`"${nome}" excluída.`); carregar(filtro); }
    catch (e: any) { toast.error("Erro: " + String(e.message ?? e)); }
  }

  const th = "cursor-pointer select-none hover:bg-zinc-50";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-800">Gerenciar Localizações</h1>
        <Button asChild><Link href="/localizacoes/novo"><Plus className="mr-2 h-4 w-4" />Nova Localização</Link></Button>
      </div>
      <div className="flex gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input value={filtro} onChange={e => setFiltro(e.target.value)} onKeyDown={e => e.key === "Enter" && carregar(filtro)} placeholder="Buscar por nome..." className="pl-9" />
        </div>
        <Button variant="outline" onClick={() => carregar(filtro)}>Buscar</Button>
        {filtro && <Button variant="ghost" onClick={() => { setFiltro(""); carregar(""); }}>Limpar</Button>}
      </div>
      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}
      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className={`w-16 ${th}`} onClick={() => toggleSort("id")}>ID <SortIcon field="id" sf={sf} sd={sd} /></TableHead>
              <TableHead className={th} onClick={() => toggleSort("nome")}>Nome da Localização <SortIcon field="nome" sf={sf} sd={sd} /></TableHead>
              <TableHead className="w-24 text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={3} className="text-center py-10 text-zinc-400">Carregando...</TableCell></TableRow>
            ) : sorted.length === 0 ? (
              <TableRow><TableCell colSpan={3} className="text-center py-10 text-zinc-400">Nenhuma localização encontrada.</TableCell></TableRow>
            ) : sorted.map((l) => (
              <TableRow key={l.id}>
                <TableCell className="text-zinc-400 font-mono text-xs">{l.id}</TableCell>
                <TableCell className="font-medium">{l.nome}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" size="icon" asChild><Link href={`/localizacoes/${l.id}`}><Pencil className="h-4 w-4" /></Link></Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild><Button variant="ghost" size="icon" className="text-red-500 hover:text-red-600 hover:bg-red-50"><Trash2 className="h-4 w-4" /></Button></AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader><AlertDialogTitle>Confirmar exclusão</AlertDialogTitle><AlertDialogDescription>Excluir <strong>{l.nome}</strong>?</AlertDialogDescription></AlertDialogHeader>
                        <AlertDialogFooter><AlertDialogCancel>Cancelar</AlertDialogCancel><AlertDialogAction className="bg-red-600 hover:bg-red-700" onClick={() => excluir(l.id, l.nome)}>Excluir</AlertDialogAction></AlertDialogFooter>
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
