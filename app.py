import tkinter as tk
from tkinter import ttk

from view import view_3d

class App(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.pack(fill=tk.BOTH, expand=True)

        self.view_3d = view_3d.View3D(self)
        self.view_3d.pack(fill=tk.BOTH, expand=True)

