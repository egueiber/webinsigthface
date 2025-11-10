# -*- coding: utf-8 -*-
"""
Módulo Principal da UI (Frontend)

Define a classe AppPrincipal que gerencia a janela, o menu
e a navegação entre os diferentes frames (telas).
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import matplotlib.pyplot as plt

# (NOVO) Importa o tema moderno
try:
    import sv_ttk
    TEMA_CARREGADO = True
except ImportError:
    TEMA_CARREGADO = False
    print("Execute 'pip install sv-ttk' para um visual moderno.")

# (NOVO) Importa os serviços de backend
from services.config_service import carregar_parametros_db

# (NOVO) Importa os frames (telas)
from .home_frame import HomeFrame
from .pessoa_frames import ListarPessoasFrame, CadastroFacialFrame
from .camera_frames import ListarCamerasFrame, CadastroCamerasFrame
from .motor_frames import ListarMotoresFrame, CadastroMotorFrame
from .parametros_frame import ListarParametrosFrame, CadastroParametroFrame
from .acompanhamento_area import AcompanhamentoAreaFrame
from .acompanhamento_pessoa import AcompanhamentoPessoaFrame
from .evento_frames import ListarEventosFrame, CadastroEventoFrame
from .pessoa_evento_frames import ListarPessoaEventosFrame, CadastroPessoaEventoFrame
from .cenario_frames import ListarCenariosFrame, CadastroCenarioFrame

# (NOVO) Importa o widget de Tooltip
from .widgets import Tooltip

class AppPrincipal(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        
        # --- (NOVO) Aplica o Tema ---
        if TEMA_CARREGADO:
            sv_ttk.set_theme("light") # Ou "dark"
            # Define estilos para botões coloridos
            style = ttk.Style()
            style.configure("Accent.TButton", font=("Arial", 12, "bold"))
            style.configure("Error.TLabel", foreground="red")
            style.configure("Secondary.TLabel", foreground="gray")
            style.configure("Card.TLabel", relief="solid", borderwidth=1)
        
        self.parametros = carregar_parametros_db()
        if self.parametros is None:
            messagebox.showerror("Erro Fatal", "Aplicação não pode iniciar sem parâmetros válidos.")
            self.destroy()
            return

        self.title(f"Health Track Unimed - UEPG")
        self.geometry("950x700")
        
        # --- (NOVO) Carregando Ícones ---
        self.icones = {}
        icon_size = (20, 20)
        icon_path = "assets"
        try:
            # Garante que o caminho seja relativo ao script (útil se main.py estiver em outro lugar)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            assets_dir = os.path.join(base_dir, '..', icon_path) # Sobe um nível (de 'ui' para 'Supervisorio_Refatorado') e entra em 'assets'

            self.icones["pessoa"] = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, "pessoa.png")).resize(icon_size))
            self.icones["camera"] = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, "camera.png")).resize(icon_size))
            self.icones["area"] = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, "area.png")).resize(icon_size))
            self.icones["grafo"] = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, "grafo.png")).resize(icon_size))
            self.icones["config"] = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, "config.png")).resize(icon_size))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar os ícones da pasta '{icon_path}': {e}")
            self.icones = {}

        # --- Menu Lateral ---
        # (MODIFICADO) Usa ttk.Frame, mas mantém a cor clara para contraste
        menu_frame = tk.Frame(self, bg="#f0f0f0" if not TEMA_CARREGADO else "#2a2a2a", width=200, relief=tk.RAISED, borderwidth=1)
        menu_frame.pack(side="left", fill="y", padx=(5,0), pady=5)
        menu_frame.pack_propagate(False) 

        label_style = {"bg": "#f0f0f0" if not TEMA_CARREGADO else "#2a2a2a"}
        if TEMA_CARREGADO:
            label_style["foreground"] = "white"

        tk.Label(menu_frame, text="MENU", font=("Arial", 16, "bold"), **label_style).pack(pady=15)
        
        # --- Conteúdo Principal ---
        content_frame = ttk.Frame(self)
        content_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # (MODIFICADO) Botões do Menu com Ícones e Tooltips
        botoes_menu = [
            ("Pessoas", "ListarPessoasFrame", "pessoa", "Gerenciar cadastro de pessoas"),  
            ("Câmeras", "ListarCamerasFrame", "camera", "Gerenciar cadastro de câmeras"), 
            ("Motores", "ListarMotoresFrame", "config", "Gerenciar motores de processamento"),
            ("Eventos", "ListarEventosFrame", "config", "Gerenciar cadastro de eventos"),
            ("Cenários", "ListarCenariosFrame", "config", "Gerenciar cadastro de cenários"),
            ("Acompanhar Área", "AcompanhamentoAreaFrame", "area", "Ver mapa de acompanhamento por área"),
            ("Acompanhar Pessoa", "AcompanhamentoPessoaFrame", "grafo", "Ver grafo de caminhamento por pessoa"),
            ("Parâmetros", "ListarParametrosFrame", "config", "Configurar parâmetros do sistema")          
        ]
        
        for texto, frame_nome, icone_key, tooltip_text in botoes_menu:
            icone_img = self.icones.get(icone_key) 
            
            # --- (FIX) O 'anchor="w"' foi removido daqui ---
            btn = ttk.Button(menu_frame, 
                            text=f" {texto}",
                            image=icone_img,
                            compound="left", # Coloca o ícone à esquerda
                            command=lambda nome=frame_nome: self.show_frame(nome))
            
            btn.pack(fill="x", pady=5, padx=10)
            Tooltip(btn, tooltip_text) # (NOVO) Adiciona o "hint"

        # --- Frames (Telas) ---
        self.frames = {}
        # (MODIFICADO) Carrega os frames dos módulos importados
        for F in (HomeFrame, 
                  ListarPessoasFrame, CadastroFacialFrame, 
                  ListarCamerasFrame, CadastroCamerasFrame, 
                  ListarMotoresFrame, CadastroMotorFrame,
                  ListarEventosFrame, CadastroEventoFrame,
                  ListarPessoaEventosFrame, CadastroPessoaEventoFrame,
                  AcompanhamentoAreaFrame, AcompanhamentoPessoaFrame,
                  ListarParametrosFrame, CadastroParametroFrame, 
                  ListarCenariosFrame, CadastroCenarioFrame):
            page_name = F.__name__
            frame = F(parent=content_frame, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.current_frame_name = None
        self.show_frame("HomeFrame")

    def recarregar_parametros(self):
        """Recarrega os parâmetros do DB e atualiza o estado global."""
        self.parametros = carregar_parametros_db()
        self.title(f"Health Track Unimed - UEPG: {self.parametros.get('fotos')})")
        print("[TEMP] Parâmetros globais recarregados.")
        
    def show_frame(self, page_name, *args):
        if self.current_frame_name == page_name and not args:
            return
            
        # Limpa recursos das telas anteriores
        if self.current_frame_name == "AcompanhamentoPessoaFrame":
            self.frames["AcompanhamentoPessoaFrame"].limpar_grafo()
        if self.current_frame_name == "CadastroFacialFrame":
            self.frames["CadastroFacialFrame"].release_camera()
        
        # Inicializa recursos da nova tela
        # Observação: a câmera NÃO é mais iniciada automaticamente ao navegar para o
        # frame de cadastro facial. A inicialização agora ocorre somente quando o
        # usuário clicar nos botões de 'Iniciar Cadastro' / 'Iniciar RE-Captura'.
            
        frame = self.frames[page_name]
        
        if hasattr(frame, "on_show"):
            frame.on_show(*args)
            
        frame.tkraise()
        self.current_frame_name = page_name

    def abrir_edicao_pessoa(self, pessoa_id):
        frame = self.frames["CadastroFacialFrame"]
        frame.carregar_dados(pessoa_id)
        self.show_frame("CadastroFacialFrame")

    def abrir_edicao_camera(self, camera_id):
        frame = self.frames["CadastroCamerasFrame"]
        frame.carregar_dados(camera_id)
        self.show_frame("CadastroCamerasFrame")

    def abrir_edicao_motor(self, motor_id):
        frame = self.frames["CadastroMotorFrame"]
        frame.carregar_dados(motor_id)
        self.show_frame("CadastroMotorFrame")

    def abrir_edicao_evento(self, evento_id):
        frame = self.frames["CadastroEventoFrame"]
        frame.carregar_dados(evento_id)
        self.show_frame("CadastroEventoFrame")

    def abrir_edicao_parametro(self, parametro_id):
        self.show_frame("CadastroParametroFrame", parametro_id)

    def abrir_edicao_cenario(self, cenario_id):
        self.show_frame("CadastroCenarioFrame", cenario_id)

    def abrir_eventos_pessoa(self, pessoa_id):
        self.show_frame("ListarPessoaEventosFrame", pessoa_id)

    def abrir_edicao_pessoa_evento(self, pessoa_id, pessoa_evento_id):
        self.show_frame("CadastroPessoaEventoFrame", pessoa_id, pessoa_evento_id)

    def on_closing(self):
        print("Fechando aplicação...")
        if "CadastroFacialFrame" in self.frames:
            try:
                self.frames["CadastroFacialFrame"].release_camera()
            except Exception as e:
                print(f"Erro ao liberar câmera: {e}")
        if "AcompanhamentoPessoaFrame" in self.frames:
            try:
                self.frames["AcompanhamentoPessoaFrame"].limpar_grafo()
            except Exception as e:
                print(f"Erro ao limpar grafo: {e}")
        plt.close('all')
        self.destroy()