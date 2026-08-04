# -*- coding: utf-8 -*-
"""
Recorte (crop) de rosto para fotos vindas da Biodoc.

Algumas imagens da Biodoc trazem a pessoa de corpo inteiro ou de longe, o que
deixa o rosto pequeno demais e prejudica o reconhecimento facial do motor.
Este modulo detecta o rosto principal e recorta ao redor dele, com uma margem.

Estrategia de deteccao, em ordem:
  1. face_recognition (dlib HOG) - mais preciso, ja usado pelo motor
  2. OpenCV Haar cascade - fallback, embutido no proprio opencv

Se nenhum rosto for detectado, a imagem ORIGINAL e mantida. A ideia e nunca
piorar o que ja existe: sem deteccao confiavel, e melhor guardar a foto
inteira do que arriscar um recorte errado.
"""
import os
import cv2

# Margem ao redor do rosto, em % do tamanho do rosto detectado.
# Reconhecimento facial funciona melhor com um pouco de testa/queixo/orelhas,
# nao apenas o retangulo justo do rosto.
MARGEM_PERCENTUAL = 0.45

# Se o rosto detectado ocupar mais que isso da largura da imagem, a foto ja
# esta enquadrada (tipo foto 3x4) e nao vale a pena recortar.
LARGURA_MAXIMA_SEM_CROP = 0.55

# Resolucao minima do rosto recortado. Abaixo disso o recorte e ampliado,
# porque rosto muito pequeno perde detalhe no reconhecimento.
LADO_MINIMO_SAIDA = 224


def _detectar_face_recognition(img_rgb):
    """Tenta detectar via dlib HOG. Retorna lista de (x, y, w, h)."""
    try:
        import face_recognition
    except ImportError:
        return []
    try:
        # model="hog" e rapido e suficiente para foto de documento
        deteccoes = face_recognition.face_locations(img_rgb, model="hog")
        # face_recognition devolve (top, right, bottom, left)
        return [(l, t, r - l, b - t) for (t, r, b, l) in deteccoes]
    except Exception:
        return []


def _detectar_haar(img_bgr):
    """Fallback com Haar cascade do proprio OpenCV."""
    try:
        caminho = os.path.join(cv2.data.haarcascades,
                               "haarcascade_frontalface_default.xml")
        cascade = cv2.CascadeClassifier(caminho)
        if cascade.empty():
            return []
        cinza = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        # Sem equalizeHist: testado e comprovado que ele PIORA a deteccao
        # justamente no caso que interessa aqui (rosto pequeno / de longe).
        faces = cascade.detectMultiScale(
            cinza, scaleFactor=1.1, minNeighbors=4, minSize=(24, 24)
        )
        return [tuple(f) for f in faces]
    except Exception:
        return []


def detectar_rostos(img_bgr):
    """
    Detecta rostos na imagem (BGR, formato do OpenCV).
    Retorna lista de (x, y, w, h), ordenada do maior para o menor.
    """
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    faces = _detectar_face_recognition(img_rgb)
    if not faces:
        faces = _detectar_haar(img_bgr)

    # Maior rosto primeiro: em foto com mais de uma pessoa, o titular
    # normalmente e o que aparece maior / mais a frente.
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    return faces


def recortar_rosto(caminho_imagem, caminho_saida=None):
    """
    Recorta o rosto principal da imagem e salva.

    Se caminho_saida for None, sobrescreve a imagem original.

    Retorna dict com:
      - recortado (bool): se houve recorte de fato
      - motivo (str): explicacao quando nao recortou
      - faces_detectadas (int)
    """
    resultado = {"recortado": False, "motivo": "", "faces_detectadas": 0}

    img = cv2.imread(caminho_imagem)
    if img is None:
        resultado["motivo"] = "Nao foi possivel ler a imagem."
        return resultado

    altura, largura = img.shape[:2]
    faces = detectar_rostos(img)
    resultado["faces_detectadas"] = len(faces)

    if not faces:
        # Sem deteccao: mantem a original, nao arrisca recorte errado.
        resultado["motivo"] = "Nenhum rosto detectado; imagem original mantida."
        return resultado

    x, y, w, h = faces[0]

    # Ja esta enquadrada? Nao mexe.
    if w / largura > LARGURA_MAXIMA_SEM_CROP:
        resultado["motivo"] = "Rosto ja ocupa boa parte da imagem; recorte dispensado."
        return resultado

    # Aplica margem ao redor do rosto
    margem_x = int(w * MARGEM_PERCENTUAL)
    margem_y = int(h * MARGEM_PERCENTUAL)

    x1 = max(0, x - margem_x)
    y1 = max(0, y - margem_y)
    x2 = min(largura, x + w + margem_x)
    y2 = min(altura, y + h + margem_y)

    recorte = img[y1:y2, x1:x2]
    if recorte.size == 0:
        resultado["motivo"] = "Recorte resultou vazio; imagem original mantida."
        return resultado

    # Amplia se o recorte ficou pequeno demais
    rec_h, rec_w = recorte.shape[:2]
    menor_lado = min(rec_h, rec_w)
    if menor_lado < LADO_MINIMO_SAIDA:
        escala = LADO_MINIMO_SAIDA / menor_lado
        recorte = cv2.resize(
            recorte, (int(rec_w * escala), int(rec_h * escala)),
            interpolation=cv2.INTER_CUBIC,
        )

    destino = caminho_saida or caminho_imagem
    ok = cv2.imwrite(destino, recorte)
    if not ok:
        resultado["motivo"] = "Falha ao gravar a imagem recortada."
        return resultado

    resultado["recortado"] = True
    return resultado
