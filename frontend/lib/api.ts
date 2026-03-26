const API_BASE = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
    throw new Error(err.detail || "Erro na requisição");
  }
  return res.json();
}

function qs(params: Record<string, string | number | boolean | null | undefined>) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== "") p.append(k, String(v));
  }
  const str = p.toString();
  return str ? `?${str}` : "";
}

// Pessoas
export const getPessoas = (filter = "") => request<any[]>(`/persons/${qs({ filter })}`);
export const getPessoa  = (id: number)  => request<any>(`/persons/${id}`);
export const createPessoa = (data: { nome: string; documento: string }) =>
  request<any>(`/persons/${qs({ name: data.nome, document: data.documento })}`, { method: "POST" });
export const deletePessoa = (id: number) => request<any>(`/persons/${id}`, { method: "DELETE" });

// Localizações
export const getLocalizacoes   = (filter = "") => request<any[]>(`/locations/${qs({ filter })}`);
export const getLocalizacao    = (id: number)  => request<any>(`/locations/${id}`);
export const createLocalizacao = (data: { nome: string; mapa_path?: string }) =>
  request<any>(`/locations/${qs({ name: data.nome, map_path: data.mapa_path ?? "" })}`, { method: "POST" });
export const updateLocalizacao = (id: number, data: { nome: string; mapa_path?: string }) =>
  request<any>(`/locations/${id}${qs({ name: data.nome, map_path: data.mapa_path ?? "" })}`, { method: "PUT" });
export const deleteLocalizacao = (id: number) => request<any>(`/locations/${id}`, { method: "DELETE" });

// Eventos
export const getEventos   = (filter = "") => request<any[]>(`/events/${qs({ filter })}`);
export const getEvento    = (id: number)  => request<any>(`/events/${id}`);
export const createEvento = (data: { nome: string; duracao?: number | null }) =>
  request<any>(`/events/${qs({ name: data.nome, duration: data.duracao ?? 0 })}`, { method: "POST" });
export const updateEvento = (id: number, data: { nome: string; duracao?: number | null }) =>
  request<any>(`/events/${id}${qs({ name: data.nome, duration: data.duracao ?? 0 })}`, { method: "PUT" });
export const deleteEvento = (id: number) => request<any>(`/events/${id}`, { method: "DELETE" });

// Cenários
export const getCenarios   = (filter = "") => request<any[]>(`/scenarios/${qs({ filter })}`);
export const getCenario    = (id: number)  => request<any>(`/scenarios/${id}`);
export const createCenario = (data: { descricao: string; idparametro: number; ativo: boolean; padrao: boolean }) =>
  request<any>(`/scenarios/${qs({ description: data.descricao, parameter_id: data.idparametro, active: data.ativo, default: data.padrao })}`, { method: "POST" });
export const updateCenario = (id: number, data: { descricao: string; idparametro: number; ativo: boolean; padrao: boolean }) =>
  request<any>(`/scenarios/${id}${qs({ description: data.descricao, parameter_id: data.idparametro, active: data.ativo, default: data.padrao })}`, { method: "PUT" });
export const deleteCenario = (id: number) => request<any>(`/scenarios/${id}`, { method: "DELETE" });
export const getCamerasDisponiveis  = () => request<any[]>("/scenarios/cameras/available");
export const getParametrosDisponiveis = () => request<any[]>("/scenarios/parameters/available");

// Parâmetros (usa JSON body via Pydantic)
function paramPayload(data: any) {
  return JSON.stringify({
    name: data.nome,
    photos_path: data.fotos,
    maps_path: data.mapas,
    videos_to_process_path: data.videos_a_processar,
    processed_videos_path: data.videos_processados,
    video_markers_path: data.video_marcoes,
    frame_interval: Number(data.intervalo_frames),
    image_scale: parseFloat(data.escala_imagem),
    recognition_tolerance: parseFloat(data.tolerancia),
    detection_model: data.modelo_deteccao,
    generate_markers: data.gerar_marcoes,
    finish_when_all_identified: data.finalizaraoidentificartodos,
  });
}
export const getParametros   = ()          => request<any[]>("/config/parameters");
export const getParametro    = (id: number) => request<any>(`/config/parameters/${id}`);
export const createParametro = (data: any) => request<any>("/config/parameters", { method: "POST", body: paramPayload(data) });
export const updateParametro = (id: number, data: any) => request<any>(`/config/parameters/${id}`, { method: "PUT", body: paramPayload(data) });
export const deleteParametro = (id: number) => request<any>(`/config/parameters/${id}`, { method: "DELETE" });

// Dashboard
export const getDashboardIndicators = (params: { data_inicio: string; data_fim: string; localizacao_id?: string }) =>
  request<any>(`/dashboard/indicators${qs({ start_date: params.data_inicio, end_date: params.data_fim, location_id: params.localizacao_id })}`);
export const getDelayedPersons = (params: { data_inicio: string; data_fim: string; localizacao_id?: string }) =>
  request<any[]>(`/dashboard/delayed-persons${qs({ start_date: params.data_inicio, end_date: params.data_fim, location_id: params.localizacao_id })}`);
