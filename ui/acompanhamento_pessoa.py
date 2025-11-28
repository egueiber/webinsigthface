# -*- coding: utf-8 -*-
"""
Módulo da Tela de Acompanhamento por Pessoa (Frontend)


"""
import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox
from datetime import date, timedelta
from tkcalendar import DateEntry
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# (NOVO) Imports dos nossos módulos de "Backend"
from services.database_service import get_pessoas_por_periodo_db, get_caminho_pessoa_db
from services.graph_service import criar_figura_grafo
from .video_player import VideoPlayerWindow


class AcompanhamentoPessoaFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.graph_canvas_widget = None
        self.graph_figure = None
        self.tooltip_cursor = None
        self.video_window = None

        # --- Frame de Filtros ---
        filtro_frame = ttk.Frame(self)
        filtro_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(filtro_frame, text="Data Inicial:").pack(side="left", padx=(0, 5))
        self.data_inicio_entry = DateEntry(filtro_frame, width=12, date_pattern='dd/mm/yyyy', takefocus=0)
        self.data_inicio_entry.pack(side="left", padx=5)
        self.data_inicio_entry.set_date(date.today())
        
        ttk.Label(filtro_frame, text="Data Final:").pack(side="left", padx=(15, 5))
        self.data_final_entry = DateEntry(filtro_frame, width=12, date_pattern='dd/mm/yyyy', takefocus=0)
        self.data_final_entry.pack(side="left", padx=5)

        self.somente_com_atraso_var = tk.BooleanVar()
        ttk.Checkbutton(filtro_frame, text="Somente com atraso", variable=self.somente_com_atraso_var).pack(side="left", padx=10)

        self.identificada_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filtro_frame, text="Identificada", variable=self.identificada_var).pack(side="left", padx=10)

        ttk.Button(filtro_frame, text="Buscar Pessoas", style="Accent.TButton",
                  command=self.buscar_pessoas).pack(side="left", padx=10)
        
        # --- Frame de Seleção ---
        selecao_frame = ttk.Frame(self)
        selecao_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(selecao_frame, text="Pessoa:").pack(side="left", padx=(0, 5))
        self.pessoa_combobox = ttk.Combobox(selecao_frame, state="readonly", width=40)
        self.pessoa_combobox.pack(side="left", padx=5)
        
        ttk.Button(selecao_frame, text="Gerar Grafo", 
                  command=self.gerar_grafo).pack(side="left", padx=10)

        # --- Frame de Conteúdo (Grafo e Lista) ---
        content_frame = ttk.Frame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        content_frame.rowconfigure(0, weight=1)
        content_frame.columnconfigure(0, weight=3) # Grafo ocupa mais espaço
        content_frame.columnconfigure(1, weight=2) # Lista ocupa menos espaço

        # --- Frame do Grafo (à esquerda) ---
        self.graph_frame = ttk.Frame(content_frame, relief=tk.SOLID, borderwidth=1)
        self.graph_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # --- Frame da Lista (à direita) ---
        list_frame = ttk.Frame(content_frame, relief=tk.SOLID, borderwidth=1)
        list_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        ttk.Label(list_frame, text="Caminho Percorrido (duplo-clique para ver o vídeo)", 
                  font=("Arial", 10, "bold")).pack(pady=5, padx=5)
        
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        cols = ("local", "horario", "segundo", "video_path", "start_second")
        display_cols = ("local", "horario", "segundo")
        
        self.tree = ttk.Treeview(tree_container, columns=cols, displaycolumns=display_cols, 
                                 show="headings", height=10)
        
        self.tree.column("local", width=150)
        self.tree.column("horario", width=80, anchor="center")
        self.tree.column("segundo", width=100, anchor="e")
        
        self.tree.heading("local", text="Local")
        self.tree.heading("horario", text="Horário")
        self.tree.heading("segundo", text="Tempo no Vídeo")
        
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)


    def on_show(self, *args):
        """
        Limpa a tela e, se dados de uma pessoa forem fornecidos, 
        gera o grafo automaticamente.
        """
        self.limpar_grafo()
        self.pessoa_combobox['values'] = []
        self.pessoa_combobox.set("")

        # Se argumentos foram passados (vindo do dashboard)
        if args and isinstance(args[0], tuple) and len(args[0]) == 4:
            pessoa_id, pessoa_nome, data_inicio, data_fim = args[0]
            
            # Define as datas nos campos de entrada
            self.data_inicio_entry.set_date(data_inicio)
            self.data_final_entry.set_date(data_fim)

            # Adiciona a pessoa ao combobox e a seleciona
            self.pessoa_combobox['values'] = [pessoa_nome]
            self.pessoa_combobox.set(pessoa_nome)
            
            # Gera o grafo
            self.gerar_grafo()
        else:
            # Comportamento padrão: define as datas para o período default
            self.data_inicio_entry.set_date(date.today())
            self.data_final_entry.set_date(date.today())

    def limpar_grafo(self):
        """Remove o widget do grafo anterior e limpa a lista de eventos."""
        if self.graph_canvas_widget:
            self.graph_canvas_widget.destroy()
            self.graph_canvas_widget = None
        if self.graph_figure:
            plt.close(self.graph_figure) # Fecha a figura do matplotlib
            self.graph_figure = None
        self.tooltip_cursor = None # O cursor está ligado à figura
        
        # Limpa a árvore de eventos
        if hasattr(self, 'tree'):
            for i in self.tree.get_children():
                self.tree.delete(i)

    def validar_datas(self):
        """Valida as datas de início e fim. Retorna (data_inicio, data_fim) ou None."""
        data_inicio = self.data_inicio_entry.get_date()
        data_fim = self.data_final_entry.get_date()
        if data_inicio > data_fim:
            messagebox.showwarning("Data Inválida", "A data de início não pode ser posterior à data de fim.")
            return None, None
        return data_inicio, data_fim

    def buscar_pessoas(self):
        """Busca pessoas com registros no período selecionado."""
        self.limpar_grafo()
        self.pessoa_combobox.set("")
        
        data_inicio, data_fim = self.validar_datas()
        if data_inicio is None:
            return

        somente_com_atraso = self.somente_com_atraso_var.get()
        pessoas = get_pessoas_por_periodo_db(data_inicio, data_fim, somente_com_atraso) # (MODIFICADO) Chama o serviço
        if not pessoas:
            messagebox.showinfo("Sem Resultados", "Nenhuma pessoa encontrada com os filtros selecionados.")
            self.pessoa_combobox['values'] = []
        else:
            self.pessoa_combobox['values'] = pessoas
            if pessoas:
                self.pessoa_combobox.current(0)

    def gerar_grafo(self, event=None):
        """Pede ao serviço para criar o grafo e o exibe no canvas."""
        self.limpar_grafo()
        
        nome_pessoa = self.pessoa_combobox.get()
        if not nome_pessoa:
            messagebox.showwarning("Seleção Vazia", "Por favor, busque e selecione uma pessoa primeiro.")
            return
            
        data_inicio, data_fim = self.validar_datas()
        if data_inicio is None:
            return
            
        data_inicio_str = data_inicio.strftime("%d/%m/%Y")
        data_fim_str = data_fim.strftime("%d/%m/%Y")
            
        caminho_data = get_caminho_pessoa_db(nome_pessoa, data_inicio, data_fim, self.identificada_var.get())
        
        if not caminho_data:
            messagebox.showinfo("Sem Dados", f"Nenhum dado de caminhamento encontrado para '{nome_pessoa}' neste período.")
            return

        # Limpa a árvore antes de preencher
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Preenche a árvore com os dados do caminho
        for row in caminho_data:
            # Assumindo que a ordem é: 0:data_hora, 1:nome_camera, ..., 4:video_path, 5:start_second
            data_hora, nome_camera, _, _, video_path, start_second = row[:6]
            horario_str = data_hora.strftime("%H:%M:%S")
            self.tree.insert("", "end", values=(nome_camera, horario_str, start_second, video_path, start_second))
            
        if any(r[2] is None or r[3] is None for r in caminho_data):
            messagebox.showwarning("Dados Incompletos", 
                                   "Alguns registros de câmera não possuem dados de 'Andar' ou 'Sala'.\n"
                                   "O grafo pode ficar incompleto ou posicionado incorretamente.\n"
                                   "Atualize os dados em 'Gerenciar Câmeras'.")
        
        # --- Lógica do Evento de Clique ---
        def on_node_double_click(event):
            # Apenas responde a duplo-cliques do mouse
            if not event.mouseevent.dblclick:
                return

            if self.video_window and self.video_window.winfo_exists():
                self.video_window.focus()
                return

            # Mapeia o índice do artista clicado para o ID do nó
            node_index = event.target.ind[0]
            node_id = node_ids_ordenados[node_index]
            node_data = graph_G.nodes[node_id]

            video_path = node_data.get("video_path")
            start_second = node_data.get("start_second")
            
            try:
                # Garante que start_second é um inteiro
                start_time = int(start_second)
            except (ValueError, TypeError):
                messagebox.showerror("Erro de Dados", f"O tempo de início do vídeo é inválido: {start_second}")
                return

            if not video_path or not os.path.exists(video_path):
                messagebox.showerror("Arquivo não Encontrado", f"O arquivo de vídeo não foi encontrado no caminho:\n{video_path}")
                return
            
            # Abre a janela do player
            self.video_window = VideoPlayerWindow(self, video_path, start_time)
            self.video_window.focus()

        # Chama o serviço para criar a figura, passando o callback
        fig, cursor, graph_G, node_ids_ordenados = criar_figura_grafo(
            caminho_data, 
            nome_pessoa, 
            data_inicio_str, 
            data_fim_str,
            on_node_click_callback=on_node_double_click
        )
        
        if fig is None:
            messagebox.showerror("Erro de Grafo", "Não foi possível gerar a figura do grafo.")
            return

        # Guarda as referências para poder limpá-las depois
        self.graph_figure = fig
        self.tooltip_cursor = cursor
        
        # Embutir o Grafo no Canvas do Tkinter
        canvas = FigureCanvasTkAgg(self.graph_figure, master=self.graph_frame)
        self.graph_canvas_widget = canvas.get_tk_widget()
        self.graph_canvas_widget.pack(fill="both", expand=True)
        canvas.draw()

    def on_tree_double_click(self, event):
        """Abre o player de vídeo para o item selecionado na árvore."""
        if self.video_window and self.video_window.winfo_exists():
            self.video_window.focus()
            return

        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_values = self.tree.item(item_id, "values")
        
        # As colunas são: 0:local, 1:horario, 2:segundo, 3:video_path, 4:start_second
        video_path = item_values[3]
        try:
            start_time = int(item_values[4])
        except (ValueError, TypeError):
            messagebox.showerror("Erro de Dados", "O tempo de início da marcação no vídeo é inválido.")
            return

        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Arquivo não Encontrado", f"O arquivo de vídeo não foi encontrado no caminho:\n{video_path}")
            return
            
        self.video_window = VideoPlayerWindow(self, video_path, start_time)
        self.video_window.focus()