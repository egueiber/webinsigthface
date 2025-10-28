# -*- coding: utf-8 -*-
"""
Módulo da Tela de Parâmetros (Frontend)
"""
import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox

# (NOVO) Imports dos nossos módulos de "Backend"
from services.config_service import salvar_parametros_db

class ParametrosFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        
        self.var_gerar_marcoes = tk.BooleanVar()
        
        titulo_label = ttk.Label(self, text="Parâmetros do Sistema", font=("Arial", 18, "bold"))
        titulo_label.pack(pady=20)
        
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10, padx=20, fill="x")

        ttk.Label(form_frame, text="Caminho Fotos Clientes:").grid(row=0, column=0, padx=5, pady=8, sticky='e')
        self.fotos_entry = ttk.Entry(form_frame, width=80)
        self.fotos_entry.grid(row=0, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Caminho Mapas Câmeras:").grid(row=1, column=0, padx=5, pady=8, sticky='e')
        self.mapas_entry = ttk.Entry(form_frame, width=80)
        self.mapas_entry.grid(row=1, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Caminho Vídeos a Processar:").grid(row=2, column=0, padx=5, pady=8, sticky='e')
        self.videos_a_processar_entry = ttk.Entry(form_frame, width=80)
        self.videos_a_processar_entry.grid(row=2, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Caminho Vídeos Processados:").grid(row=3, column=0, padx=5, pady=8, sticky='e')
        self.videos_processados_entry = ttk.Entry(form_frame, width=80)
        self.videos_processados_entry.grid(row=3, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Caminho Vídeo Marcações:").grid(row=4, column=0, padx=5, pady=8, sticky='e')
        self.video_marcoes_entry = ttk.Entry(form_frame, width=80)
        self.video_marcoes_entry.grid(row=4, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Configurações:").grid(row=5, column=0, padx=5, pady=15, sticky='ne')
        
        config_frame = ttk.Frame(form_frame)
        config_frame.grid(row=5, column=1, sticky='w', padx=5, pady=10)

        ttk.Label(config_frame, text="Intervalo Frames:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.intervalo_frames_entry = ttk.Entry(config_frame, width=10)
        self.intervalo_frames_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(config_frame, text="Escala Imagem (ex: 1):").grid(row=0, column=2, padx=10, pady=5, sticky='e')
        self.escala_imagem_entry = ttk.Entry(config_frame, width=10)
        self.escala_imagem_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Tolerância (ex: 0.6):").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.tolerancia_entry = ttk.Entry(config_frame, width=10)
        self.tolerancia_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Modelo Detecção (hog/cnn):").grid(row=1, column=2, padx=10, pady=5, sticky='e')
        self.modelo_deteccao_entry = ttk.Entry(config_frame, width=10)
        self.modelo_deteccao_entry.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Processamento:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.gerar_marcoes_check = ttk.Checkbutton(config_frame, text="Gerar Vídeo com Marcações",
                                                  variable=self.var_gerar_marcoes)
        self.gerar_marcoes_check.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky='w')

        
        self.btn_salvar = ttk.Button(self, text="Salvar Parâmetros", style="Accent.TButton", command=self.salvar_parametros)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)
        
        self.carregar_dados()
        
    def carregar_dados(self):
        """Carrega os parâmetros atuais do controlador."""
        params = self.controller.parametros
        
        self.fotos_entry.delete(0, tk.END)
        self.mapas_entry.delete(0, tk.END)
        self.videos_a_processar_entry.delete(0, tk.END)
        self.videos_processados_entry.delete(0, tk.END)
        self.video_marcoes_entry.delete(0, tk.END)
        self.intervalo_frames_entry.delete(0, tk.END)
        self.escala_imagem_entry.delete(0, tk.END)
        self.tolerancia_entry.delete(0, tk.END)
        self.modelo_deteccao_entry.delete(0, tk.END)
        
        if params:
            self.fotos_entry.insert(0, params.get("fotos", ""))
            self.mapas_entry.insert(0, params.get("mapas", ""))
            self.videos_a_processar_entry.insert(0, params.get("videos_a_processar", ""))
            self.videos_processados_entry.insert(0, params.get("videos_processados", ""))
            self.video_marcoes_entry.insert(0, params.get("video_marcoes", ""))
            self.intervalo_frames_entry.insert(0, params.get("intervalo_frames", 15))
            self.escala_imagem_entry.insert(0, params.get("escala_imagem", 1))
            self.tolerancia_entry.insert(0, params.get("tolerancia", 0.6))
            self.modelo_deteccao_entry.insert(0, params.get("modelo_deteccao", "hog"))
            self.var_gerar_marcoes.set(params.get("gerar_marcoes", False))
        
    def salvar_parametros(self):
        param_id = self.controller.parametros.get("id")
        if not param_id:
            messagebox.showerror("Erro", "Não foi possível identificar o ID dos parâmetros.")
            return
            
        fotos = self.fotos_entry.get().strip()
        mapas = self.mapas_entry.get().strip()
        videos_a_processar = self.videos_a_processar_entry.get().strip()
        videos_processados = self.videos_processados_entry.get().strip()
        video_marcoes = self.video_marcoes_entry.get().strip()
        modelo_deteccao = self.modelo_deteccao_entry.get().strip()

        if not all([fotos, mapas, videos_a_processar, videos_processados, video_marcoes, modelo_deteccao]):
            messagebox.showwarning("Dados Incompletos", "Todos os campos de texto/caminho são obrigatórios.")
            return

        try:
            intervalo_frames = int(self.intervalo_frames_entry.get().strip())
            escala_imagem = int(self.escala_imagem_entry.get().strip())
            tolerancia = float(self.tolerancia_entry.get().strip())
        except ValueError as e:
            messagebox.showerror("Erro de Validação", 
                                 f"Erro ao converter valores numéricos:\n{e}\n\n"
                                 "Verifique 'Intervalo Frames', 'Escala Imagem' (inteiros) e 'Tolerância' (float).")
            return
            
        gerar_marcoes = self.var_gerar_marcoes.get()

        success = salvar_parametros_db( # (MODIFICADO) Chama o serviço
            param_id, fotos, mapas, videos_a_processar, videos_processados,
            video_marcoes, intervalo_frames, escala_imagem, 
            modelo_deteccao, tolerancia, gerar_marcoes
        )
        
        if success:
            self.controller.recarregar_parametros()
            messagebox.showinfo("Sucesso", "Parâmetros atualizados com sucesso!")
        
    def on_show(self):
        """Chamado pelo show_frame para garantir que os dados estejam atualizados."""
        self.carregar_dados()