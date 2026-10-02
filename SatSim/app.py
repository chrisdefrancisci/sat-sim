import tkinter as tk
import ttkbootstrap as ttk

from SatSim.view import view_3d
from SatSim.model.simulate import Simulate
from SatSim.controller.sim_controller import SimController


class App(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.pack(fill=tk.BOTH, expand=True)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        self.view_3d = view_3d.View3D(self)
        self.view_3d.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.sim = Simulate()

        self.controller = SimController(self, self.sim, self.view_3d)
        self.controller.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
