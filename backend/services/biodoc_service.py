"""
Servico de integracao com a API da Biodoc.
Busca a foto biometrica de um beneficiario pela carteirinha.

A URL e o token sao lidos da tabela tb_parametro (campos biodocapiurl e
biodocapitoken) do parametro marcado como padrao. Isso permite configurar
a integracao pela interface, sem depender de variavel de ambiente.
"""
import os
import base64
import requests
from backend.services.database_service import get_biodoc_config


def _get_config():
    """Le URL e token do banco (parametro padrao)."""
    cfg = get_biodoc_config()
    url   = (cfg.get("url") or "").strip().rstrip("/")
    token = (cfg.get("token") or "").strip()
    return token, url


def buscar_imagem_principal(id_card: str, procedure: str = None):
    """
    GET /card/integration/mainimage
    Retorna dict: status, name, base64_image, main_image_url, release_biometric
    """
    token, base_url = _get_config()
    if not base_url:
        raise ValueError("URL da Biodoc nao configurada. Preencha o campo nos Parametros.")
    if not token:
        raise ValueError("Token da Biodoc nao configurado. Preencha o campo nos Parametros.")

    params = {"idCard": id_card}
    if procedure:
        params["procedure"] = procedure

    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(
        f"{base_url}/card/integration/mainimage",
        params=params, headers=headers, timeout=30,
    )

    if resp.status_code == 401:
        raise PermissionError("Token da Biodoc invalido ou expirado.")
    if resp.status_code == 403:
        raise PermissionError("Acesso nao permitido pela Biodoc.")
    if resp.status_code != 200:
        raise RuntimeError(f"Erro na Biodoc (HTTP {resp.status_code}): {resp.text}")

    payload = resp.json()
    data = payload.get("data", payload)

    return {
        "status":            data.get("cardStatus"),
        "name":              data.get("name"),
        "base64_image":      data.get("base64Image"),
        "main_image_url":    data.get("mainImage"),
        "release_biometric": data.get("releaseBiometric", False),
    }


def salvar_imagem_base64(base64_str: str, destino: str):
    """Decodifica base64 e salva no caminho. Remove prefixo data: se houver."""
    if not base64_str:
        raise ValueError("A Biodoc nao retornou imagem para esta carteirinha.")

    if "," in base64_str and base64_str.strip().startswith("data:"):
        base64_str = base64_str.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(base64_str)
    except Exception as e:
        raise ValueError(f"Imagem base64 invalida: {e}")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "wb") as f:
        f.write(img_bytes)
    return destino


# Mapa de status do cartao (enum da Biodoc)
STATUS_CARTAO = {
    1: "Biometria com imagem",
    2: "Beneficiario nao cadastrado",
    3: "Biometria sem imagem",
    4: "Solicitacao de troca de imagem obrigatoria",
    5: "Alteracao de biometria pendente",
    6: "Alteracao de biometria obrigatoria pendente",
}
