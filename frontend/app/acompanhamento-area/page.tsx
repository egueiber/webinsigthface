"use client";
import { Card, CardContent } from "@/components/ui/card";
import { Map } from "lucide-react";

export default function AcompanhamentoAreaPage() {
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-zinc-800">Acompanhamento por Área</h1>
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16 gap-4 text-center">
          <div className="p-4 bg-blue-50 rounded-full text-blue-500">
            <Map size={32} />
          </div>
          <div>
            <p className="font-semibold text-zinc-700">Tela em desenvolvimento</p>
            <p className="text-sm text-zinc-400 mt-1 max-w-sm">
              Exibirá o mapa (planta baixa) com pins das pessoas detectadas por localização e data.
            </p>
          </div>
          <code className="bg-zinc-100 text-zinc-500 text-xs rounded-md px-4 py-2 text-left">
            GET /locations → selecionar localização + data<br />
            GET /dashboard/indicators → dados de presença
          </code>
        </CardContent>
      </Card>
    </div>
  );
}
