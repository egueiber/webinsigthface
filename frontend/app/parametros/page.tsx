"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { getParametros, deleteParametro, getUsuarioLocal } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Plus, Pencil, Trash2, AlertCircle, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

// Backend retorna tuplas: [idParametro, nomeparametro]
function parseParam(p: any) {
  if (Array.isArray(p)) return { id: p[0], nome: p[1] };
  return { id: p.idParametro ?? p.id, nome: p.nomeparametro ?? p.nome ?? p.name };
}

export default function ParametrosPage() {
  const [items,    setItems]    = useState<any[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");
  const [souAdmin, setSouAdmin] = useState(false);

  async function carregar() {
    setLoading(true); setError("");
    try { setItems((await getParametros()).map(parseParam)); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  useEffect(() => {
    setSouAdmin(getUsuarioLocal()?.papel === "admin");
    carregar();
  }, []);

  async function excluir(id: number, nome: string) {
    try { await deleteParametro(id); toast.success(`Parâmetro "${nome}" excluído.`); carregar(); }
    catch (e: any) { toast.error("Erro: " + e.message); }
  }

  if (!souAdmin) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-zinc-400 gap-3">
        <ShieldAlert className="h-10 w-10" />
        <p className="text-sm">Esta área é restrita a administradores.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-800">Gerenciar Parâmetros</h1>
        <Button asChild><Link href="/parametros/novo"><Plus className="mr-2 h-4 w-4" />Novo Parâmetro</Link></Button>
      </div>
      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}
      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome do Parâmetro</TableHead>
              <TableHead className="w-16 text-center">ID</TableHead>
              <TableHead className="w-24 text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={3} className="text-center py-10 text-zinc-400">Carregando...</TableCell></TableRow>
            ) : items.length === 0 ? (
              <TableRow><TableCell colSpan={3} className="text-center py-10 text-zinc-400">Nenhum parâmetro encontrado.</TableCell></TableRow>
            ) : items.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-medium">{p.nome}</TableCell>
                <TableCell className="text-center text-zinc-400 font-mono text-xs">{p.id}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" size="icon" asChild><Link href={`/parametros/${p.id}`}><Pencil className="h-4 w-4" /></Link></Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild><Button variant="ghost" size="icon" className="text-red-500 hover:text-red-600 hover:bg-red-50"><Trash2 className="h-4 w-4" /></Button></AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader><AlertDialogTitle>Confirmar exclusão</AlertDialogTitle><AlertDialogDescription>Excluir <strong>{p.nome}</strong>?</AlertDialogDescription></AlertDialogHeader>
                        <AlertDialogFooter><AlertDialogCancel>Cancelar</AlertDialogCancel><AlertDialogAction className="bg-red-600 hover:bg-red-700" onClick={() => excluir(p.id, p.nome)}>Excluir</AlertDialogAction></AlertDialogFooter>
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
