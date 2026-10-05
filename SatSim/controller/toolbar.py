import tkinter as tk
import ttkbootstrap as ttk

from SatSim.controller.settings import SettingsDialog


class Toolbar(ttk.Frame):
    def __init__(self, parent, get_settings, load_settings, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.get_settings = get_settings
        self.load_settings = load_settings

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
        dialog = SettingsDialog(self, self.get_settings(), on_save=self.load_settings)
        self.wait_window(dialog)  # pause here until the popup closes
