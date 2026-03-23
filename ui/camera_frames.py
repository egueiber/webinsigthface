# -*- coding: utf-8 -*-
"""
Módulo das Telas de Câmera (Frontend)
"""
import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox, filedialog
from .widgets import temporary_message
import os
import shutil 
from PIL import Image, ImageTk

# (NOVO) Imports dos nossos módulos de "Backend"
from backend.services.database_service import (
    list_cameras, 
    get_camera_by_id, 
    save_camera, 
    delete_camera
)
from backend.services.location_service import list_locations


# --- Módulo 2A: Lista de Câmeras ---
class ListarCamerasFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(top_frame, text="Gerenciar Câmeras", font=("Arial", 18, "bold")).pack(side="left")
        ttk.Button(top_frame, text="Nova Câmera +", 
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
        
        cols = ("id", "nome", "localizacao")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nome", width=250)
        self.tree.column("localizacao", width=300)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome Câmera")
        self.tree.heading("localizacao", text="Localização") 
        
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
        cameras = list_cameras(filtro) # (MODIFICADO) Chama o serviço
        for camera in cameras:
            self.tree.insert("", "end", values=camera)

    def abrir_novo(self):
        self.controller.abrir_edicao_camera(None) 

    def abrir_edicao(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma câmera na lista para editar.")
            return
        dados_camera = self.tree.item(selecionado)
        camera_id = dados_camera["values"][0] 
        self.controller.abrir_edicao_camera(camera_id)
        
    def excluir(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma câmera na lista para excluir.")
            return
        dados_camera = self.tree.item(selecionado)
        camera_id = dados_camera["values"][0]
        nome = dados_camera["values"][1]
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir a câmera '{nome}' (ID: {camera_id})?"):
            return
        
        success = delete_camera(camera_id) # (MODIFICADO) Chama o serviço
        if success:
            temporary_message(self.controller, "Sucesso", f"Câmera '{nome}' foi excluída com sucesso.")
            self.popular_lista() 
        
    def on_show(self):
        self.popular_lista()


# --- Módulo 2B: Cadastro/Edição de Câmera ---
class CadastroCamerasFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.camera_id_atual = None
        self.localizacoes = {}  # Dicionário para mapear nome da localização para ID
        
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        self.titulo_label = ttk.Label(top_frame, text="Nova Câmera", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")
        ttk.Button(top_frame, text="< Voltar para Lista", 
                  command=lambda: controller.show_frame("ListarCamerasFrame")).pack(side="right")

        
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10, padx=20)

        ttk.Label(form_frame, text="Nome da Câmera:").grid(row=0, column=0, padx=5, pady=8, sticky='e')
        self.nome_entry = ttk.Entry(form_frame, width=40)
        self.nome_entry.grid(row=0, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Localização:").grid(row=1, column=0, padx=5, pady=8, sticky='e')
        self.loc_combobox = ttk.Combobox(form_frame, width=38, state="readonly")
        self.loc_combobox.grid(row=1, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Andar (ex: 0, 1, -1):").grid(row=2, column=0, padx=5, pady=8, sticky='e')
        self.andar_entry = ttk.Entry(form_frame, width=10)
        self.andar_entry.grid(row=2, column=1, padx=5, pady=8, sticky='w')
        
        ttk.Label(form_frame, text="Nº Sala Próxima:").grid(row=3, column=0, padx=5, pady=8, sticky='e')
        self.nrsala_entry = ttk.Entry(form_frame, width=10)
        self.nrsala_entry.grid(row=3, column=1, padx=5, pady=8, sticky='w')

        ttk.Label(form_frame, text="Nota para Ignorar (0.0 a 1.0):").grid(row=4, column=0, padx=5, pady=8, sticky='e')
        self.notaignorar_entry = ttk.Entry(form_frame, width=10)
        self.notaignorar_entry.grid(row=4, column=1, padx=5, pady=8, sticky='w')

        ttk.Label(form_frame, text="Nota de Identificação (0.0 a 1.0):").grid(row=5, column=0, padx=5, pady=8, sticky='e')
        self.notaidentificacao_entry = ttk.Entry(form_frame, width=10)
        self.notaidentificacao_entry.grid(row=5, column=1, padx=5, pady=8, sticky='w')

        self.btn_salvar = ttk.Button(self, text="Salvar Cadastro", style="Accent.TButton", command=self.salvar_camera)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)

    def carregar_dados(self, camera_id):
        self.camera_id_atual = camera_id
        
        # Limpa campos
        self.nome_entry.delete(0, tk.END)
        self.loc_combobox.set('')
        self.andar_entry.delete(0, tk.END)
        self.nrsala_entry.delete(0, tk.END)
        self.notaignorar_entry.delete(0, tk.END)
        self.notaidentificacao_entry.delete(0, tk.END)
        
        # Carrega e popula as localizações
        try:
            loc_data = list_locations()
            self.localizacoes = {loc[1]: loc[0] for loc in loc_data} # Nome -> ID
            self.loc_combobox['values'] = list(self.localizacoes.keys())
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar as localizações: {e}")
            self.loc_combobox['values'] = []

        if camera_id is None:
            self.titulo_label.config(text="Nova Câmera")
            self.btn_salvar.config(text="Salvar Nova Câmera")
            self.andar_entry.insert(0, "0")
            self.nrsala_entry.insert(0, "0")
            self.notaignorar_entry.insert(0, "0.7")
            self.notaidentificacao_entry.insert(0, "0.7")
        else:
            self.titulo_label.config(text="Editar Câmera")
            self.btn_salvar.config(text="Salvar Alterações")
            camera_data = get_camera_by_id(self.camera_id_atual)
            
            if camera_data:
                self.nome_entry.insert(0, camera_data["nome"])
                
                # Encontra o nome da localização pelo ID
                idlocalizacao = camera_data.get("idlocalizacao")
                nome_localizacao = ""
                for nome, id_loc in self.localizacoes.items():
                    if id_loc == idlocalizacao:
                        nome_localizacao = nome
                        break
                self.loc_combobox.set(nome_localizacao)

                self.andar_entry.insert(0, str(camera_data.get("andar", 0)))
                self.nrsala_entry.insert(0, str(camera_data.get("nrsala", 0)))
                self.notaignorar_entry.insert(0, str(camera_data.get("notaparaignorar", 0.7)))
                self.notaidentificacao_entry.insert(0, str(camera_data.get("notaidentificacao", 0.7)))
            else:
                self.controller.show_frame("ListarCamerasFrame")

    def salvar_camera(self):
        nome = self.nome_entry.get().strip()
        nome_localizacao = self.loc_combobox.get()
        
        if not nome or not nome_localizacao:
            messagebox.showwarning("Dados Incompletos", "Por favor, preencha Nome e selecione uma Localização.")
            return
            
        idlocalizacao = self.localizacoes.get(nome_localizacao)
        if idlocalizacao is None:
            messagebox.showerror("Erro de Validação", "Localização selecionada é inválida.")
            return

        try:
            andar = int(self.andar_entry.get().strip())
            nrsala = int(self.nrsala_entry.get().strip())
            notaparaignorar = float(self.notaignorar_entry.get().strip())
            notaidentificacao = float(self.notaidentificacao_entry.get().strip())
            if not ((0.0 <= notaparaignorar <= 10 and 0.0 <= notaidentificacao <= 10) and (notaparaignorar < notaidentificacao)):
                raise ValueError("Notas devem estar entre 0.0 e 10.0 e a nota para ignorar deve ser menor a de identificação.")
        except ValueError as e:
            messagebox.showerror("Erro de Validação", f"Os campos de nota devem ser números entre 0.0 e 1.0. Os campos 'Andar' e 'Nº Sala Próxima' devem ser números inteiros.\n\nDetalhe: {e}")
            return
            
        success = save_camera(
            nome, idlocalizacao, 
            andar, nrsala, notaparaignorar, notaidentificacao, self.camera_id_atual
        )
        
        if success:
            temporary_message(self.controller, "Cadastro Salvo", f"Câmera '{nome}' salva com sucesso no banco de dados!")
            self.controller.show_frame("ListarCamerasFrame")

    def on_show(self):
        """Chamado ao exibir o frame. Não faz nada no cadastro, mas precisa existir."""
        pass