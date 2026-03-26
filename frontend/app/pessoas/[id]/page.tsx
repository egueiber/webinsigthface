"use client";
import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { getPessoa, createPessoa } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Save, AlertCircle, Info } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

export default function PessoaFormPage() {
  const router = useRouter();
  const params = useParams();
  const id     = params?.id as string;
  const isNew  = id === "novo";

  const [nome,      setNome]      = useState("");
  const [documento, setDocumento] = useState("");
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState("");

  useEffect(() => {
    if (!isNew) {
      getPessoa(Number(id))
        .then(data => { setNome(data.nome ?? ""); setDocumento(data.documento ?? ""); })
        .catch(e => setError(e.message));
    }
  }, [id]);

  async function salvar() {
    if (!nome.trim() || !documento.trim()) { setError("Preencha o Nome e o Documento."); return; }
    setLoading(true); setError("");
    try {
      await createPessoa({ nome, documento });
      toast.success("Pessoa salva com sucesso!");
      router.push("/pessoas");
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/pessoas"><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <h1 className="text-2xl font-bold text-zinc-800">{isNew ? "Nova Pessoa" : "Editar Pessoa"}</h1>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader><CardTitle className="text-base">Dados Cadastrais</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <Label htmlFor="nome">Nome Completo <span className="text-red-500">*</span></Label>
            <Input id="nome" value={nome} onChange={e => setNome(e.target.value)} placeholder="Ex: João da Silva" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="documento">Nº da Carteira / Documento <span className="text-red-500">*</span></Label>
            <Input id="documento" value={documento} onChange={e => setDocumento(e.target.value)} placeholder="Ex: 123456" />
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              O cadastro facial (captura de fotos via webcam) é realizado pelo sistema desktop.
              Aqui você gerencia os dados cadastrais da pessoa.
            </AlertDescription>
          </Alert>

          <Button onClick={salvar} disabled={loading}>
            <Save className="mr-2 h-4 w-4" />
            {loading ? "Salvando..." : "Salvar"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
