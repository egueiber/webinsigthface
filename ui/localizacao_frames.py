
# -*- coding: utf-8 -*-
"""
Módulo das Telas de Localização (Frontend)
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from .widgets import temporary_message

# Imports dos nossos módulos de "Backend"
from services.localizacao_service import (
    listar_localizacoes_db,
    get_localizacao_por_id_db,
    salvar_localizacao_no_banco,
    excluir_localizacao_db
)

# --- Módulo: Lista de Localizações ---
class ListarLocalizacoesFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="Gerenciar Localizações", font=("Arial", 18, "bold")).pack(side="left")
        ttk.Button(top_frame, text="Novo Cadastro +",
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

        cols = ("id", "nome")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nome", width=300)

        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome da Localização")

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
        localizacoes = listar_localizacoes_db(filtro)
        for localizacao in localizacoes:
            self.tree.insert("", "end", values=localizacao)

    def abrir_novo(self):
        self.controller.abrir_edicao_localizacao(None)

    def abrir_edicao(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma localização na lista para editar.")
            return
        dados_localizacao = self.tree.item(selecionado)
        localizacao_id = dados_localizacao["values"][0]
        self.controller.abrir_edicao_localizacao(localizacao_id)

    def excluir(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma localização na lista para excluir.")
            return
        dados_localizacao = self.tree.item(selecionado)
        localizacao_id = dados_localizacao["values"][0]
        nome = dados_localizacao["values"][1]
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{nome}' (ID: {localizacao_id})?"):
            return

        success = excluir_localizacao_db(localizacao_id)

        if success:
            temporary_message(self.controller, "Sucesso", f"'{nome}' foi excluído com sucesso.")
            self.popular_lista()

    def on_show(self):
        self.popular_lista()


# --- Módulo: Cadastro/Edição de Localização ---
class CadastroLocalizacaoFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.localizacao_id_atual = None

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.titulo_label = ttk.Label(top_frame, text="Nova Localização", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")
        ttk.Button(top_frame, text="< Voltar para Lista",
                  command=lambda: controller.show_frame("ListarLocalizacoesFrame")).pack(side="right")

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=20)

        ttk.Label(form_frame, text="Nome da Localização:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.nome_entry = ttk.Entry(form_frame, width=40)
        self.nome_entry.grid(row=0, column=1, padx=5, pady=5)

        self.btn_salvar = ttk.Button(self, text="Salvar", style="Accent.TButton", command=self.salvar)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)

    def carregar_dados(self, localizacao_id):
        self.localizacao_id_atual = localizacao_id
        self.nome_entry.delete(0, tk.END)

        if localizacao_id is None:
            self.titulo_label.config(text="Nova Localização")
        else:
            self.titulo_label.config(text="Editar Localização")
            localizacao_data = get_localizacao_por_id_db(localizacao_id)
            if localizacao_data:
                self.nome_entry.insert(0, localizacao_data.get("nome", ""))

    def salvar(self):
        nome = self.nome_entry.get().strip()
        
        if not nome:
            messagebox.showwarning("Dados Incompletos", "Por favor, preencha o Nome da Localização.")
            return

        success = salvar_localizacao_no_banco(nome, self.localizacao_id_atual)

        if success:
            temporary_message(self.controller, "Sucesso", f"Localização '{nome}' salva com sucesso!")
            self.controller.show_frame("ListarLocalizacoesFrame")

    def on_show(self):
        pass
