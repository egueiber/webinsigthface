"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { getPessoas, deletePessoa } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Plus, Search, Pencil, Trash2, AlertCircle } from "lucide-react";
import { toast } from "sonner";

// Backend retorna tuplas: [idPessoa, nomePessoa, documentoPessoa]
function parsePessoa(p: any) {
  if (Array.isArray(p)) return { id: p[0], nome: p[1], documento: p[2] };
  return { id: p.idPessoa ?? p.id, nome: p.nomePessoa ?? p.nome ?? p.name, documento: p.documentoPessoa ?? p.documento ?? p.document };
}

export default function PessoasPage() {
  const [pessoas,  setPessoas]  = useState<any[]>([]);
  const [filtro,   setFiltro]   = useState("");
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");

  async function carregar(nome = "") {
    setLoading(true); setError("");
    try { setPessoas((await getPessoas(nome)).map(parsePessoa)); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  useEffect(() => { carregar(); }, []);

  async function excluir(id: number, nome: string) {
    try { await deletePessoa(id); toast.success(`"${nome}" excluído com sucesso.`); carregar(filtro); }
    catch (e: any) { toast.error("Erro ao excluir: " + e.message); }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-800">Gerenciar Pessoas</h1>
        <Button asChild><Link href="/pessoas/novo"><Plus className="mr-2 h-4 w-4" />Novo Cadastro</Link></Button>
      </div>
      <div className="flex gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input value={filtro} onChange={e => setFiltro(e.target.value)}
            onKeyDown={e => e.key === "Enter" && carregar(filtro)}
            placeholder="Buscar por nome..." className="pl-9" />
        </div>
        <Button variant="outline" onClick={() => carregar(filtro)}>Buscar</Button>
      </div>
      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}
      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-16">ID</TableHead>
              <TableHead>Nome Completo</TableHead>
              <TableHead>Documento</TableHead>
              <TableHead className="w-24 text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={4} className="text-center py-10 text-zinc-400">Carregando...</TableCell></TableRow>
            ) : pessoas.length === 0 ? (
              <TableRow><TableCell colSpan={4} className="text-center py-10 text-zinc-400">Nenhuma pessoa encontrada.</TableCell></TableRow>
            ) : pessoas.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="text-zinc-400 font-mono text-xs">{p.id}</TableCell>
                <TableCell className="font-medium">{p.nome}</TableCell>
                <TableCell className="text-zinc-600">{p.documento}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" size="icon" asChild>
                      <Link href={`/pessoas/${p.id}`}><Pencil className="h-4 w-4" /></Link>
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="ghost" size="icon" className="text-red-500 hover:text-red-600 hover:bg-red-50"><Trash2 className="h-4 w-4" /></Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
                          <AlertDialogDescription>Excluir <strong>{p.nome}</strong>? Todos os dados e fotos serão apagados permanentemente.</AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancelar</AlertDialogCancel>
                          <AlertDialogAction className="bg-red-600 hover:bg-red-700" onClick={() => excluir(p.id, p.nome)}>Excluir</AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
