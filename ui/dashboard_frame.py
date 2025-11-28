# -*- coding: utf-8 -*-
"""
DashboardFrame

Este módulo define o frame principal do dashboard, 
exibindo indicadores e listas relevantes.
"""
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import date, timedelta

# Importa os serviços do backend
from services import dashboard_service

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.localizacoes = [] # Para guardar a lista de (id, nome)
        self.selected_person = None # Para guardar (id, nome) da pessoa selecionada

        # --- Layout Principal ---
        self.grid_rowconfigure(2, weight=1) # A linha da lista (2) deve expandir
        self.grid_columnconfigure(0, weight=1)

        # --- Frame de Filtros ---
        filtros_frame = ttk.LabelFrame(self, text="Filtros", padding=(10, 5))
        filtros_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        filtros_frame.grid_columnconfigure(4, weight=1) # Coluna do combobox de localização

        # Data Início
        ttk.Label(filtros_frame, text="Data Início:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.data_inicio_entry = DateEntry(filtros_frame, width=12, date_pattern='dd/mm/yyyy', takefocus=0)
        self.data_inicio_entry.grid(row=0, column=1, padx=(0, 10), pady=5)
        self.data_inicio_entry.set_date(date.today() - timedelta(days=1))

        # Data Fim
        ttk.Label(filtros_frame, text="Data Fim:").grid(row=0, column=2, padx=(0, 5), pady=5, sticky="w")
        self.data_fim_entry = DateEntry(filtros_frame, width=12, date_pattern='dd/mm/yyyy', takefocus=0)
        self.data_fim_entry.grid(row=0, column=3, padx=(0, 10), pady=5)

        # Localização
        ttk.Label(filtros_frame, text="Localização:").grid(row=0, column=4, padx=(0, 5), pady=5, sticky="w")
        self.localizacao_combo = ttk.Combobox(filtros_frame, state="readonly")
        self.localizacao_combo.grid(row=0, column=5, padx=(0, 10), pady=5, sticky="ew")
        
        # Botão de Filtrar
        self.filtrar_btn = ttk.Button(filtros_frame, text="Atualizar", command=self.atualizar_dashboard, style="Accent.TButton")
        self.filtrar_btn.grid(row=0, column=6, padx=5, pady=5, sticky="e")

        # --- Frame de Indicadores ---
        indicadores_frame = ttk.LabelFrame(self, text="Indicadores do Período", padding=(10, 5))
        indicadores_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        indicadores_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Indicador 1: Pessoas Atendidas
        self.total_atendidos_var = tk.StringVar(value="...")
        ttk.Label(indicadores_frame, text="Pessoas Atendidas", font=("", 11, "bold")).grid(row=0, column=0, pady=(5,0))
        ttk.Label(indicadores_frame, textvariable=self.total_atendidos_var, font=("", 18, "bold")).grid(row=1, column=0, pady=(0,10))

        # Indicador 2: Tempo Médio de Atendimento
        self.tempo_medio_var = tk.StringVar(value="...")
        ttk.Label(indicadores_frame, text="Tempo Médio Atendimento", font=("", 11, "bold")).grid(row=0, column=1, pady=(5,0))
        ttk.Label(indicadores_frame, textvariable=self.tempo_medio_var, font=("", 18, "bold")).grid(row=1, column=1, pady=(0,10))

        # Indicador 3: Pessoas Presentes
        self.total_presentes_var = tk.StringVar(value="...")
        ttk.Label(indicadores_frame, text="Pessoas Presentes", font=("", 11, "bold")).grid(row=0, column=2, pady=(5,0))
        ttk.Label(indicadores_frame, textvariable=self.total_presentes_var, font=("", 18, "bold")).grid(row=1, column=2, pady=(0,10))

        # --- Frame da Lista de Pessoas com Atraso ---
        lista_frame = ttk.LabelFrame(self, text="Pessoas com Atraso no Atendimento", padding=(10, 5))
        lista_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        lista_frame.grid_rowconfigure(0, weight=1)
        lista_frame.grid_columnconfigure(0, weight=1)

        # Colunas
        self.tree_pessoas_atraso = ttk.Treeview(lista_frame, columns=("id", "nome", "tempo_atraso", "localizacao"), show="headings")
        self.tree_pessoas_atraso.heading("nome", text="Nome")
        self.tree_pessoas_atraso.heading("tempo_atraso", text="Tempo de Atraso")
        self.tree_pessoas_atraso.heading("localizacao", text="Última Localização")
        
        # Oculta a coluna 'id'
        self.tree_pessoas_atraso.column("id", width=0, stretch=tk.NO)
        self.tree_pessoas_atraso.heading("id", text="ID")

        self.tree_pessoas_atraso.column("nome", width=250)
        self.tree_pessoas_atraso.column("tempo_atraso", width=100, anchor="center")
        self.tree_pessoas_atraso.column("localizacao", width=150, anchor="center")
        
        self.tree_pessoas_atraso.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree_pessoas_atraso.yview)
        self.tree_pessoas_atraso.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.tree_pessoas_atraso.bind("<<TreeviewSelect>>", self.ao_selecionar_pessoa)

        # Botão para abrir o grafo
        self.ver_grafo_btn = ttk.Button(lista_frame, text="Acompanhar Pessoa Selecionada", 
                                        command=self.abrir_grafo_para_selecionado, state="disabled")
        self.ver_grafo_btn.grid(row=1, column=0, columnspan=2, pady=(5,0), sticky="e")

    def _format_timedelta(self, td):
        """Formata um objeto timedelta para HH:MM:SS."""
        # if not isinstance(td, timedelta):
        #     return "00:00:00"
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def atualizar_dashboard(self):
        """Busca os dados do backend e atualiza os componentes da UI."""
        data_inicio = self.data_inicio_entry.get_date()
        data_fim = self.data_fim_entry.get_date()
        
        # Pega o ID do cenário selecionado
        cenario_selecionado = self.localizacao_combo.get()
        cenario_id = None
        if cenario_selecionado != "Todas":
            for loc_id, loc_nome in self.localizacoes:
                if loc_nome == cenario_selecionado:
                    cenario_id = loc_id
                    break
        
        # --- Atualiza Indicadores ---
        indicadores = dashboard_service.get_indicadores(data_inicio, data_fim, cenario_id)
        self.total_atendidos_var.set(str(indicadores.get('total_atendidos', 0)))
        self.tempo_medio_var.set(self._format_timedelta(indicadores.get('tempo_medio')))
        self.total_presentes_var.set(str(indicadores.get('total_presentes', 0)))

        # --- Atualiza Lista de Atrasos ---
        # Limpa a seleção e desabilita o botão
        self.selected_person = None
        self.ver_grafo_btn.config(state="disabled")
        # Limpa a lista antiga
        for item in self.tree_pessoas_atraso.get_children():
            self.tree_pessoas_atraso.delete(item)
            
        pessoas_atraso = dashboard_service.get_pessoas_com_atraso(data_inicio, data_fim, cenario_id)
        for id_pessoa, nome, atraso, local in pessoas_atraso:
            #self.tree_pessoas_atraso.insert("", "end", values=(id_pessoa, nome, self._format_timedelta(atraso), local))
            self.tree_pessoas_atraso.insert("", "end", values=(id_pessoa, nome, atraso, local))

    def ao_selecionar_pessoa(self, event):
        """Chamado quando uma pessoa é selecionada na lista de atrasos."""
        selected_item = self.tree_pessoas_atraso.focus()
        if selected_item:
            item_details = self.tree_pessoas_atraso.item(selected_item)
            # Recupera o ID e o nome da pessoa
            pessoa_id = item_details['values'][0]
            pessoa_nome = item_details['values'][1]
            self.selected_person = (pessoa_id, pessoa_nome)
            self.ver_grafo_btn.config(state="normal")
        else:
            self.selected_person = None
            self.ver_grafo_btn.config(state="disabled")

    def abrir_grafo_para_selecionado(self):
        """Abre o grafo para a pessoa atualmente selecionada na lista."""
        if self.selected_person:
            data_inicio = self.data_inicio_entry.get_date()
            data_fim = self.data_fim_entry.get_date()
            person_id, person_name = self.selected_person
            self.controller.abrir_grafo_pessoa((person_id, person_name, data_inicio, data_fim))

    def on_show(self, *args):
        """Chamado quando o frame é exibido."""
        self.carregar_localizacoes()
        self.atualizar_dashboard()
        
    def carregar_localizacoes(self):
        """Busca as localizações (cenários) do banco e atualiza o combobox."""
        self.localizacoes = dashboard_service.get_localizacoes_para_filtro()
        nomes_localizacoes = ["Todas"] + [loc[1] for loc in self.localizacoes]
        self.localizacao_combo['values'] = nomes_localizacoes
        self.localizacao_combo.set("Todas")