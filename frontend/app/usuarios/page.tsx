"use client";
import { useState, useEffect } from "react";
import { getUsuarios, createUsuario, updateUsuario, resetSenhaUsuario, getUsuarioLocal } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { Plus, Pencil, KeyRound, AlertCircle, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

interface Usuario {
  id: number;
  nome: string;
  login: string;
  papel: string;
  ativo: boolean;
  data_criacao?: string;
}

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");
  const [souAdmin, setSouAdmin] = useState(true);

  // Modal criar/editar
  const [modalAberto, setModalAberto] = useState(false);
  const [editando,    setEditando]    = useState<Usuario | null>(null);
  const [formNome,    setFormNome]    = useState("");
  const [formLogin,   setFormLogin]   = useState("");
  const [formSenha,   setFormSenha]   = useState("");
  const [formPapel,   setFormPapel]   = useState("user");
  const [formAtivo,   setFormAtivo]   = useState(true);
  const [salvando,    setSalvando]    = useState(false);
  const [erroModal,   setErroModal]   = useState("");

  // Modal redefinir senha
  const [senhaModalAberto, setSenhaModalAberto] = useState(false);
  const [usuarioSenhaId,   setUsuarioSenhaId]   = useState<number | null>(null);
  const [novaSenha,        setNovaSenha]        = useState("");
  const [redefinindo,      setRedefinindo]      = useState(false);
  const [erroSenha,        setErroSenha]        = useState("");

  useEffect(() => {
    const local = getUsuarioLocal();
    setSouAdmin(local?.papel === "admin");
    carregar();
  }, []);

  async function carregar() {
    setLoading(true); setError("");
    try {
      setUsuarios(await getUsuarios());
    } catch (e: any) {
      setError(String(e.message ?? e));
    } finally {
      setLoading(false);
    }
  }

  function abrirNovo() {
    setEditando(null);
    setFormNome(""); setFormLogin(""); setFormSenha("");
    setFormPapel("user"); setFormAtivo(true);
    setErroModal("");
    setModalAberto(true);
  }

  function abrirEditar(u: Usuario) {
    setEditando(u);
    setFormNome(u.nome); setFormLogin(u.login); setFormSenha("");
    setFormPapel(u.papel); setFormAtivo(u.ativo);
    setErroModal("");
    setModalAberto(true);
  }

  async function salvar() {
    if (!formNome.trim())  { setErroModal("Informe o nome."); return; }
    if (!formLogin.trim()) { setErroModal("Informe o login."); return; }
    if (!editando && formSenha.length < 6) {
      setErroModal("A senha deve ter pelo menos 6 caracteres.");
      return;
    }

    setSalvando(true); setErroModal("");
    try {
      if (editando) {
        await updateUsuario(editando.id, {
          nome: formNome.trim(), login: formLogin.trim(),
          papel: formPapel, ativo: formAtivo,
        });
        toast.success("Usuário atualizado com sucesso!");
      } else {
        await createUsuario({
          nome: formNome.trim(), login: formLogin.trim(),
          senha: formSenha, papel: formPapel,
        });
        toast.success("Usuário criado com sucesso!");
      }
      setModalAberto(false);
      carregar();
    } catch (e: any) {
      setErroModal(String(e.message ?? e));
    } finally {
      setSalvando(false);
    }
  }

  function abrirRedefinirSenha(id: number) {
    setUsuarioSenhaId(id);
    setNovaSenha("");
    setErroSenha("");
    setSenhaModalAberto(true);
  }

  async function redefinirSenha() {
    if (!usuarioSenhaId) return;
    if (novaSenha.length < 6) { setErroSenha("A senha deve ter pelo menos 6 caracteres."); return; }

    setRedefinindo(true); setErroSenha("");
    try {
      await resetSenhaUsuario(usuarioSenhaId, novaSenha);
      toast.success("Senha redefinida com sucesso!");
      setSenhaModalAberto(false);
    } catch (e: any) {
      setErroSenha(String(e.message ?? e));
    } finally {
      setRedefinindo(false);
    }
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
        <div>
          <h1 className="text-2xl font-bold text-zinc-800">Usuários</h1>
          <p className="text-sm text-zinc-500 mt-1">Gerencie o acesso ao sistema.</p>
        </div>
        <Button onClick={abrirNovo}><Plus className="mr-2 h-4 w-4" />Novo Usuário</Button>
      </div>

      {error && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Login</TableHead>
              <TableHead className="text-center">Papel</TableHead>
              <TableHead className="text-center">Status</TableHead>
              <TableHead className="w-28 text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={5} className="text-center py-10 text-zinc-400">Carregando...</TableCell></TableRow>
            ) : usuarios.length === 0 ? (
              <TableRow><TableCell colSpan={5} className="text-center py-10 text-zinc-400">Nenhum usuário encontrado.</TableCell></TableRow>
            ) : usuarios.map(u => (
              <TableRow key={u.id}>
                <TableCell className="font-medium">{u.nome}</TableCell>
                <TableCell className="text-zinc-600 font-mono text-sm">{u.login}</TableCell>
                <TableCell className="text-center">
                  <Badge variant={u.papel === "admin" ? "default" : "secondary"}>
                    {u.papel === "admin" ? "Administrador" : "Usuário"}
                  </Badge>
                </TableCell>
                <TableCell className="text-center">
                  {u.ativo ? <Badge variant="default">Ativo</Badge> : <Badge variant="secondary">Inativo</Badge>}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" size="icon" onClick={() => abrirEditar(u)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => abrirRedefinirSenha(u.id)}>
                      <KeyRound className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <p className="text-xs text-zinc-400">{usuarios.length} usuário(s) cadastrado(s)</p>

      {/* Modal criar/editar */}
      <Dialog open={modalAberto} onOpenChange={setModalAberto}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editando ? "Editar Usuário" : "Novo Usuário"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {erroModal && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription className="text-xs">{erroModal}</AlertDescription></Alert>}

            <div className="space-y-1.5">
              <Label>Nome completo</Label>
              <Input value={formNome} onChange={e => setFormNome(e.target.value)} placeholder="Ex: Maria Souza" />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="novo-usuario-login">Login</Label>
              <Input id="novo-usuario-login" name="novo-usuario-login" autoComplete="off"
                value={formLogin} onChange={e => setFormLogin(e.target.value)} placeholder="Ex: maria.souza" />
            </div>

            {!editando && (
              <div className="space-y-1.5">
                <Label htmlFor="novo-usuario-senha">Senha</Label>
                <Input id="novo-usuario-senha" name="novo-usuario-senha" type="password" autoComplete="new-password"
                  value={formSenha} onChange={e => setFormSenha(e.target.value)} placeholder="Mínimo 6 caracteres" />
              </div>
            )}

            <div className="space-y-1.5">
              <Label>Papel</Label>
              <Select value={formPapel} onValueChange={setFormPapel}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Usuário</SelectItem>
                  <SelectItem value="admin">Administrador</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {editando && (
              <div className="flex items-center gap-2">
                <Checkbox id="ativo" checked={formAtivo} onCheckedChange={v => setFormAtivo(!!v)} />
                <Label htmlFor="ativo" className="cursor-pointer">Usuário ativo</Label>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalAberto(false)}>Cancelar</Button>
            <Button onClick={salvar} disabled={salvando}>{salvando ? "Salvando..." : "Salvar"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal redefinir senha */}
      <Dialog open={senhaModalAberto} onOpenChange={setSenhaModalAberto}>
        <DialogContent className="max-w-sm">
          <DialogHeader><DialogTitle>Redefinir Senha</DialogTitle></DialogHeader>
          <div className="space-y-4">
            {erroSenha && <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription className="text-xs">{erroSenha}</AlertDescription></Alert>}
            <div className="space-y-1.5">
              <Label htmlFor="redefinir-senha">Nova senha</Label>
              <Input id="redefinir-senha" name="redefinir-senha" type="password" autoComplete="new-password"
                value={novaSenha} onChange={e => setNovaSenha(e.target.value)} placeholder="Mínimo 6 caracteres" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSenhaModalAberto(false)}>Cancelar</Button>
            <Button onClick={redefinirSenha} disabled={redefinindo}>{redefinindo ? "Salvando..." : "Redefinir"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
