
# -*- coding: utf-8 -*-
"""
Módulo das Telas de Evento (Frontend)
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from .widgets import temporary_message

# Imports dos nossos módulos de "Backend"
from services.evento_service import (
    listar_eventos_db,
    get_evento_por_id_db,
    salvar_evento_no_banco,
    excluir_evento_db
)

# --- Módulo: Lista de Eventos ---
class ListarEventosFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="Gerenciar Eventos", font=("Arial", 18, "bold")).pack(side="left")
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

        cols = ("id", "nome", "duracao")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nome", width=300)
        self.tree.column("duracao", width=150, anchor="center")

        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome do Evento")
        self.tree.heading("duracao", text="Duração (minutos)")

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
        eventos = listar_eventos_db(filtro)
        for evento in eventos:
            self.tree.insert("", "end", values=evento)

    def abrir_novo(self):
        self.controller.abrir_edicao_evento(None)

    def abrir_edicao(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione um evento na lista para editar.")
            return
        dados_evento = self.tree.item(selecionado)
        evento_id = dados_evento["values"][0]
        self.controller.abrir_edicao_evento(evento_id)

    def excluir(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione um evento na lista para excluir.")
            return
        dados_evento = self.tree.item(selecionado)
        evento_id = dados_evento["values"][0]
        nome = dados_evento["values"][1]
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{nome}' (ID: {evento_id})?"):
            return

        success = excluir_evento_db(evento_id)

        if success:
            temporary_message(self.controller, "Sucesso", f"'{nome}' foi excluído com sucesso.")
            self.popular_lista()

    def on_show(self):
        self.popular_lista()


# --- Módulo: Cadastro/Edição de Evento ---
class CadastroEventoFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.evento_id_atual = None

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.titulo_label = ttk.Label(top_frame, text="Novo Evento", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")
        ttk.Button(top_frame, text="< Voltar para Lista",
                  command=lambda: controller.show_frame("ListarEventosFrame")).pack(side="right")

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=20)

        ttk.Label(form_frame, text="Nome do Evento:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.nome_entry = ttk.Entry(form_frame, width=40)
        self.nome_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Duração (minutos):").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.duracao_entry = ttk.Entry(form_frame, width=20)
        self.duracao_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        self.btn_salvar = ttk.Button(self, text="Salvar", style="Accent.TButton", command=self.salvar)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)

    def carregar_dados(self, evento_id):
        self.evento_id_atual = evento_id
        self.nome_entry.delete(0, tk.END)
        self.duracao_entry.delete(0, tk.END)

        if evento_id is None:
            self.titulo_label.config(text="Novo Evento")
        else:
            self.titulo_label.config(text="Editar Evento")
            evento_data = get_evento_por_id_db(evento_id)
            if evento_data:
                self.nome_entry.insert(0, evento_data.get("nome", ""))
                duracao = evento_data.get("duracao")
                if duracao is not None:
                    self.duracao_entry.insert(0, str(duracao))

    def salvar(self):
        nome = self.nome_entry.get().strip()
        duracao_str = self.duracao_entry.get().strip()

        if not nome:
            messagebox.showwarning("Dados Incompletos", "Por favor, preencha o Nome do Evento.")
            return

        duracao = None
        if duracao_str:
            try:
                duracao = int(duracao_str)
            except ValueError:
                messagebox.showwarning("Dado Inválido", "A duração deve ser um número inteiro.")
                return

        success = salvar_evento_no_banco(nome, duracao, self.evento_id_atual)

        if success:
            temporary_message(self.controller, "Sucesso", f"Evento '{nome}' salvo com sucesso!")
            self.controller.show_frame("ListarEventosFrame")

    def on_show(self):
        pass
