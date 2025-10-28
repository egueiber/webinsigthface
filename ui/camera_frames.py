# -*- coding: utf-8 -*-
"""
Módulo das Telas de Câmera (Frontend)
"""
import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox, filedialog
import os
import shutil 
from PIL import Image, ImageTk

# (NOVO) Imports dos nossos módulos de "Backend"
from services.database_service import (
    listar_cameras_db, 
    get_camera_por_id_db, 
    salvar_camera_no_banco, 
    excluir_camera_db
)

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
        cameras = listar_cameras_db(filtro) # (MODIFICADO) Chama o serviço
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
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir a câmera '{nome}' (ID: {camera_id})?\n\nO MAPA ASSOCIADO SERÁ APAGADO PERMANENTEMENTE."):
            return
        camera_data = get_camera_por_id_db(camera_id) # (MODIFICADO) Chama o serviço
        caminho_mapa = camera_data.get("mapa_path") if camera_data else None
        success = excluir_camera_db(camera_id, caminho_mapa) # (MODIFICADO) Chama o serviço
        if success:
            messagebox.showinfo("Sucesso", f"Câmera '{nome}' foi excluída com sucesso.")
            self.popular_lista() 
        
    def on_show(self):
        self.popular_lista()


# --- Módulo 2B: Cadastro/Edição de Câmera ---
class CadastroCamerasFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.filepath_original_selecionado = None 
        self.camera_id_atual = None
        
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
        self.loc_entry = ttk.Entry(form_frame, width=40)
        self.loc_entry.grid(row=1, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Andar (ex: 0, 1, -1):").grid(row=2, column=0, padx=5, pady=8, sticky='e')
        self.andar_entry = ttk.Entry(form_frame, width=10)
        self.andar_entry.grid(row=2, column=1, padx=5, pady=8, sticky='w')
        
        ttk.Label(form_frame, text="Nº Sala Próxima:").grid(row=3, column=0, padx=5, pady=8, sticky='e')
        self.nrsala_entry = ttk.Entry(form_frame, width=10)
        self.nrsala_entry.grid(row=3, column=1, padx=5, pady=8, sticky='w')

        ttk.Label(form_frame, text="Imagem (Mapa):").grid(row=4, column=0, padx=5, pady=8, sticky='e')
        self.btn_selecionar = ttk.Button(form_frame, text="Selecionar Nova Imagem...", command=self.selecionar_imagem)
        self.btn_selecionar.grid(row=4, column=1, padx=5, pady=8, sticky='w')
        
        self.path_label = ttk.Label(form_frame, text="Nenhum arquivo selecionado.", style="Secondary.TLabel") # (MODIFICADO) Usa Style
        self.path_label.grid(row=5, column=1, padx=5, sticky='w')

        # --- (FIX V7.4) Move o botão para ANTES do mapa ---
        self.btn_salvar = ttk.Button(self, text="Salvar Cadastro", style="Accent.TButton", command=self.salvar_camera)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5) # <-- BOTÃO (AGORA VISÍVEL)

        self.thumbnail_label = ttk.Label(self, relief="solid", style="Card.TLabel", anchor="center")
        self.thumbnail_label.pack(pady=10, ipadx=100, ipady=100) # <-- MAPA
        

    def carregar_dados(self, camera_id):
        self.camera_id_atual = camera_id
        self.filepath_original_selecionado = None 
        self.nome_entry.delete(0, tk.END)
        self.loc_entry.delete(0, tk.END)
        self.andar_entry.delete(0, tk.END)
        self.nrsala_entry.delete(0, tk.END)
        
        self.thumbnail_label.config(image='', text="")
        self.thumbnail_label.image = None
        self.path_label.config(text="Nenhum arquivo selecionado.", style="Secondary.TLabel")
        
        if camera_id is None:
            self.titulo_label.config(text="Nova Câmera")
            self.btn_salvar.config(text="Salvar Nova Câmera")
            self.andar_entry.insert(0, "0")
            self.nrsala_entry.insert(0, "0")
        else:
            self.titulo_label.config(text="Editar Câmera")
            self.btn_salvar.config(text="Salvar Alterações") # <-- O texto do botão muda aqui
            camera_data = get_camera_por_id_db(self.camera_id_atual) # (MODIFICADO) Chama o serviço
            
            if camera_data:
                self.nome_entry.insert(0, camera_data["nome"])
                self.loc_entry.insert(0, camera_data["localizacao"])
                self.andar_entry.insert(0, str(camera_data.get("andar", 0)))
                self.nrsala_entry.insert(0, str(camera_data.get("nrsala", 0)))
                
                mapa_path = camera_data.get("mapa_path")
                if mapa_path: # Mesmo que não exista, guardamos o caminho
                    self.filepath_original_selecionado = mapa_path # Guarda o caminho do DB
                    if os.path.exists(mapa_path):
                        self.exibir_thumbnail(mapa_path)
                        self.path_label.config(text=f"(Atual) {os.path.basename(mapa_path)}", style="TLabel")
                    else:
                        self.path_label.config(text="(Arquivo de mapa não encontrado!)", style="Error.TLabel")
            else:
                self.controller.show_frame("ListarCamerasFrame")


    def selecionar_imagem(self):
        filetypes = (('Imagens', '*.jpg *.jpeg *.png *.bmp'), ('Todos os arquivos', '*.*'))
        filepath = filedialog.askopenfilename(title='Selecione uma imagem de mapa', filetypes=filetypes)
        if filepath:
            self.filepath_original_selecionado = filepath # Sobrepõe o caminho do DB com o novo
            self.path_label.config(text=os.path.basename(filepath), style="TLabel")
            self.exibir_thumbnail(filepath)

    def exibir_thumbnail(self, filepath):
        try:
            img = Image.open(filepath)
            max_size = (300, 300)
            img.thumbnail(max_size)
            imgtk = ImageTk.PhotoImage(image=img)
            self.thumbnail_label.config(image=imgtk, text="") # Remove texto
            self.thumbnail_label.image = imgtk 
        except Exception as e:
            messagebox.showerror("Erro de Imagem", f"Não foi possível carregar a imagem: {e}")
            self.thumbnail_label.config(image='', text="Erro ao carregar imagem")
            self.thumbnail_label.image = None
            self.path_label.config(text="Arquivo inválido.", style="Error.TLabel")
            self.filepath_original_selecionado = None

    def salvar_camera(self):
        nome = self.nome_entry.get().strip()
        localizacao = self.loc_entry.get().strip()
        
        if not nome or not localizacao:
            messagebox.showwarning("Dados Incompletos", "Por favor, preencha Nome e Localização.")
            return
            
        try:
            andar = int(self.andar_entry.get().strip())
            nrsala = int(self.nrsala_entry.get().strip())
        except ValueError:
            messagebox.showerror("Erro de Validação", "Os campos 'Andar' e 'Nº Sala Próxima' devem ser números inteiros.")
            return

        if self.filepath_original_selecionado is None:
             messagebox.showwarning("Dados Incompletos", "Por favor, selecione uma imagem para o mapa.")
             return
             
        base_path_mapas = self.controller.parametros.get("mapas") # Pasta de destino
        
        try:
            os.makedirs(base_path_mapas, exist_ok=True)
        except Exception as e:
             messagebox.showerror("Erro de Parâmetro", f"Não foi possível criar a pasta de destino dos mapas:\n{base_path_mapas}\n\nErro: {e}")
             return
        
        source_path = self.filepath_original_selecionado
        nome_arquivo = os.path.basename(source_path)
        dest_path = os.path.join(base_path_mapas, nome_arquivo) # Caminho de destino final
        
        try:
            base_path_mapas_norm = os.path.normpath(base_path_mapas)
            source_path_norm = os.path.normpath(source_path)

            if not source_path_norm.startswith(base_path_mapas_norm):
                shutil.copy(source_path, dest_path)
                print(f"Arquivo de mapa copiado para: {dest_path}")
            else:
                print("Arquivo já está (ou deveria estar) na pasta de destino. Pulando cópia.")

        except Exception as e:
            messagebox.showerror("Erro de Cópia", f"Não foi possível copiar o NOVO arquivo de mapa:\n{source_path}\n\nErro: {e}")
            return
            
        success = salvar_camera_no_banco(
            nome, localizacao, dest_path, 
            andar, nrsala, self.camera_id_atual
        )
        
        if success:
            messagebox.showinfo("Cadastro Salvo", f"Câmera '{nome}' salva com sucesso no banco de dados!")
            self.controller.show_frame("ListarCamerasFrame")

    def on_show(self):
        """Chamado ao exibir o frame. Não faz nada no cadastro, mas precisa existir."""
        pass