# -*- coding: utf-8 -*-
"""
Módulo de Widgets (Frontend)

Classes de widgets Tkinter personalizadas e reutilizáveis.
"""
import tkinter as tk

class Tooltip:
    """
    Cria um tooltip (hint) para um widget tkinter.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind("<Enter>", self.mostrar)
        widget.bind("<Leave>", self.esconder)

    def mostrar(self, event=None):
        if self.tooltip_window:
            return
        
        # Tenta obter as coordenadas relativas ao widget
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        except tk.TclError:
            # Widget pode não estar visível ainda
            return

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Arial", 9, "normal"))
        label.pack(ipadx=4, ipady=2)

    def esconder(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None