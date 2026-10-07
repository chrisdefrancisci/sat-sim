import tkinter as tk
import ttkbootstrap as ttk

from SatSim.controller.settings import SettingsDialog
from SatSim.model.settings_model import SettingsModel


class Toolbar(ttk.Frame):
    def __init__(self, parent, settings_model:SettingsModel, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.settings_model = settings_model

        self.pack(fill=tk.BOTH, expand=True)

        self.settings = ttk.Button(self, icon="gear-fill", icon_only=True, bootstyle="primary",
                                   command=self.open_settings)
        ttk.ToolTip(self.settings, text="Settings", bootstyle="info")
        self.settings.pack(side="left", padx=(5, 0))
        self.open = ttk.Button(self, icon="folder", icon_only=True, bootstyle="secondary")
        self.open.pack(side="left", padx=(5, 0))
        ttk.ToolTip(self.open, text="Open Config", bootstyle="info")
        self.save = ttk.Button(self, icon="floppy-fill", icon_only=True, bootstyle="secondary")
        self.save.pack(side="left", padx=(5, 0))
        ttk.ToolTip(self.save, text="Save Config", bootstyle="info")

    def open_settings(self):
        dialog = SettingsDialog(self, self.settings_model)
        self.wait_window(dialog)  # pause here until the popup closes
