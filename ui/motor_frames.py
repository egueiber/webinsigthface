# -*- coding: utf-8 -*-
"""
Módulo das Telas de Motor (Frontend)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from ui.widgets import temporary_message
import json

from services.database_service import (
    listar_motores_db,
    get_motor_por_id_db,
    salvar_motor_no_banco,
    excluir_motor_db
)

class ListarMotoresFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="Gerenciar Motores", font=("Arial", 18, "bold")).pack(side="left")
        ttk.Button(top_frame, text="Novo Motor +",
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

        cols = ("id", "nome", "versao", "ativo", "padrao")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nome", width=250)
        self.tree.column("versao", width=100, anchor="center")
        self.tree.column("ativo", width=100, anchor="center")
        self.tree.column("padrao", width=80, anchor="center")

        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome do Motor")
        self.tree.heading("versao", text="Versão")
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
        motores = listar_motores_db(filtro)
        for motor in motores:
            self.tree.insert("", "end", values=motor)

    def abrir_novo(self):
        self.controller.abrir_edicao_motor(None)

    def abrir_edicao(self):
        selecionados = self.tree.selection()
        if not selecionados:
            messagebox.showwarning("Seleção", "Por favor, selecione um motor na lista para editar.")
            return
        selecionado = selecionados[0]
        dados_motor = self.tree.item(selecionado)
        motor_id = dados_motor.get("values", [None])[0]
        self.controller.abrir_edicao_motor(motor_id)

    def excluir(self):
        selecionados = self.tree.selection()
        if not selecionados:
            messagebox.showwarning("Seleção", "Por favor, selecione um motor na lista para excluir.")
            return
        selecionado = selecionados[0]
        dados_motor = self.tree.item(selecionado)
        valores = dados_motor.get("values", [])
        motor_id = valores[0] if len(valores) > 0 else None
        nome = valores[1] if len(valores) > 1 else ""
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o motor '{nome}' (ID: {motor_id})?"):
            return
        
        success = excluir_motor_db(motor_id)
        if success:
            temporary_message(self.controller, "Sucesso", f"Motor '{nome}' foi excluído com sucesso.")
            self.popular_lista()

    def on_show(self):
        self.popular_lista()


class CadastroMotorFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.motor_id_atual = None

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.titulo_label = ttk.Label(top_frame, text="Novo Motor", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")
        ttk.Button(top_frame, text="< Voltar para Lista",
                   command=lambda: controller.show_frame("ListarMotoresFrame")).pack(side="right")

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10, padx=20)

        ttk.Label(form_frame, text="Nome do Motor:").grid(row=0, column=0, padx=5, pady=8, sticky='e')
        self.nome_entry = ttk.Entry(form_frame, width=40)
        self.nome_entry.grid(row=0, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Versão:").grid(row=1, column=0, padx=5, pady=8, sticky='e')
        self.versao_entry = ttk.Entry(form_frame, width=10)
        self.versao_entry.grid(row=1, column=1, padx=5, pady=8, sticky='w')

        ttk.Label(form_frame, text="Função Chamada:").grid(row=2, column=0, padx=5, pady=8, sticky='e')
        self.funcao_entry = ttk.Entry(form_frame, width=40)
        self.funcao_entry.grid(row=2, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Método:").grid(row=3, column=0, padx=5, pady=8, sticky='e')
        self.metodo_entry = ttk.Entry(form_frame, width=40)
        self.metodo_entry.grid(row=3, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Arquivo Externo:").grid(row=4, column=0, padx=5, pady=8, sticky='e')
        self.arquivo_externo_entry = ttk.Entry(form_frame, width=40)
        self.arquivo_externo_entry.grid(row=4, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="JSON Interno:").grid(row=5, column=0, padx=5, pady=8, sticky='ne')
        self.json_interno_text = tk.Text(form_frame, width=40, height=5)
        self.json_interno_text.grid(row=5, column=1, padx=5, pady=8)

        self.ativo_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Ativo", variable=self.ativo_var).grid(row=6, column=1, padx=5, pady=8, sticky='w')

        # Campo novo: padrao (apenas um registro pode ser padrão)
        self.padrao_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form_frame, text="Padrão", variable=self.padrao_var).grid(row=7, column=1, padx=5, pady=8, sticky='w')

        self.btn_salvar = ttk.Button(self, text="Salvar Cadastro", style="Accent.TButton", command=self.salvar_motor)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)

    def carregar_dados(self, motor_id):
        self.motor_id_atual = motor_id
        self.nome_entry.delete(0, tk.END)
        self.versao_entry.delete(0, tk.END)
        self.funcao_entry.delete(0, tk.END)
        self.metodo_entry.delete(0, tk.END)
        self.arquivo_externo_entry.delete(0, tk.END)
        self.json_interno_text.delete("1.0", tk.END)
        self.ativo_var.set(True)

        if motor_id is None:
            self.titulo_label.config(text="Novo Motor")
            self.btn_salvar.config(text="Salvar Novo Motor")
        else:
            self.titulo_label.config(text="Editar Motor")
            self.btn_salvar.config(text="Salvar Alterações")
            motor_data = get_motor_por_id_db(self.motor_id_atual)

            if motor_data:
                # Garante que os valores inseridos no Entry sejam strings
                self.nome_entry.insert(0, str(motor_data.get("nomemotor", "")))
                self.versao_entry.insert(0, str(motor_data.get("numversao", "")))
                self.funcao_entry.insert(0, str(motor_data.get("nomefuncaochamada", "")))
                self.metodo_entry.insert(0, str(motor_data.get("nomemetodo", "")))
                self.arquivo_externo_entry.insert(0, str(motor_data.get("nomearquivoexterno", "")))

                json_content = motor_data.get("nomearquivojsonerno")
                if json_content:
                    self.json_interno_text.insert("1.0", json.dumps(json_content, indent=4))
                
                self.ativo_var.set(motor_data.get("ativo", True))
                # Novo campo 'padrao'
                self.padrao_var.set(bool(motor_data.get("padrao", False)))
            else:
                self.controller.show_frame("ListarMotoresFrame")

    def salvar_motor(self):
        nome = self.nome_entry.get().strip()
        if not nome:
            messagebox.showwarning("Dados Incompletos", "Por favor, preencha o Nome do Motor.")
            return

        try:
            versao = float(self.versao_entry.get().strip())
        except ValueError:
            messagebox.showerror("Erro de Validação", "O campo 'Versão' deve ser um número.")
            return

        funcao = self.funcao_entry.get().strip()
        metodo = self.metodo_entry.get().strip()
        arquivo_externo = self.arquivo_externo_entry.get().strip()
        json_interno_str = self.json_interno_text.get("1.0", tk.END).strip()
        
        json_interno = None
        if json_interno_str:
            try:
                json_interno = json.loads(json_interno_str)
            except json.JSONDecodeError:
                messagebox.showerror("Erro de Validação", "O conteúdo do JSON Interno é inválido.")
                return

        ativo = self.ativo_var.get()
        padrao = self.padrao_var.get()

        success = salvar_motor_no_banco(
            nome, versao, funcao, metodo, json_interno, arquivo_externo, ativo, padrao, self.motor_id_atual
        )

        if success:
            temporary_message(self.controller, "Cadastro Salvo", f"Motor '{nome}' salvo com sucesso no banco de dados!")
            self.controller.show_frame("ListarMotoresFrame")

    def on_show(self):
        pass
