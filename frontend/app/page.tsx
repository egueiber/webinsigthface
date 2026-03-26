import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center gap-4">
      <h1 className="text-3xl font-bold text-zinc-800">Health Track Unimed · UEPG</h1>
      <p className="text-zinc-500 text-lg">Selecione um módulo no menu lateral para começar.</p>
      <Button asChild className="mt-2">
        <Link href="/dashboard">Ir para Dashboard →</Link>
      </Button>
    </div>
  );
}
