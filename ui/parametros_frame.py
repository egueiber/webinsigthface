# -*- coding: utf-8 -*-
"""
Módulo das Telas de Parâmetros (Frontend)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from .widgets import temporary_message
from backend.services.config_service import (
    list_parameters,
    get_parameter_by_id,
    save_parameters,
    delete_parameter
)

class ListarParametrosFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="Gerenciar Parâmetros", font=("Arial", 18, "bold")).pack(side="left")
        ttk.Button(top_frame, text="Novo Parâmetro +",
                   command=self.abrir_novo, style="Accent.TButton").pack(side="right")

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Buscar por Nome:").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<Return>", lambda event: self.popular_lista())
        ttk.Button(search_frame, text="Buscar", command=self.popular_lista).pack(side="left", padx=5)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("nome", "id")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("nome", width=400)
        self.tree.column("id", width=80, anchor="center")

        self.tree.heading("nome", text="Nome do Parâmetro")
        self.tree.heading("id", text="ID")

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(action_frame, text="Editar Selecionado",
                   command=self.abrir_edicao).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Excluir Selecionado",
                   command=self.excluir).pack(side="right", padx=5)

    def popular_lista(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        filtro = self.search_entry.get()
        parametros = list_parameters(filtro)
        for param in parametros:
            # Invertendo a ordem para (nome, id)
            self.tree.insert("", "end", values=(param[1], param[0]))

    def abrir_novo(self):
        self.controller.abrir_edicao_parametro(None)

    def abrir_edicao(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione um parâmetro para editar.")
            return
        dados = self.tree.item(selecionado)
        param_id = dados["values"][1]
        self.controller.abrir_edicao_parametro(param_id)

    def excluir(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione um parâmetro para excluir.")
            return
        dados = self.tree.item(selecionado)
        param_id = dados["values"][1]
        nome = dados["values"][0]
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o parâmetro '{nome}' (ID: {param_id})?"):
            return

        if delete_parameter(param_id):
            temporary_message(self.controller, "Sucesso", f"Parâmetro '{nome}' foi excluído.")
            self.popular_lista()

    def on_show(self):
        self.popular_lista()


class CadastroParametroFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.param_id_atual = None
        
        self.var_gerar_marcoes = tk.BooleanVar()
        self.var_finalizaraoidentificartodos = tk.BooleanVar()

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        self.titulo_label = ttk.Label(top_frame, text="Novo Parâmetro", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")
        ttk.Button(top_frame, text="< Voltar para Lista",
                   command=lambda: controller.show_frame("ListarParametrosFrame")).pack(side="right")
        
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10, padx=20, fill="x")

        ttk.Label(form_frame, text="Nome do Parâmetro:").grid(row=0, column=0, padx=5, pady=8, sticky='e')
        self.nome_entry = ttk.Entry(form_frame, width=80)
        self.nome_entry.grid(row=0, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Caminho Fotos Clientes:").grid(row=1, column=0, padx=5, pady=8, sticky='e')
        self.fotos_entry = ttk.Entry(form_frame, width=80)
        self.fotos_entry.grid(row=1, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Caminho Mapas Câmeras:").grid(row=2, column=0, padx=5, pady=8, sticky='e')
        self.mapas_entry = ttk.Entry(form_frame, width=80)
        self.mapas_entry.grid(row=2, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Caminho Vídeos a Processar:").grid(row=3, column=0, padx=5, pady=8, sticky='e')
        self.videos_a_processar_entry = ttk.Entry(form_frame, width=80)
        self.videos_a_processar_entry.grid(row=3, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Caminho Vídeos Processados:").grid(row=4, column=0, padx=5, pady=8, sticky='e')
        self.videos_processados_entry = ttk.Entry(form_frame, width=80)
        self.videos_processados_entry.grid(row=4, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Caminho Vídeo Marcações:").grid(row=5, column=0, padx=5, pady=8, sticky='e')
        self.video_marcoes_entry = ttk.Entry(form_frame, width=80)
        self.video_marcoes_entry.grid(row=5, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Configurações:").grid(row=6, column=0, padx=5, pady=15, sticky='ne')
        
        config_frame = ttk.Frame(form_frame)
        config_frame.grid(row=6, column=1, sticky='w', padx=5, pady=10)

        ttk.Label(config_frame, text="Intervalo Frames:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.intervalo_frames_entry = ttk.Entry(config_frame, width=10)
        self.intervalo_frames_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(config_frame, text="Escala Imagem (ex: 1.0):").grid(row=0, column=2, padx=10, pady=5, sticky='e')
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
        
        self.finalizaraoidentificartodos_check = ttk.Checkbutton(config_frame, text="Finalizar ao identificar todos com eventos ativos",
                                                  variable=self.var_finalizaraoidentificartodos)
        self.finalizaraoidentificartodos_check.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky='w')

        self.btn_salvar = ttk.Button(self, text="Salvar Parâmetros", style="Accent.TButton", command=self.salvar)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)
        
    def carregar_dados(self, param_id):
        self.param_id_atual = param_id
        self._limpar_campos()

        if param_id is None:
            self.titulo_label.config(text="Novo Parâmetro")
            self.var_gerar_marcoes.set(False)
            self.var_finalizaraoidentificartodos.set(False)
        else:
            self.titulo_label.config(text="Editar Parâmetro")
            params = get_parameter_by_id(param_id)
            if params:
                self.nome_entry.insert(0, params.get("nome", ""))
                self.fotos_entry.insert(0, params.get("fotos", ""))
                self.mapas_entry.insert(0, params.get("mapas", ""))
                self.videos_a_processar_entry.insert(0, params.get("videos_a_processar", ""))
                self.videos_processados_entry.insert(0, params.get("videos_processados", ""))
                self.video_marcoes_entry.insert(0, params.get("video_marcoes", ""))
                self.intervalo_frames_entry.insert(0, params.get("intervalo_frames", 15))
                self.escala_imagem_entry.insert(0, params.get("escala_imagem", 1.0))
                self.tolerancia_entry.insert(0, params.get("tolerancia", 0.6))
                self.modelo_deteccao_entry.insert(0, params.get("modelo_deteccao", "hog"))
                self.var_gerar_marcoes.set(params.get("gerar_marcoes", False))
                self.var_finalizaraoidentificartodos.set(params.get("finalizaraoidentificartodos", False))

    def _limpar_campos(self):
        self.nome_entry.delete(0, tk.END)
        self.fotos_entry.delete(0, tk.END)
        self.mapas_entry.delete(0, tk.END)
        self.videos_a_processar_entry.delete(0, tk.END)
        self.videos_processados_entry.delete(0, tk.END)
        self.video_marcoes_entry.delete(0, tk.END)
        self.intervalo_frames_entry.delete(0, tk.END)
        self.escala_imagem_entry.delete(0, tk.END)
        self.tolerancia_entry.delete(0, tk.END)
        self.modelo_deteccao_entry.delete(0, tk.END)
        
    def salvar(self):
        nome = self.nome_entry.get().strip()
        if not nome:
            messagebox.showwarning("Dados Incompletos", "O nome do parâmetro é obrigatório.")
            return

        try:
            param_data = {
                "nome": nome,
                "fotos": self.fotos_entry.get().strip(),
                "mapas": self.mapas_entry.get().strip(),
                "videos_a_processar": self.videos_a_processar_entry.get().strip(),
                "videos_processados": self.videos_processados_entry.get().strip(),
                "video_marcoes": self.video_marcoes_entry.get().strip(),
                "modelo_deteccao": self.modelo_deteccao_entry.get().strip(),
                "intervalo_frames": int(self.intervalo_frames_entry.get().strip()),
                "escala_imagem": float(self.escala_imagem_entry.get().strip()),
                "tolerancia": float(self.tolerancia_entry.get().strip()),
                "gerar_marcoes": self.var_gerar_marcoes.get(),
                "finalizaraoidentificartodos": self.var_finalizaraoidentificartodos.get()
            }
        except ValueError as e:
            messagebox.showerror("Erro de Validação", f"Erro ao converter valores numéricos: {e}")
            return

        if not all(param_data[k] for k in ["fotos", "mapas", "videos_a_processar", "videos_processados", "video_marcoes", "modelo_deteccao"]):
            messagebox.showwarning("Dados Incompletos", "Todos os campos de texto/caminho são obrigatórios.")
            return

        novo_id = save_parameters(param_data, self.param_id_atual)
        
        if novo_id:
            # Se for um novo parâmetro, o ID global de parâmetros da aplicação
            # pode precisar ser recarregado se for o único/primeiro.
            if self.controller.parametros is None or self.controller.parametros.get('id') == novo_id:
                 self.controller.recarregar_parametros()

            msg = f"Parâmetro '{nome}' atualizado." if self.param_id_atual else f"Parâmetro '{nome}' criado."
            temporary_message(self.controller, "Sucesso", msg)
            self.controller.show_frame("ListarParametrosFrame")
        
    def on_show(self, param_id=None):
        self.carregar_dados(param_id)