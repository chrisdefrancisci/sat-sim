import tkinter as tk
import ttkbootstrap as ttk

from SatSim.view import view_3d
from SatSim.model.simulate import Simulate
from SatSim.controller.sim_controller import SimController
from SatSim.controller.toolbar import Toolbar
from SatSim.controller.settings import SettingsDialog


class App(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.pack(fill=tk.BOTH, expand=True)

        self.view_3d = view_3d.View3D(self)

        self.sim = Simulate()

        self.toolbar = Toolbar(self, self.sim.get_settings, self.sim.load_settings)
        self.controller = SimController(self, self.sim, self.view_3d)

        self.toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.view_3d.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.controller.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
