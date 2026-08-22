const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function traduzErro(detail: string): string {
  const d = String(detail);
  if (d.includes("violates foreign key") || d.includes("still referenced")) {
    if (d.includes("tb_pessoa_evento") && d.includes("tb_pessoa"))
      return "Não é possível excluir esta pessoa pois ela possui eventos vinculados. Exclua primeiro os registros em Pessoa — Eventos.";
    if (d.includes("tb_cameras") && d.includes("tb_localizacao"))
      return "Não é possível excluir esta localização pois há câmeras vinculadas a ela. Exclua ou remaneje as câmeras primeiro.";
    if (d.includes("tb_pessoa_evento") && d.includes("tb_evento"))
      return "Não é possível excluir este evento pois há pessoas vinculadas a ele. Exclua primeiro os registros em Pessoa — Eventos.";
    if (d.includes("tb_cenario") && d.includes("tb_parametro"))
      return "Não é possível excluir este parâmetro pois há cenários que o utilizam. Altere ou exclua os cenários primeiro.";
    if (d.includes("tb_cenario_camera") || (d.includes("tb_cameras") && d.includes("cenario")))
      return "Não é possível excluir esta câmera pois ela está vinculada a um ou mais cenários. Remova-a dos cenários primeiro.";
    if (d.includes("tb_videos_processados"))
      return "Não é possível excluir este registro pois há detecções processadas vinculadas a ele.";
    return "Não é possível excluir este registro pois ele está vinculado a outros dados no sistema. Remova os vínculos primeiro.";
  }
  if (d.includes("unique constraint") || d.includes("já está cadastrado"))
    return d.includes("já está cadastrado") ? d : "Este registro já existe no sistema (valor duplicado).";
  return d;
}

// ── Token de autenticação ─────────────────────────────────────────────────────
const TOKEN_KEY = "healthtrack_token";
const USER_KEY  = "healthtrack_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function getUsuarioLocal(): any | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function setUsuarioLocal(usuario: any) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(USER_KEY, JSON.stringify(usuario));
}

export function logout() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  const token = getToken();
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options?.headers ?? {}),
      },
    });
  } catch {
    throw new Error("Não foi possível conectar ao servidor. Verifique se o backend está em execução.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
    const detail = typeof err.detail === "string" ? err.detail : "Erro na requisição";

    // Sessão expirada ou inválida: limpa e manda para o login
    if (res.status === 401 && !path.startsWith("/auth/")) {
      logout();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    throw new Error(traduzErro(detail));
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

// Upload de arquivo (multipart/form-data). Não força Content-Type: application/json
// (o browser define o boundary sozinho), mas injeta o token igual ao request().
async function requestUpload<T>(path: string, formData: FormData): Promise<T> {
  let res: Response;
  const token = getToken();
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    });
  } catch {
    throw new Error("Não foi possível conectar ao servidor. Verifique se o backend está em execução.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
    const detail = typeof err.detail === "string" ? err.detail : "Erro na requisição";
    if (res.status === 401) {
      logout();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    throw new Error(traduzErro(detail));
  }
  return res.json();
}

// ── Autenticação ──────────────────────────────────────────────────────────────
export const login = (data: { login: string; senha: string }) =>
  request<any>("/auth/login", { method: "POST", body: JSON.stringify(data) });

export const getMe = () => request<any>("/auth/me");

export const setupNeeded = () => request<{ setup_needed: boolean }>("/auth/setup-needed");

export const setupAdmin = (data: { nome: string; login: string; senha: string }) =>
  request<any>("/auth/setup", { method: "POST", body: JSON.stringify(data) });

// ── Usuários (admin) ──────────────────────────────────────────────────────────
export const getUsuarios = () => request<any[]>("/users/");
export const getUsuario  = (id: number) => request<any>(`/users/${id}`);
export const createUsuario = (data: { nome: string; login: string; senha: string; papel: string }) =>
  request<any>("/users/", { method: "POST", body: JSON.stringify(data) });
export const updateUsuario = (id: number, data: { nome: string; login: string; papel: string; ativo: boolean }) =>
  request<any>(`/users/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const resetSenhaUsuario = (id: number, novaSenha: string) =>
  request<any>(`/users/${id}/reset-password`, { method: "POST", body: JSON.stringify({ nova_senha: novaSenha }) });

// Pessoas
export const getPessoas  = (filter = "") => request<any[]>(`/persons/${qs({ filter })}`);
export const getPessoa   = (id: number)  => request<any>(`/persons/${id}`);
export const createPessoa = (data: { nome: string; documento: string; carteirinha?: string }) =>
  request<any>(`/persons/${qs({ name: data.nome, document: data.documento, biodoc_card: data.carteirinha ?? "" })}`, { method: "POST" });
export const updatePessoa = (id: number, data: { nome: string; documento: string; carteirinha?: string }) =>
  request<any>(`/persons/${id}${qs({ name: data.nome, document: data.documento, biodoc_card: data.carteirinha ?? "" })}`, { method: "PUT" });
export const deletePessoa = (id: number) => request<any>(`/persons/${id}`, { method: "DELETE" });
export const getFotosPessoa = (id: number) => request<{ photos: string[]; folder?: string; folder_path?: string }>(`/persons/${id}/photos`);
export const uploadFotoPessoa = (id: number, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return requestUpload<{ message: string; path: string; filename: string }>(`/persons/${id}/photos`, form);
};
export const deleteFotoPessoa = (id: number, filename: string) =>
  request<any>(`/persons/${id}/photos/${encodeURIComponent(filename)}`, { method: "DELETE" });
export const vincularBiodoc = (personId: number, idCard: string) =>
  request<{ message: string; filename: string; biodoc_name?: string; photos_folder: string }>(
    `/biodoc/vincular/${personId}${qs({ id_card: idCard })}`, { method: "POST" }
  );
// Consulta a Biodoc pela carteirinha SEM salvar nada — usada para pré-preencher
// o nome ao digitar a carteirinha, antes mesmo de a pessoa existir no sistema.
export const consultarBiodoc = (idCard: string) =>
  request<{ status: number; status_descricao: string; name: string; tem_imagem: boolean; release_biometric: boolean }>(
    `/biodoc/consultar/${encodeURIComponent(idCard)}`
  );

// Localizações
export const getLocalizacoes   = (filter = "") => request<any[]>(`/locations/${qs({ filter })}`);
export const getLocalizacao    = (id: number)  => request<any>(`/locations/${id}`);
export const createLocalizacao = (data: { nome: string; mapa_path?: string }) =>
  request<any>(`/locations/${qs({ name: data.nome, map_path: data.mapa_path ?? "" })}`, { method: "POST" });
export const updateLocalizacao = (id: number, data: { nome: string; mapa_path?: string }) =>
  request<any>(`/locations/${id}${qs({ name: data.nome, map_path: data.mapa_path ?? "" })}`, { method: "PUT" });
export const deleteLocalizacao = (id: number) => request<any>(`/locations/${id}`, { method: "DELETE" });
export const uploadMapaLocalizacao = (id: number, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return requestUpload<{ message: string; path: string }>(`/locations/${id}/mapa`, form);
};

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
export const getCamerasCenario = (id: number) => request<any[]>(`/scenarios/${id}/cameras`);
export const addCameraCenario = (cenarioId: number, cameraId: number) =>
  request<any>(`/scenarios/${cenarioId}/cameras/${cameraId}`, { method: "POST" });
export const removeCameraCenario = (cenarioId: number, scenarioCameraId: number) =>
  request<any>(`/scenarios/${cenarioId}/cameras/${scenarioCameraId}`, { method: "DELETE" });

// Parâmetros
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
    biodoc_api_url: data.biodoc_api_url ?? "",
    biodoc_api_token: data.biodoc_api_token ?? "",
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

// Câmeras
export const getCameras   = (filter = "") => request<any[]>(`/cameras/${qs({ filter })}`);
export const getCamera    = (id: number)  => request<any>(`/cameras/${id}`);
export const createCamera = (data: {
  nome: string; idlocalizacao: number; andar?: number;
  nrsalaproxima?: number; notaparaignorar?: number; notaidentificacao?: number;
}) =>
  request<any>(`/cameras/${qs({
    name: data.nome, location_id: data.idlocalizacao,
    floor: data.andar ?? 0, room_number: data.nrsalaproxima ?? 0,
    ignore_threshold: data.notaparaignorar ?? 0.7,
    identification_threshold: data.notaidentificacao ?? 0.7,
  })}`, { method: "POST" });
export const updateCamera = (id: number, data: {
  nome: string; idlocalizacao: number; andar?: number;
  nrsalaproxima?: number; notaparaignorar?: number; notaidentificacao?: number;
}) =>
  request<any>(`/cameras/${id}${qs({
    name: data.nome, location_id: data.idlocalizacao,
    floor: data.andar ?? 0, room_number: data.nrsalaproxima ?? 0,
    ignore_threshold: data.notaparaignorar ?? 0.7,
    identification_threshold: data.notaidentificacao ?? 0.7,
  })}`, { method: "PUT" });
export const deleteCamera = (id: number) => request<any>(`/cameras/${id}`, { method: "DELETE" });

// Tracking / Acompanhamento
export const getAreaTracking = (location_id: number, date_filter: string) =>
  request<any[]>(`/tracking/area${qs({ location_id, date_filter })}`);
export const getPersonPath = (person_id: number, start_date: string, end_date: string, identified_only = true) =>
  request<any[]>(`/tracking/person-path${qs({ person_id, start_date, end_date, identified_only })}`);

// Pessoa — Eventos
type PessoaEventoData = {
  person_id: number; event_id: number; entry_datetime: string;
  expected_exit_datetime?: string | null; actual_exit_datetime?: string | null;
  event_cancelled?: boolean;
};
function pessoaEventoPayload(data: PessoaEventoData) {
  return {
    person_id: data.person_id,
    event_id: data.event_id,
    entry_datetime: data.entry_datetime,
    event_cancelled: data.event_cancelled ?? false,
    expected_exit_datetime: data.expected_exit_datetime ?? "",
    actual_exit_datetime: data.actual_exit_datetime ?? "",
  };
}
export const getPessoaEventos = (person_id?: number) => request<any[]>(`/person-events/${qs({ person_id })}`);
export const getPessoaEvento  = (id: number) => request<any>(`/person-events/${id}`);
export const createPessoaEvento = (data: PessoaEventoData) =>
  request<any>(`/person-events/${qs(pessoaEventoPayload(data))}`, { method: "POST" });
export const updatePessoaEvento = (id: number, data: PessoaEventoData) =>
  request<any>(`/person-events/${id}${qs(pessoaEventoPayload(data))}`, { method: "PUT" });
export const deletePessoaEvento = (id: number) => request<any>(`/person-events/${id}`, { method: "DELETE" });
