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

def temporary_message(parent, title, message, duration=2000):
    """
    Displays a temporary message box that disappears after a specified duration.
    """
    window = tk.Toplevel(parent)
    window.wm_overrideredirect(True)
    window.wm_title(title)

    # Calculate position to center on parent
    parent.update_idletasks()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()

    label = tk.Label(window, text=message, justify='left',
                     background="#dcedc8", relief='solid', borderwidth=1,
                     font=("Arial", 10, "bold"), wraplength=300, fg="#1b5e20")
    label.pack(ipadx=20, ipady=10)
    
    window.update_idletasks()
    win_width = window.winfo_width()
    win_height = window.winfo_height()

    x = parent_x + (parent_width // 2) - (win_width // 2)
    y = parent_y + (parent_height // 2) - (win_height // 2)

    window.wm_geometry(f"+{x}+{y}")

    window.after(duration, window.destroy)
