# -*- coding: utf-8 -*-
"""
Módulo da Tela Home (Frontend)
"""
import tkinter as tk
from tkinter import ttk

class HomeFrame(ttk.Frame): # (MODIFICADO) Usa ttk.Frame para o tema
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        label = ttk.Label(self, text="Health Track Unimed - UEPG", font=("Arial", 24, "bold"))
        label.pack(pady=100)
        label2 = ttk.Label(self, text="Selecione um módulo no menu lateral para começar.", font=("Arial", 16))
        label2.pack(pady=10)