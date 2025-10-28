# -*- coding: utf-8 -*-
"""
Módulo de Serviço Facial (Backend)

Lógica de processamento de imagem e visão computacional.
"""
import cv2
import os

PADDING_PIXELS = 60 # Aumenta a área de recorte ao redor do rosto (em pixels)

def gerar_aumentos_de_dados(caminho_pasta):
    print(f"Iniciando aumento de dados para a pasta: {caminho_pasta}")
    arquivos_originais = [f for f in os.listdir(caminho_pasta) if f.endswith(('.jpg', '.png'))]
    
    for nome_arquivo in arquivos_originais:
        caminho_imagem = os.path.join(caminho_pasta, nome_arquivo)
        imagem = cv2.imread(caminho_imagem)
        
        if imagem is None: 
            continue

        nome_base, extensao = os.path.splitext(nome_arquivo)

        imagem_distante_75 = cv2.resize(imagem, (0, 0), fx=0.75, fy=0.75)
        novo_nome_75 = f"{nome_base}_distante_75{extensao}"
        cv2.imwrite(os.path.join(caminho_pasta, novo_nome_75), imagem_distante_75)

        imagem_distante_50 = cv2.resize(imagem, (0, 0), fx=0.5, fy=0.5)
        novo_nome_50 = f"{nome_base}_distante_50{extensao}"
        cv2.imwrite(os.path.join(caminho_pasta, novo_nome_50), imagem_distante_50)

        imagem_desfocada = cv2.GaussianBlur(imagem, (3, 3), 0)
        novo_nome_desfocado = f"{nome_base}_desfocado{extensao}"
        cv2.imwrite(os.path.join(caminho_pasta, novo_nome_desfocado), imagem_desfocada)
        
    print("Aumento de dados concluído.")