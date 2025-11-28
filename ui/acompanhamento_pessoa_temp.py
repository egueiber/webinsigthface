# -*- coding: utf-8 -*-
"""
Módulo da Tela de Acompanhamento por Pessoa (Frontend)


"""
import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox
from datetime import datetime 
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# (NOVO) Imports dos nossos módulos de "Backend"
from services.database_service import get_pessoas_por_periodo_db, get_caminho_pessoa_db
from services.graph_service import criar_figura_grafo

class AcompanhamentoPessoaFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.graph_canvas_widget = None
        self.graph_figure = None
        self.tooltip_cursor = None

        # --- Frame de Filtros ---
        filtro_frame = ttk.Frame(self)
        filtro_frame.pack(fill="x", padx=10, pady=10)
        
        
        ttk.Label(filtro_frame, text="Data Inicial:").pack(side="left", padx=(0, 5))
        self.data_inicio_entry = ttk.Entry(filtro_frame, width=12)
        self.data_inicio_entry.pack(side="left", padx=5)
        self.data_inicio_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(filtro_frame, text="Data Final:").pack(side="left", padx=(15, 5))
        self.data_final_entry = ttk.Entry(filtro_frame, width=12)
        self.data_final_entry.pack(side="left", padx=5)
        self.data_final_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

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

        # --- Frame do Grafo ---
        self.graph_frame = ttk.Frame(self, relief=tk.SOLID, borderwidth=1)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

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
            
            # Formata as datas para string (o Entry espera string)
            data_inicio_str = data_inicio.strftime("%Y-%m-%d")
            data_fim_str = data_fim.strftime("%Y-%m-%d")

            # Define as datas nos campos de entrada
            self.data_inicio_entry.delete(0, tk.END)
            self.data_inicio_entry.insert(0, data_inicio_str)
            self.data_final_entry.delete(0, tk.END)
            self.data_final_entry.insert(0, data_fim_str)

            # Adiciona a pessoa ao combobox e a seleciona
            self.pessoa_combobox['values'] = [pessoa_nome]
            self.pessoa_combobox.set(pessoa_nome)
            
            # Gera o grafo
            self.gerar_grafo()
        else:
            # Comportamento padrão: define as datas para o período default
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.data_inicio_entry.delete(0, tk.END)
            self.data_inicio_entry.insert(0, today_str)
            self.data_final_entry.delete(0, tk.END)
            self.data_final_entry.insert(0, today_str)

    def limpar_grafo(self):
        """Remove o widget do grafo anterior."""
        if self.graph_canvas_widget:
            self.graph_canvas_widget.destroy()
            self.graph_canvas_widget = None
        if self.graph_figure:
            plt.close(self.graph_figure) # Fecha a figura do matplotlib
            self.graph_figure = None
        self.tooltip_cursor = None # O cursor está ligado à figura

    def validar_datas(self):
        """Valida as datas de início e fim. Retorna (data_inicio, data_fim) ou None."""
        data_inicio_str = self.data_inicio_entry.get()
        data_fim_str = self.data_final_entry.get()
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
            return data_inicio, data_fim
        except ValueError:
            messagebox.showwarning("Data Inválida", "Por favor, insira as datas no formato AAAA-MM-DD.")
            return None, None

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
            
        data_inicio_str = self.data_inicio_entry.get()
        data_fim_str = self.data_final_entry.get()
            
        caminho_data = get_caminho_pessoa_db(nome_pessoa, data_inicio, data_fim, self.identificada_var.get()) # (MODIFICADO) Chama o serviço
        
        if not caminho_data:
            messagebox.showinfo("Sem Dados", f"Nenhum dado de caminhamento encontrado para '{nome_pessoa}' neste período.")
            return
            
        if any(r[2] is None or r[3] is None for r in caminho_data):
            messagebox.showwarning("Dados Incompletos", 
                                   "Alguns registros de câmera não possuem dados de 'Andar' ou 'Sala'.\n"
                                   "O grafo pode ficar incompleto ou posicionado incorretamente.\n"
                                   "Atualize os dados em 'Gerenciar Câmeras'.")
            
        # (MODIFICADO) Lógica do grafo movida para o 'graph_service'
        # A tela só recebe a figura pronta e o cursor
        fig, cursor, graph_G, node_ids_ordenados = criar_figura_grafo(
            caminho_data, nome_pessoa, data_inicio_str, data_fim_str
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