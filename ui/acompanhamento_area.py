# -*- coding: utf-8 -*-
"""
Módulo da Tela de Acompanhamento por Área (Frontend)
"""
import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox
import os
from PIL import Image, ImageTk
from datetime import datetime 

# (NOVO) Imports dos nossos módulos de "Backend"
from services.database_service import get_localizacoes_db, get_dados_acompanhamento_db
from .widgets import Tooltip

class AcompanhamentoAreaFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.map_image_tk = None 
        self.localizacoes_mapas = {} 
        self.icones_canvas = [] 
        self.tooltip_window_mapa = None 
        
        self.cores_icones = [
            "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
            "#FF4500", "#ADFF2F", "#DA70D6", "#B0C4DE"
        ]

        # --- Layout Principal ---
        filtro_frame = ttk.Frame(self)
        filtro_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(filtro_frame, text="Localização:").pack(side="left", padx=(0, 5))
        self.loc_combobox = ttk.Combobox(filtro_frame, state="readonly", width=30)
        self.loc_combobox.pack(side="left", padx=5)

        ttk.Label(filtro_frame, text="Data (AAAA-MM-DD):").pack(side="left", padx=(15, 5))
        self.data_entry = ttk.Entry(filtro_frame, width=12)
        self.data_entry.pack(side="left", padx=5)
        self.data_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Button(filtro_frame, text="Buscar", style="Accent.TButton",
                  command=self.buscar_dados).pack(side="left", padx=10)

        content_frame = ttk.Frame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        map_frame = ttk.Frame(content_frame, relief=tk.SOLID, borderwidth=1)
        map_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Canvas não é temático, então continua tk.Canvas
        self.map_canvas = tk.Canvas(map_frame, relief=tk.SUNKEN, borderwidth=1)
        self.map_canvas.pack(fill="both", expand=True)

        list_frame = ttk.Frame(content_frame, width=400, relief=tk.SOLID, borderwidth=1)
        list_frame.pack(side="right", fill="y", expand=False, padx=(5, 0))
        list_frame.pack_propagate(False) 

        ttk.Label(list_frame, text="Pessoas Identificadas", font=("Arial", 12, "bold")).pack(pady=5)
        
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        cols = ("nome", "horario", "segundo", "notacomparacao")
        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", height=10)
        self.tree.column("nome", width=100)
        self.tree.column("horario", width=80, anchor="center")
        self.tree.column("segundo", width=70, anchor="e")
        self.tree.column("notacomparacao", width=60, anchor="center")
        
        self.tree.heading("nome", text="Nome")
        self.tree.heading("horario", text="Horário")
        self.tree.heading("segundo", text="Tempo")
        self.tree.heading("notacomparacao", text="Nota")
        
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

    def on_show(self):
        """Chamado ao exibir o frame. Carrega as localizações."""
        self.carregar_localizacoes()
        self.limpar_tela()

    def carregar_localizacoes(self):
        """Busca localizações do DB e preenche o combobox."""
        self.localizacoes_mapas = get_localizacoes_db() # (MODIFICADO) Chama o serviço
        loc_nomes = list(self.localizacoes_mapas.keys())
        self.loc_combobox['values'] = loc_nomes
        if loc_nomes:
            self.loc_combobox.current(0)

    def limpar_tela(self):
        """Limpa o mapa e a lista."""
        self.map_canvas.delete("all")
        self.map_image_tk = None
        self.icones_canvas = []
        for i in self.tree.get_children():
            self.tree.delete(i)
        if self.tooltip_window_mapa:
            self.tooltip_window_mapa.destroy()
            self.tooltip_window_mapa = None

    def buscar_dados(self):
        """Função principal que busca dados e atualiza a tela."""
        self.limpar_tela()
        
        localizacao = self.loc_combobox.get()
        data_str = self.data_entry.get()

        if not localizacao:
            messagebox.showwarning("Filtro Incompleto", "Por favor, selecione uma localização.")
            return
        
        try:
            datetime.strptime(data_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Data Inválida", "Por favor, insira a data no formato AAAA-MM-DD.")
            return

        # 1. Carregar o Mapa no Canvas
        mapa_path = self.localizacoes_mapas.get(localizacao)
        
        map_x_pos, map_y_pos = 0, 0
        map_width, map_height = 100, 100
        
        if mapa_path and os.path.exists(mapa_path):
            try:
                self.map_canvas.update_idletasks()
                canvas_width = self.map_canvas.winfo_width()
                canvas_height = self.map_canvas.winfo_height()
                if canvas_width <= 1: canvas_width = 500
                if canvas_height <= 1: canvas_height = 500

                img = Image.open(mapa_path)
                img_ratio = img.width / img.height
                canvas_ratio = canvas_width / canvas_height

                if img_ratio > canvas_ratio: 
                    new_width = canvas_width
                    new_height = int(new_width / img_ratio)
                else: 
                    new_height = canvas_height
                    new_width = int(new_height * img_ratio)

                if new_width <= 0: new_width = 500
                if new_height <= 0: new_height = 500
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                self.map_image_tk = ImageTk.PhotoImage(img)
                
                x_pos = (canvas_width - new_width) / 2
                y_pos = (canvas_height - new_height) / 2
                self.map_canvas.create_image(x_pos, y_pos, anchor='nw', image=self.map_image_tk)
                
                map_x_pos, map_y_pos = x_pos, y_pos
                map_width, map_height = new_width, new_height

            except Exception as e:
                print(f"Erro ao carregar imagem: {e}")
                self.map_canvas.create_text(10, 10, anchor='nw', text=f"Erro ao carregar mapa:\n{e}", fill="red")
        else:
            self.map_canvas.create_text(10, 10, anchor='nw', text=f"Mapa não encontrado para '{localizacao}'\nCaminho: {mapa_path}", fill="red")

        # 2. Buscar Dados de Acompanhamento
        dados = get_dados_acompanhamento_db(localizacao, data_str) # (MODIFICADO) Chama o serviço
        if not dados:
            if mapa_path and os.path.exists(mapa_path): 
                messagebox.showinfo("Sem Resultados", f"Nenhum registro encontrado para '{localizacao}' na data '{data_str}'.")
            return

        # 3. Preencher a Lista (Treeview) e agrupar dados por pessoa
        pessoas_unicas = {}
        for nome_pessoa, data_hora, segundo, notacomparacao, notaparaignorar, notaidentificacao in dados:
            if nome_pessoa not in pessoas_unicas:
                pessoas_unicas[nome_pessoa] = {
                    "horarios": [],
                    "max_notacomparacao": 0,
                    "notaparaignorar": notaparaignorar,
                    "notaidentificacao": notaidentificacao
                }
            
            pessoas_unicas[nome_pessoa]["horarios"].append(data_hora)
            if notacomparacao > pessoas_unicas[nome_pessoa]["max_notacomparacao"]:
                pessoas_unicas[nome_pessoa]["max_notacomparacao"] = notacomparacao

            horario_str = data_hora.strftime("%H:%M:%S")
            self.tree.insert("", "end", values=(nome_pessoa, horario_str, segundo, notacomparacao))

        # 4. Desenhar os ícones no mapa
        centro_x = map_x_pos + (map_width / 2)
        centro_y = map_y_pos + (map_height / 2)
        
        offsets = [
            (0, 0), (-40, -40), (40, 40), (0, -60), (0, 60), (-70, 0),
            (70, 0), (-50, 50), (50, -50), (80, -20), (-80, 20)
        ]
        
        raio = 8 
        
        for i, (nome_pessoa, dados_pessoa) in enumerate(pessoas_unicas.items()):
            # Definir a cor do ícone com base na nota de comparação
            notacomparacao = dados_pessoa["max_notacomparacao"]
            notaparaignorar = dados_pessoa["notaparaignorar"]
            notaidentificacao = dados_pessoa["notaidentificacao"]

            cor_icone = "yellow" # Cor padrão (intermediária)
            if notacomparacao <= notaparaignorar:
                cor_icone = "red"
            elif notacomparacao >= notaidentificacao:
                cor_icone = "green"

            offset_x, offset_y = offsets[i % len(offsets)]
            x = centro_x + offset_x
            y = centro_y + offset_y
            
            x = max(map_x_pos + raio, min(map_x_pos + map_width - raio, x))
            y = max(map_y_pos + raio, min(map_y_pos + map_height - raio, y))
            
            icone = self.map_canvas.create_oval(x-raio, y-raio, x+raio, y+raio, 
                                                fill=cor_icone, outline="black", width=1,
                                                tags=(f"icone_{i}")) 
            self.icones_canvas.append(icone) 

            primeira_vez = min(dados_pessoa["horarios"]).strftime("%H:%M:%S")
            ultima_vez = max(dados_pessoa["horarios"]).strftime("%H:%M:%S")
            contagem = len(dados_pessoa["horarios"])
            
            tooltip_text = f"Pessoa: {nome_pessoa}\n" \
                           f"Detecções: {contagem}\n" \
                           f"Primeira vez: {primeira_vez}\n" \
                           f"Última vez: {ultima_vez}"
                           
            self.map_canvas.tag_bind(f"icone_{i}", "<Enter>", lambda e, txt=tooltip_text: self.mostrar_tooltip_icone(e, txt))
            self.map_canvas.tag_bind(f"icone_{i}", "<Leave>", lambda e: self.esconder_tooltip_icone())

    def mostrar_tooltip_icone(self, event, texto):
        if self.tooltip_window_mapa:
            self.tooltip_window_mapa.destroy()
        x = event.x_root + 15
        y = event.y_root + 10
        self.tooltip_window_mapa = tk.Toplevel(self.map_canvas)
        self.tooltip_window_mapa.wm_overrideredirect(True)
        self.tooltip_window_mapa.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window_mapa, text=texto, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Arial", 9, "normal"))
        label.pack(ipadx=4, ipady=2)

    def esconder_tooltip_icone(self, event=None): 
        if self.tooltip_window_mapa:
            self.tooltip_window_mapa.destroy()
        self.tooltip_window_mapa = None