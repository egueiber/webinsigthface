# -*- coding: utf-8 -*-
"""
Módulo das Telas de Eventos da Pessoa (Frontend)
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, timedelta
from .widgets import temporary_message

# Imports dos nossos módulos de "Backend"
from services.database_service import (
    listar_eventos_por_pessoa_db,
    get_pessoa_evento_por_id_db,
    salvar_pessoa_evento_no_banco,
    excluir_pessoa_evento_db,
    listar_eventos_db, # para o combobox
    get_pessoa_por_id_db # para exibir o nome da pessoa
)
from services.evento_service import get_evento_por_id_db


# --- Módulo: Lista de Eventos da Pessoa ---
class ListarPessoaEventosFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.pessoa_id = None

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.label_titulo = ttk.Label(top_frame, text="Eventos da Pessoa", font=("Arial", 18, "bold"))
        self.label_titulo.pack(side="left")

        ttk.Button(top_frame, text="< Voltar para Pessoas",
                  command=lambda: controller.show_frame("ListarPessoasFrame")).pack(side="right")

        ttk.Button(top_frame, text="Novo Evento +",
                  command=self.abrir_novo, style="Accent.TButton").pack(side="right", padx=10)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("id", "evento", "entrada", "saida_prevista", "saida_efetiva", "cancelado")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("evento", width=200)
        self.tree.column("entrada", width=150, anchor="center")
        self.tree.column("saida_prevista", width=150, anchor="center")
        self.tree.column("saida_efetiva", width=150, anchor="center")
        self.tree.column("cancelado", width=80, anchor="center")

        self.tree.heading("id", text="ID")
        self.tree.heading("evento", text="Evento")
        self.tree.heading("entrada", text="Entrada")
        self.tree.heading("saida_prevista", text="Saída Prevista")
        self.tree.heading("saida_efetiva", text="Saída Efetiva")
        self.tree.heading("cancelado", text="Cancelado")

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
        if self.pessoa_id:
            eventos = listar_eventos_por_pessoa_db(self.pessoa_id)
            for evento in eventos:
                # evento is a tuple: (id, evento, entrada, saida_prevista, saida_efetiva, cancelado)
                formatted_evento = list(evento)
                # Format dates before inserting
                for i in range(2, 5): # indices for date fields
                    if formatted_evento[i] and isinstance(formatted_evento[i], datetime):
                        formatted_evento[i] = formatted_evento[i].strftime('%d/%m/%Y %H:%M:%S')
                self.tree.insert("", "end", values=formatted_evento)

    def abrir_novo(self):
        self.controller.abrir_edicao_pessoa_evento(self.pessoa_id, None)

    def abrir_edicao(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione um evento na lista para editar.")
            return
        dados_evento = self.tree.item(selecionado)
        pessoa_evento_id = dados_evento["values"][0]
        self.controller.abrir_edicao_pessoa_evento(self.pessoa_id, pessoa_evento_id)

    def excluir(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione um evento na lista para excluir.")
            return
        dados_evento = self.tree.item(selecionado)
        pessoa_evento_id = dados_evento["values"][0]
        nome_evento = dados_evento["values"][1]
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o evento '{nome_evento}' desta pessoa?"):
            return

        success = excluir_pessoa_evento_db(pessoa_evento_id)

        if success:
            temporary_message(self.controller, "Sucesso", f"Evento '{nome_evento}' foi removido com sucesso.")
            self.popular_lista()

    def on_show(self, pessoa_id):
        self.pessoa_id = pessoa_id
        pessoa = get_pessoa_por_id_db(self.pessoa_id)
        if pessoa:
            self.label_titulo.config(text=f"Eventos de: {pessoa['nome']}")
        else:
            self.label_titulo.config(text="Eventos da Pessoa")
        self.popular_lista()


# --- Módulo: Cadastro/Edição de Evento da Pessoa ---
class CadastroPessoaEventoFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.pessoa_id = None
        self.pessoa_evento_id_atual = None

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.titulo_label = ttk.Label(top_frame, text="Adicionar Evento para Pessoa", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")
        ttk.Button(top_frame, text="< Voltar para Lista",
                  command=lambda: controller.show_frame("ListarPessoaEventosFrame", self.pessoa_id)).pack(side="right")

        form_frame = ttk.Frame(self)
        form_frame.pack(pady=20)

        ttk.Label(form_frame, text="Evento:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.evento_combo = ttk.Combobox(form_frame, width=38)
        self.evento_combo.grid(row=0, column=1, padx=5, pady=5)
        self.evento_combo.bind("<<ComboboxSelected>>", self._calcular_saida_prevista)

        ttk.Label(form_frame, text="Entrada (DD/MM/AAAA HH:MM:SS):").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.entrada_entry = ttk.Entry(form_frame, width=30)
        self.entrada_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.entrada_entry.bind("<FocusOut>", self._calcular_saida_prevista)

        ttk.Label(form_frame, text="Saída Prev. (DD/MM/AAAA HH:MM:SS):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.saida_prev_entry = ttk.Entry(form_frame, width=30)
        self.saida_prev_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(form_frame, text="Saída Efet. (DD/MM/AAAA HH:MM:SS):").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.saida_efet_entry = ttk.Entry(form_frame, width=30)
        self.saida_efet_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')

        self.cancelado_var = tk.BooleanVar()
        ttk.Checkbutton(form_frame, text="Evento Cancelado", variable=self.cancelado_var).grid(row=4, column=1, padx=5, pady=5, sticky='w')

        self.btn_salvar = ttk.Button(self, text="Salvar", style="Accent.TButton", command=self.salvar)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)

    def _calcular_saida_prevista(self, event=None):
        try:
            entrada_str = self.entrada_entry.get().strip()
            if not entrada_str:
                return
            entrada_dt = datetime.strptime(entrada_str, '%d/%m/%Y %H:%M:%S')
            
            nome_evento = self.evento_combo.get()
            if not nome_evento:
                return
            idevento = self.eventos_map[nome_evento]
            
            evento_data = get_evento_por_id_db(idevento)
            
            if evento_data and evento_data.get("duracao") is not None and evento_data["duracao"] > 0:
                duracao_minutos = evento_data["duracao"]
                saida_prev_dt = entrada_dt + timedelta(minutes=duracao_minutos)
                self.saida_prev_entry.delete(0, tk.END)
                self.saida_prev_entry.insert(0, saida_prev_dt.strftime('%d/%m/%Y %H:%M:%S'))
            else:
                self.saida_prev_entry.delete(0, tk.END)

        except (ValueError, KeyError):
            self.saida_prev_entry.delete(0, tk.END)
            pass

    def _str_to_datetime(self, dt_str):
        """Tenta converter uma string para datetime."""
        print(f"[DEBUG] Recebido para conversão de data: {dt_str} (tipo: {type(dt_str)})") # DEBUG
        if not dt_str or isinstance(dt_str, datetime):
            return dt_str
        try:
            return datetime.strptime(str(dt_str), '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            try:
                return datetime.strptime(str(dt_str), '%d/%m/%Y %H:%M:%S')
            except (ValueError, TypeError):
                return None

    def carregar_dados(self, pessoa_id, pessoa_evento_id):
        self.pessoa_id = pessoa_id
        self.pessoa_evento_id_atual = pessoa_evento_id

        pessoa = get_pessoa_por_id_db(self.pessoa_id)
        pessoa_nome = pessoa['nome'] if pessoa else ""

        # Carregar eventos no combobox
        eventos = listar_eventos_db()
        self.eventos_map = {evento[1]: evento[0] for evento in eventos}
        self.evento_combo['values'] = list(self.eventos_map.keys())

        self.entrada_entry.delete(0, tk.END)
        self.saida_prev_entry.delete(0, tk.END)
        self.saida_efet_entry.delete(0, tk.END)
        self.cancelado_var.set(False)
        self.evento_combo.set('')

        if pessoa_evento_id is None:
            self.titulo_label.config(text=f"Adicionar Evento para: {pessoa_nome}")
            now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            self.entrada_entry.insert(0, now)
        else:
            self.titulo_label.config(text=f"Editar Evento de: {pessoa_nome}")
            pessoa_evento_data = get_pessoa_evento_por_id_db(pessoa_evento_id)
            if pessoa_evento_data:
                idevento = pessoa_evento_data["idevento"]
                for nome, id_ in self.eventos_map.items():
                    if id_ == idevento:
                        self.evento_combo.set(nome)
                        break
                
                entrada_dt = self._str_to_datetime(pessoa_evento_data.get("datahoraentrada"))
                saida_prev_dt = self._str_to_datetime(pessoa_evento_data.get("datahoraprevistasaida"))
                saida_efet_dt = self._str_to_datetime(pessoa_evento_data.get("datahoraefetivasaida"))

                if entrada_dt:
                    self.entrada_entry.insert(0, entrada_dt.strftime('%d/%m/%Y %H:%M:%S'))
                
                if saida_prev_dt:
                    self.saida_prev_entry.insert(0, saida_prev_dt.strftime('%d/%m/%Y %H:%M:%S'))

                if saida_efet_dt:
                    self.saida_efet_entry.insert(0, saida_efet_dt.strftime('%d/%m/%Y %H:%M:%S'))

                cancelado = pessoa_evento_data.get("eventocancelado")
                self.cancelado_var.set(bool(cancelado))
        
        if not self.saida_prev_entry.get().strip():
            self._calcular_saida_prevista()

    def salvar(self):
        nome_evento = self.evento_combo.get()
        if not nome_evento:
            messagebox.showwarning("Dados Incompletos", "Por favor, selecione um evento.")
            return
        idevento = self.eventos_map[nome_evento]

        entrada_str = self.entrada_entry.get().strip()
        saida_prev_str = self.saida_prev_entry.get().strip()
        saida_efet_str = self.saida_efet_entry.get().strip()

        try:
            entrada = datetime.strptime(entrada_str, '%d/%m/%Y %H:%M:%S') if entrada_str else None
            saida_prev = datetime.strptime(saida_prev_str, '%d/%m/%Y %H:%M:%S') if saida_prev_str else None
            saida_efet = datetime.strptime(saida_efet_str, '%d/%m/%Y %H:%M:%S') if saida_efet_str else None
        except ValueError:
            messagebox.showwarning("Formato Inválido", "Por favor, use o formato DD/MM/AAAA HH:MM:SS para as datas.")
            return

        cancelado = self.cancelado_var.get()

        success = salvar_pessoa_evento_no_banco(
            self.pessoa_id, idevento, entrada, saida_prev, saida_efet, cancelado, self.pessoa_evento_id_atual
        )

        if success:
            temporary_message(self.controller, "Sucesso", f"Evento '{nome_evento}' salvo para a pessoa.")
            self.controller.show_frame("ListarPessoaEventosFrame", self.pessoa_id)

    def on_show(self, pessoa_id, pessoa_evento_id):
        self.carregar_dados(pessoa_id, pessoa_evento_id)
