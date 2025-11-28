# -*- coding: utf-8 -*-
"""
Módulo da Janela do Player de Vídeo
"""
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk

class VideoPlayerWindow(tk.Toplevel):
    def __init__(self, parent, video_path, start_time_seconds):
        super().__init__(parent)
        self.title("Player de Vídeo da Marcação")
        self.geometry("800x650")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.video_path = video_path
        self.start_time_ms = start_time_seconds * 1000
        self.cap = None
        self.photo = None
        
        # --- Layout ---
        self.canvas = tk.Canvas(self)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ttk.Button(controls_frame, text="Fechar", command=self.on_close).pack(side="right", padx=5)
        ttk.Button(controls_frame, text="Próximo Quadro >", command=self.next_frame).pack(side="right", padx=5)
        ttk.Button(controls_frame, text="< Quadro Anterior", command=self.previous_frame).pack(side="right", padx=5)
        
        self.after(100, self.load_and_display_initial_frame)

    def load_and_display_initial_frame(self):
        """Abre o vídeo, busca o frame inicial e o exibe."""
        try:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                self.show_error("Não foi possível abrir o arquivo de vídeo.")
                return

            # Posiciona o vídeo no tempo correto
            self.cap.set(cv2.CAP_PROP_POS_MSEC, self.start_time_ms)
            
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
            else:
                self.show_error("Não foi possível ler o frame no tempo especificado.")

        except Exception as e:
            self.show_error(f"Erro ao iniciar o vídeo: {e}")

    def display_frame(self, frame):
        """Redimensiona e exibe um único frame no canvas."""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
             # Se o canvas ainda não tiver sido renderizado, tenta novamente em 50ms
            self.after(50, lambda: self.display_frame(frame))
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        
        img_ratio = img.width / img.height
        canvas_ratio = canvas_width / canvas_height

        if img_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(new_width / img_ratio)
        else:
            new_height = canvas_height
            new_width = int(new_height * img_ratio)
        
        if new_width > 0 and new_height > 0:
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        self.photo = ImageTk.PhotoImage(image=img)
        
        self.canvas.delete("all")
        x_pos = (canvas_width - new_width) / 2
        y_pos = (canvas_height - new_height) / 2
        self.canvas.create_image(x_pos, y_pos, image=self.photo, anchor='nw')

    def next_frame(self):
        """Avança e exibe o próximo frame."""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)

    def previous_frame(self):
        """Retrocede e exibe o frame anterior."""
        if self.cap and self.cap.isOpened():
            # Pega o número do frame atual
            current_frame_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            
            # Retrocede 2 frames (1 para o frame atual, 1 para o anterior)
            previous_frame_pos = max(0, current_frame_pos - 2)
            
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, previous_frame_pos)
            
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)

    def show_error(self, message):
        """Exibe uma mensagem de erro no canvas."""
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() / 2, 
            self.canvas.winfo_height() / 2, 
            text=message, 
            fill="red", 
            font=("Arial", 12)
        )

    def on_close(self):
        """Libera os recursos e fecha a janela."""
        if self.cap:
            self.cap.release()
        self.destroy()
