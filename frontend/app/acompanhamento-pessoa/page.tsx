"use client";
import { Card, CardContent } from "@/components/ui/card";
import { UserSearch } from "lucide-react";

export default function AcompanhamentoPessoaPage() {
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-zinc-800">Acompanhamento por Pessoa</h1>
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16 gap-4 text-center">
          <div className="p-4 bg-purple-50 rounded-full text-purple-500">
            <UserSearch size={32} />
          </div>
          <div>
            <p className="font-semibold text-zinc-700">Tela em desenvolvimento</p>
            <p className="text-sm text-zinc-400 mt-1 max-w-sm">
              Exibirá o grafo de caminhamento com a sequência de câmeras pelas quais uma pessoa passou.
            </p>
          </div>
          <code className="bg-zinc-100 text-zinc-500 text-xs rounded-md px-4 py-2 text-left">
            GET /persons → selecionar pessoa + período<br />
            GET /dashboard/delayed-persons → dados de caminhamento
          </code>
        </CardContent>
      </Card>
    </div>
  );
}
