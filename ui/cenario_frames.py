# -*- coding: utf-8 -*-
"""
Módulo das Telas de Cenário (Frontend)
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from .widgets import temporary_message

from services.cenario_service import (
    listar_cenarios_db,
    get_cenario_por_id_db,
    salvar_cenario_no_banco,
    excluir_cenario_db,
    get_cameras_para_cenario_db,
    adicionar_camera_cenario_db,
    remover_camera_cenario_db,
    listar_cameras_disponiveis_db,
    listar_parametros_disponiveis_db
)

class ListarCenariosFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="Gerenciar Cenários", font=("Arial", 18, "bold")).pack(side="left")
        ttk.Button(top_frame, text="Novo Cenário +",
                   command=self.abrir_novo, style="Accent.TButton").pack(side="right")

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Buscar por Descrição:").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<Return>", lambda event: self.popular_lista())
        ttk.Button(search_frame, text="Buscar", command=self.popular_lista).pack(side="left", padx=5)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("id", "descricao", "parametro", "ativo", "padrao")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("descricao", width=300)
        self.tree.column("parametro", width=100, anchor="center")
        self.tree.column("ativo", width=80, anchor="center")
        self.tree.column("padrao", width=80, anchor="center")

        self.tree.heading("id", text="ID")
        self.tree.heading("descricao", text="Descrição")
        self.tree.heading("parametro", text="Parâmetro")
        self.tree.heading("ativo", text="Ativo")
        self.tree.heading("padrao", text="Padrão")

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
        cenarios = listar_cenarios_db(filtro)
        for cenario in cenarios:
            self.tree.insert("", "end", values=cenario)

    def abrir_novo(self):
        self.controller.abrir_edicao_cenario(None)

    def abrir_edicao(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione um cenário na lista para editar.")
            return
        dados_cenario = self.tree.item(selecionado)
        cenario_id = dados_cenario["values"][0]
        self.controller.abrir_edicao_cenario(cenario_id)

    def excluir(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione um cenário para excluir.")
            return
        dados_cenario = self.tree.item(selecionado)
        cenario_id = dados_cenario["values"][0]
        descricao = dados_cenario["values"][1]
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o cenário '{descricao}' (ID: {cenario_id})?"):
            return

        success = excluir_cenario_db(cenario_id)
        if success:
            temporary_message(self.controller, "Sucesso", f"Cenário '{descricao}' foi excluído com sucesso.")
            self.popular_lista()

    def on_show(self):
        self.popular_lista()


class CadastroCenarioFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.cenario_id_atual = None

        # --- Topo ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        self.titulo_label = ttk.Label(top_frame, text="Novo Cenário", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")
        ttk.Button(top_frame, text="< Voltar para Lista",
                   command=lambda: controller.show_frame("ListarCenariosFrame")).pack(side="right")

        # --- Formulário Principal ---
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10, padx=20, fill="x")

        ttk.Label(form_frame, text="Descrição:").grid(row=0, column=0, padx=5, pady=8, sticky='e')
        self.descricao_entry = ttk.Entry(form_frame, width=50)
        self.descricao_entry.grid(row=0, column=1, padx=5, pady=8, sticky='w')

        ttk.Label(form_frame, text="Parâmetro:").grid(row=1, column=0, padx=5, pady=8, sticky='e')
        self.parametro_combo = ttk.Combobox(form_frame, state="readonly")
        self.parametro_combo.grid(row=1, column=1, padx=5, pady=8, sticky='w')

        self.ativo_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Ativo", variable=self.ativo_var).grid(row=2, column=1, padx=5, pady=8, sticky='w')
        
        self.padrao_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form_frame, text="Padrão", variable=self.padrao_var).grid(row=2, column=1, padx=5, pady=8, sticky='e')

        # --- Câmeras do Cenário ---
        cameras_frame = ttk.LabelFrame(self, text="Câmeras no Cenário")
        cameras_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # --- Adicionar Câmera ---
        add_camera_frame = ttk.Frame(cameras_frame)
        add_camera_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(add_camera_frame, text="Adicionar Câmera:").pack(side="left")
        self.camera_combo = ttk.Combobox(add_camera_frame, state="readonly", width=40)
        self.camera_combo.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(add_camera_frame, text="Adicionar", command=self.adicionar_camera).pack(side="left", padx=5)

        # --- Lista de Câmeras ---
        tree_frame = ttk.Frame(cameras_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("idcenariocamera", "idcamera", "nomecamera")
        self.tree_cameras = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree_cameras.column("idcenariocamera", width=0, stretch=tk.NO) # Oculto
        self.tree_cameras.column("idcamera", width=50, anchor="center")
        self.tree_cameras.column("nomecamera", width=300)
        self.tree_cameras.heading("idcamera", text="ID Câmera")
        self.tree_cameras.heading("nomecamera", text="Nome da Câmera")
        self.tree_cameras.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_cameras.yview)
        self.tree_cameras.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(cameras_frame, text="Remover Câmera Selecionada", command=self.remover_camera).pack(pady=5)

        # --- Botão Salvar ---
        self.btn_salvar = ttk.Button(self, text="Salvar Cenário", style="Accent.TButton", command=self.salvar_cenario)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)

    def carregar_dados(self, cenario_id):
        self.cenario_id_atual = cenario_id
        self.descricao_entry.delete(0, tk.END)
        self.parametro_combo.set('')
        self.ativo_var.set(True)
        self.padrao_var.set(False)
        self.popular_combos()
        self.limpar_lista_cameras()

        if cenario_id is None:
            self.titulo_label.config(text="Novo Cenário")
        else:
            self.titulo_label.config(text="Editar Cenário")
            cenario_data = get_cenario_por_id_db(cenario_id)
            if cenario_data:
                self.descricao_entry.insert(0, cenario_data["descricao"])
                self.ativo_var.set(cenario_data["ativo"])
                self.padrao_var.set(cenario_data["padrao"])
                
                # Seleciona o parâmetro no combobox
                param_id = cenario_data["idparametro"]
                for i, item in enumerate(self.parametros_list):
                    if item[0] == param_id:
                        self.parametro_combo.current(i)
                        break
                
                self.popular_lista_cameras()

    def popular_combos(self):
        # Parâmetros
        self.parametros_list = listar_parametros_disponiveis_db()
        self.parametro_combo['values'] = [p[1] for p in self.parametros_list]
        
        # Câmeras
        self.cameras_list = listar_cameras_disponiveis_db()
        self.camera_combo['values'] = [c[1] for c in self.cameras_list]

    def popular_lista_cameras(self):
        self.limpar_lista_cameras()
        if self.cenario_id_atual:
            cameras = get_cameras_para_cenario_db(self.cenario_id_atual)
            for cam in cameras:
                self.tree_cameras.insert("", "end", values=cam)

    def limpar_lista_cameras(self):
        for i in self.tree_cameras.get_children():
            self.tree_cameras.delete(i)

    def adicionar_camera(self):
        if not self.cenario_id_atual:
            messagebox.showwarning("Aviso", "Salve o cenário antes de adicionar câmeras.")
            return
        
        idx_camera = self.camera_combo.current()
        if idx_camera == -1:
            messagebox.showwarning("Seleção", "Selecione uma câmera para adicionar.")
            return
        
        camera_id = self.cameras_list[idx_camera][0]
        
        success = adicionar_camera_cenario_db(self.cenario_id_atual, camera_id)
        if success:
            self.popular_lista_cameras()
            self.camera_combo.set('')

    def remover_camera(self):
        selecionado = self.tree_cameras.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione uma câmera na lista para remover.")
            return
        
        item = self.tree_cameras.item(selecionado)
        idcenariocamera = item['values'][0]
        
        success = remover_camera_cenario_db(idcenariocamera)
        if success:
            self.popular_lista_cameras()

    def salvar_cenario(self):
        descricao = self.descricao_entry.get().strip()
        if not descricao:
            messagebox.showwarning("Dados Incompletos", "A descrição do cenário é obrigatória.")
            return

        idx_param = self.parametro_combo.current()
        if idx_param == -1:
            messagebox.showwarning("Dados Incompletos", "Selecione um parâmetro.")
            return
        parametro_id = self.parametros_list[idx_param][0]
        
        ativo = self.ativo_var.get()
        padrao = self.padrao_var.get()

        novo_cenario_id = salvar_cenario_no_banco(descricao, parametro_id, ativo, padrao, self.cenario_id_atual)

        if novo_cenario_id:
            if not self.cenario_id_atual: # Se era um novo cenário
                self.cenario_id_atual = novo_cenario_id
                temporary_message(self.controller, "Sucesso", f"Cenário '{descricao}' salvo. Agora você pode adicionar câmeras.")
                self.carregar_dados(novo_cenario_id) # Recarrega para habilitar a adição de câmeras
            else:
                temporary_message(self.controller, "Sucesso", f"Cenário '{descricao}' atualizado com sucesso.")
                self.controller.show_frame("ListarCenariosFrame")

    def on_show(self, cenario_id=None):
        self.carregar_dados(cenario_id)
