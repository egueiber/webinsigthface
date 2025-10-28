# -*- coding: utf-8 -*-
"""
Ponto de Entrada Principal da Aplicação

Este script inicializa os serviços de backend e
inicia a interface gráfica (frontend).
"""
import tkinter as tk
from tkinter import messagebox
from sys import exit

# Importa o inicializador de parâmetros (backend)
from services.config_service import inicializar_db_parametros

# Importa a classe principal da aplicação (frontend)
from ui.app_principal import AppPrincipal

if __name__ == "__main__":
    
    # 1. Tenta inicializar/verificar os parâmetros do banco
    try:
        inicializar_db_parametros()
    except Exception as e:
        messagebox.showerror("Erro Crítico de Inicialização", 
                             f"Não foi possível inicializar os parâmetros do banco.\n"
                             f"Verifique a conexão e a estrutura das tabelas.\n\nErro: {e}")
        exit() # Sai se não puder inicializar
        
    # 2. Cria e inicia a aplicação
    try:
        app = AppPrincipal()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Erro Inesperado", 
                             f"A aplicação encontrou um erro fatal:\n{e}")