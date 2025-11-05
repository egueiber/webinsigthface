# -*- coding: utf-8 -*-
"""
Módulo das Telas de Pessoa (Frontend)
"""
import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox
from .widgets import temporary_message
import cv2
import face_recognition
import os
import re
import shutil 
from PIL import Image, ImageTk

# (NOVO) Imports dos nossos módulos de "Backend"
from services.database_service import (
    listar_pessoas_db, 
    get_pessoa_por_id_db, 
    salvar_pessoa_no_banco, 
    excluir_pessoa_db,
    get_db_connection
)
from services.facial_service import gerar_aumentos_de_dados, PADDING_PIXELS


# --- Módulo 1A: Lista de Pessoas ---
class ListarPessoasFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(top_frame, text="Gerenciar Pessoas", font=("Arial", 18, "bold")).pack(side="left")
        ttk.Button(top_frame, text="Novo Cadastro +", 
                  command=self.abrir_novo, style="Accent.TButton").pack(side="right") # (MODIFICADO) Usa ttk e Style

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(search_frame, text="Buscar por Nome:").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<Return>", lambda event: self.popular_lista())
        ttk.Button(search_frame, text="Buscar", command=self.popular_lista).pack(side="left", padx=5)
        
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("id", "nome", "documento")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nome", width=300)
        self.tree.column("documento", width=150, anchor="center")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome Completo")
        self.tree.heading("documento", text="Documento")
        
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
        ttk.Button(action_frame, text="Eventos", 
                  command=self.abrir_eventos).pack(side="left", padx=5)

    def popular_lista(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        filtro = self.search_entry.get()
        pessoas = listar_pessoas_db(filtro) # (MODIFICADO) Chama o serviço
        for pessoa in pessoas:
            self.tree.insert("", "end", values=pessoa)

    def abrir_novo(self):
        self.controller.abrir_edicao_pessoa(None) 

    def abrir_edicao(self):
        selecionado = self.tree.focus() 
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma pessoa na lista para editar.")
            return
        dados_pessoa = self.tree.item(selecionado)
        pessoa_id = dados_pessoa["values"][0] 
        self.controller.abrir_edicao_pessoa(pessoa_id)

    def abrir_eventos(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma pessoa na lista para ver os eventos.")
            return
        dados_pessoa = self.tree.item(selecionado)
        pessoa_id = dados_pessoa["values"][0]
        self.controller.abrir_eventos_pessoa(pessoa_id)
        
    def excluir(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma pessoa na lista para excluir.")
            return
        dados_pessoa = self.tree.item(selecionado)
        pessoa_id = dados_pessoa["values"][0]
        nome = dados_pessoa["values"][1]
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{nome}' (ID: {pessoa_id})?\n\nTODOS OS DADOS E FOTOS SERÃO APAGADOS PERMANENTEMENTE."):
            return
        
        nome_pasta_fotos = None
        conn = get_db_connection() # (MODIFICADO) Chama o serviço
        if conn is None: return
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT "fotosPessoa" FROM sch_supervisorio.tb_pessoa WHERE "idPessoa" = %s', (pessoa_id,))
                result = cur.fetchone()
                if result:
                    nome_pasta_fotos = result[0]
        finally:
            conn.close()
        
        caminho_completo_para_excluir = None
        if nome_pasta_fotos:
            base_path_fotos = self.controller.parametros.get("fotos")
            if base_path_fotos:
                 caminho_completo_para_excluir = os.path.join(base_path_fotos, nome_pasta_fotos)
            
        success = excluir_pessoa_db(pessoa_id, caminho_completo_para_excluir) # (MODIFICADO) Chama o serviço
        
        if success:
            temporary_message(self.controller, "Sucesso", f"'{nome}' foi excluído com sucesso.")
            self.popular_lista() 
        
    def on_show(self):
        self.popular_lista()


# --- Módulo 1B: Cadastro/Edição de Pessoa ---
class CadastroFacialFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        
        self.poses = ["Frente", "Direita", "Esquerda", "Sorrindo", "Cima", "Baixo"]
        self.current_pose_index = 0
        self.capturando = False
        self.video_capture = None
        self.pessoa_id_atual = None 

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.titulo_label = ttk.Label(top_frame, text="Nova Pessoa", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")

        # Indicador visual do estado da câmera (ON/OFF)
        self.camera_status_label = ttk.Label(top_frame, text="Câmera: OFF", foreground="red")
        self.camera_status_label.pack(side="right", padx=5)

        tk.Button(top_frame, text="< Voltar para Lista", 
          command=lambda: controller.show_frame("ListarPessoasFrame")).pack(side="right")

        self.video_label = ttk.Label(self)
        self.video_label.pack(pady=10)
        
        self.instrucao_label = ttk.Label(self, text="Preencha os dados e inicie o cadastro.")
        self.instrucao_label.pack(pady=10)
        
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=5)

        ttk.Label(form_frame, text="Nome Completo:").grid(row=0, column=0, padx=5, sticky='w')
        self.nome_entry = ttk.Entry(form_frame, width=30)
        self.nome_entry.grid(row=0, column=1, padx=5)

        ttk.Label(form_frame, text="Nº da Carteira de ID:").grid(row=1, column=0, padx=5, sticky='w')
        self.id_entry = ttk.Entry(form_frame, width=30)
        self.id_entry.grid(row=1, column=1, padx=5)

        self.btn_acao = ttk.Button(self, text="Iniciar Cadastro", style="Accent.TButton", command=self.iniciar_cadastro)
        self.btn_acao.pack(pady=15, ipadx=10, ipady=5)
        
        # --- (FIX V7.1) ---
        # Removido 'width' e 'height' que não são suportados pelo ttk.Label
        # Adicionado 'anchor' e 'justify' para centralizar o texto
        self.camera_off_label = ttk.Label(self, text="Câmera desligada.\nO cadastro facial ativará a câmera.", 
                                         font=("Arial", 14), 
                                         relief="solid", style="Card.TLabel", 
                                         anchor="center", justify="center")

    def carregar_dados(self, pessoa_id):
        self.pessoa_id_atual = pessoa_id
        self.nome_entry.config(state=tk.NORMAL)
        self.id_entry.config(state=tk.NORMAL)
        self.nome_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)
        if pessoa_id is None:
            self.titulo_label.config(text="Nova Pessoa")
            self.instrucao_label.config(text="Preencha os dados e inicie o cadastro.")
            self.btn_acao.config(text="Iniciar Cadastro", command=self.iniciar_cadastro, style="Accent.TButton")
            self.capturando = False
        else:
            self.titulo_label.config(text="Editar Pessoa")
            pessoa_data = get_pessoa_por_id_db(pessoa_id) # (MODIFICADO) Chama o serviço
            if pessoa_data:
                self.nome_entry.insert(0, pessoa_data["nome"])
                self.id_entry.insert(0, pessoa_data["documento"])
            self.instrucao_label.config(text="Para RE-CAPTURAR fotos, clique em 'Iniciar Captura'.\nPara salvar apenas os dados (Nome/ID), clique em 'Salvar Dados'.")
            self.btn_acao.config(text="Iniciar RE-Captura", command=self.iniciar_cadastro, style="TButton")

    def iniciar_camera(self):
        if self.video_capture is None:
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened():
                messagebox.showerror("Erro de Câmera", "Não foi possível acessar a câmera.")
                self.video_capture = None
                # Atualiza indicador
                try:
                    self.camera_status_label.config(text="Câmera: OFF", foreground="red")
                except Exception:
                    pass
                self.camera_off_label.pack(pady=5, fill="both", expand=True) 
                return
        # Indicador e início do fluxo de vídeo
        try:
            self.camera_status_label.config(text="Câmera: ON", foreground="green")
        except Exception:
            pass
        self.camera_off_label.pack_forget()
        self.video_label.pack(pady=5)
        self.update_frame()

    def release_camera(self):
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
            self.video_label.config(image='')
            self.video_label.imgtk = None
            self.video_label.pack_forget()
            # Atualiza indicador
            try:
                self.camera_status_label.config(text="Câmera: OFF", foreground="red")
            except Exception:
                pass
            self.camera_off_label.pack(pady=5, fill="both", expand=True)

    def update_frame(self):
        if self.video_capture is None or not self.video_capture.isOpened():
            self.release_camera() 
            return
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.flip(frame, 1)
            face_locations = face_recognition.face_locations(frame, model='hog')
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        self.after(15, self.update_frame)

    def sanitizar_nome(self, nome):
        return re.sub(r'[^a-zA-Z0-9_]', '', nome.replace(" ", "_"))

    def iniciar_cadastro(self):
        nome = self.nome_entry.get().strip()
        id_carteira = self.id_entry.get().strip()
        if not nome or not id_carteira:
            messagebox.showwarning("Dados Incompletos", "Por favor, preencha o Nome e o Número da Carteira.")
            return
        base_path_fotos = self.controller.parametros.get("fotos")
        if not base_path_fotos or not os.path.isdir(base_path_fotos):
             messagebox.showerror("Erro de Parâmetro", f"O caminho de fotos não está configurado ou é inválido:\n{base_path_fotos}\n\nVá ao menu 'Parâmetros' para corrigir.")
             return
        nome_sanitizado = self.sanitizar_nome(nome)
        id_sanitizado = self.sanitizar_nome(id_carteira)
        self.nome_pasta = f"{nome_sanitizado}_{id_sanitizado}"
        self.caminho_pasta = os.path.join(base_path_fotos, self.nome_pasta)
        if os.path.exists(self.caminho_pasta):
            if not messagebox.askyesno("Pasta Existente", f"A pasta de fotos '{self.nome_pasta}' já existe.\nDeseja sobrescrever as fotos existentes?"):
                return
        else:
            os.makedirs(self.caminho_pasta)
        self.capturando = True
        self.current_pose_index = 0
        self.nome_entry.config(state=tk.DISABLED)
        self.id_entry.config(state=tk.DISABLED)
        self.atualizar_passo_gui()
        self.btn_acao.config(command=self.processar_passo, text="Capturar e Prosseguir", style="TButton")

        # Inicia a câmera quando o usuário clica em Iniciar Cadastro / RE-Captura
        self.iniciar_camera()

    def processar_passo(self):
        if not self.capturando or self.video_capture is None:
            return
        ret, frame = self.video_capture.read()
        if not ret:
            messagebox.showerror("Erro de Câmera", "Não foi possível ler a imagem da câmera.")
            return
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model='hog')
        if len(face_locations) != 1:
            messagebox.showwarning("Aviso de Captura", "Não foi possível detectar um único rosto.")
            return
        top, right, bottom, left = face_locations[0]
        h, w, _ = frame.shape
        top_padded = max(0, top - PADDING_PIXELS)
        left_padded = max(0, left - PADDING_PIXELS)
        bottom_padded = min(h, bottom + PADDING_PIXELS)
        right_padded = min(w, right + PADDING_PIXELS)
        rosto_recortado = frame[top_padded:bottom_padded, left_padded:right_padded]
        pose_atual = self.poses[self.current_pose_index]
        nome_arquivo = f"{pose_atual}.jpg"
        caminho_arquivo = os.path.join(self.caminho_pasta, nome_arquivo)
        cv2.imwrite(caminho_arquivo, rosto_recortado)
        print(f"[TEMP] Rosto recortado e salvo em: {caminho_arquivo}")
        self.current_pose_index += 1
        if self.current_pose_index < len(self.poses):
            self.atualizar_passo_gui()
        else:
            self.finalizar_cadastro()

    def atualizar_passo_gui(self):
        pose_instrucao = self.poses[self.current_pose_index]
        self.instrucao_label.config(text=f"Passo {self.current_pose_index + 1}/{len(self.poses)}: Peça para a pessoa estar na pose '{pose_instrucao.upper()}'")

    def finalizar_cadastro(self):
        gerar_aumentos_de_dados(self.caminho_pasta) # (MODIFICADO) Chama o serviço
        nome_final = self.nome_entry.get().strip()
        id_final = self.id_entry.get().strip()
        
        success = salvar_pessoa_no_banco(nome_final, id_final, self.nome_pasta, self.pessoa_id_atual) # (MODIFICADO) Chama o serviço
        
        if success:
            temporary_message(self.controller, "Cadastro Concluído", f"Cadastro de '{nome_final}' salvo com sucesso!\n\nDados salvos no banco e fotos salvas em:\n{self.caminho_pasta}")
            self.controller.show_frame("ListarPessoasFrame")
        self.capturando = False
        self.nome_entry.config(state=tk.NORMAL)
        self.id_entry.config(state=tk.NORMAL)
        self.carregar_dados(self.pessoa_id_atual)

    def on_show(self):
        """Chamado ao exibir o frame. Não faz nada no cadastro, mas precisa existir."""
        pass