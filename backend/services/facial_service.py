# -*- coding: utf-8 -*-
"""
Módulo de Serviço Facial (Backend)

Lógica de processamento de imagem e visão computacional.
"""
import cv2
import os

PADDING_PIXELS = 60  # Aumenta a área de recorte ao redor do rosto (em pixels)


def generate_data_augmentations(folder_path: str):
    print(f"[INFO] Iniciando aumento de dados para a pasta: {folder_path}")
    original_files = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png'))]

    for filename in original_files:
        image_path = os.path.join(folder_path, filename)
        image = cv2.imread(image_path)

        if image is None:
            continue

        base_name, extension = os.path.splitext(filename)

        # Redimensiona para 75%
        image_distant_75 = cv2.resize(image, (0, 0), fx=0.75, fy=0.75)
        new_name_75 = f"{base_name}_distant_75{extension}"
        cv2.imwrite(os.path.join(folder_path, new_name_75), image_distant_75)

        # Redimensiona para 50%
        image_distant_50 = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)
        new_name_50 = f"{base_name}_distant_50{extension}"
        cv2.imwrite(os.path.join(folder_path, new_name_50), image_distant_50)

        # Aplica desfoque gaussiano
        image_blurred = cv2.GaussianBlur(image, (3, 3), 0)
        new_name_blurred = f"{base_name}_blurred{extension}"
        cv2.imwrite(os.path.join(folder_path, new_name_blurred), image_blurred)

    print("[INFO] Aumento de dados concluído.")