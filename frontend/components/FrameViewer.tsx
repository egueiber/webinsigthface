"use client";
import { useEffect } from "react";
import { createPortal } from "react-dom";
import { ZoomIn, ZoomOut, RotateCcw, Maximize2, X } from "lucide-react";

interface FrameViewerProps {
  src: string;
  alt: string;
  onError: () => void;
  scale: number;                 // tamanho atual da janela, em % do "maximizado"
  baseScale: number;             // tamanho para o qual o botão de reset volta (ex.: 70)
  minScale?: number;             // padrão 40
  maxScale?: number;             // padrão 100 (100% = totalmente maximizado)
  onScaleChange: (updater: (prev: number) => number) => void;
  fullscreen: boolean;
  onFullscreenChange: (open: boolean) => void;
}

export function FrameViewer({
  src,
  alt,
  onError,
  scale,
  baseScale,
  minScale = 40,
  maxScale = 100,
  onScaleChange,
  fullscreen,
  onFullscreenChange,
}: FrameViewerProps) {
  useEffect(() => {
    if (!fullscreen) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onFullscreenChange(false);
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [fullscreen, onFullscreenChange]);

  function zoomIn()    { onScaleChange((s) => Math.min(s + 10, maxScale)); }
  function zoomOut()   { onScaleChange((s) => Math.max(s - 10, minScale)); }
  function resetZoom() { onScaleChange(() => baseScale); }

  const body = (
    <div className="relative group w-full h-full flex items-center justify-center">
      <div
        className={`w-full h-full bg-black/5 overflow-hidden flex items-center justify-center ${
          fullscreen ? "" : "rounded-lg border border-zinc-200"
        }`}
        onWheel={(e) => {
          e.preventDefault();
          if (e.deltaY < 0) zoomIn(); else zoomOut();
        }}
      >
        {/* object-contain: a foto sempre ocupa o máximo de espaço possível
            dentro da janela, sem cortar nem distorcer — cresce/encolhe junto
            com o tamanho da própria janela. */}
        <img
          src={src}
          alt={alt}
          className="w-full h-full object-contain pointer-events-none"
          draggable={false}
          onError={onError}
        />
      </div>

      <div
        className={`absolute bottom-3 right-3 flex items-center bg-white/90 backdrop-blur-sm rounded-lg shadow-md border border-zinc-200 overflow-hidden transition-opacity ${
          fullscreen ? "opacity-100" : "opacity-0 group-hover:opacity-100"
        }`}
      >
        <button type="button" onClick={(e) => { e.stopPropagation(); zoomIn(); }}
          className="p-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 transition-colors" title="Aumentar janela">
          <ZoomIn size={18} />
        </button>
        <button type="button" onClick={(e) => { e.stopPropagation(); zoomOut(); }}
          className="p-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 border-l border-zinc-200 transition-colors" title="Diminuir janela">
          <ZoomOut size={18} />
        </button>
        <button type="button" onClick={(e) => { e.stopPropagation(); resetZoom(); }}
          className="p-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 border-l border-zinc-200 transition-colors" title="Restaurar tamanho">
          <RotateCcw size={18} />
        </button>
        {!fullscreen && (
          <button type="button" onClick={(e) => { e.stopPropagation(); onFullscreenChange(true); }}
            className="p-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 border-l border-zinc-200 transition-colors" title="Tela cheia">
            <Maximize2 size={18} />
          </button>
        )}
      </div>

      {fullscreen && (
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onFullscreenChange(false); }}
          title="Fechar (Esc)"
          className="absolute top-4 right-4 flex items-center justify-center h-11 w-11 rounded-full bg-white/15 text-white backdrop-blur-sm hover:bg-white/30 transition-colors z-50"
        >
          <X className="h-6 w-6" />
        </button>
      )}
    </div>
  );

  if (!fullscreen) return body;

  // Portal garante que o overlay de tela cheia cubra a viewport de verdade,
  // mesmo se o Dialog pai tiver transform/overflow que limitaria um `fixed`.
  return createPortal(
    <div className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-4">
      {body}
    </div>,
    document.body
  );
}