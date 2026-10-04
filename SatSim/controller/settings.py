from typing import Any

import ttkbootstrap as ttk

from SatSim.controller.orbit_entry import OrbitEntry


class SatelliteSettings(ttk.Frame):
    def __init__(self, parent, settings=None):
        super().__init__(parent)
        chaser_frame = ttk.LabelFrame(self, text="Chaser")
        chaser_frame.pack(side="top", fill="both", expand=True)
        self.chaser_entry = OrbitEntry(chaser_frame)
        self.chaser_entry.pack(side="top", fill="both", expand=True)
        target_frame = ttk.LabelFrame(self, text="Target")
        target_frame.pack(side="top", fill="both", expand=True)
        self.target_entry = OrbitEntry(target_frame)
        self.target_entry.pack(side="top", fill="both", expand=True)
        self.set_values(settings)

    def set_values(self, settings: dict[str, Any]):
        target_settings = settings.get("target", {})
        chaser_settings = settings.get("chaser", {})
        self.target_entry.set_values(target_settings)
        self.chaser_entry.set_values(chaser_settings)

    def get_values(self) -> dict:
        settings = {"target": self.target_entry.get_values(), "chaser": self.chaser_entry.get_values()}
        return settings


class HohmannSettings(ttk.Frame):
    def __init__(self, parent, on_save, settings=None):
        super().__init__(parent)
        ttk.Label(self, text="Hohmann Settings").pack(fill="both", expand=True)


class BiellipticSettings(ttk.Frame):
    def __init__(self, parent, on_save, settings=None):
        super().__init__(parent)
        ttk.Label(self, text="Bi-Elliptic Settings").pack(fill="both", expand=True)


class ManeuverSettings(ttk.Frame):
    def __init__(self, parent, on_save, settings=None):
        super().__init__(parent)
        ttk.Label(self, text="Maneuver Settings").pack(fill="both", expand=True)


class SettingsDialog(ttk.Toplevel):
    """
    Modal window for displaying and editing settings.
    """

    def __init__(self, parent, settings: dict, on_save):
        super().__init__(
            master=parent,
            title="Settings",
            transient=parent,  # stays on top of the parent
            resizable=(False, False),
        )
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)
        self.body.rowconfigure(0, weight=1)
        self.body.columnconfigure(0, weight=1)
        self.notebook = ttk.Notebook(self.body)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        buttons = ttk.Frame(self.body)
        buttons.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(buttons, icon="plus-circle", text="Add Maneuver", bootstyle="info",
                   command=self._add_maneuver).pack(
            side="left", padx=(5, 0)
        )
        self.remove = ttk.Button(buttons, icon="dash-circle", text="Delete Maneuver", bootstyle="info",
                                 command=self._delete_maneuver).pack(
            side="left", padx=(5, 0)
        )
        self.remove.state(["disabled"])

        ttk.Button(buttons, icon="x-circle-fill", text="Cancel", bootstyle="danger", command=self.destroy).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(buttons, icon="check-circle-fill", text="Save", bootstyle="primary", command=self._save).pack(
            side="right")

        self.parent = parent
        self.on_save = on_save

        self.satellite_settings = SatelliteSettings(self.notebook, settings.get("orbits", None))
        self.maneuver_settings = []

        self._build_ui()
        self._center_on_parent()

        # Make it modal: block interaction with the main window until closed
        self.grab_set()
        self.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _add_maneuver(self):
        self.maneuver_settings.append(ManeuverSettings(self.notebook, self.on_save))
        self.notebook.add(self.maneuver_settings[-1], text=f"Maneuver {len(self.maneuver_settings)} Settings")
        self.remove.state(["!disabled"])

    def _delete_maneuver(self):
        active_index = self.notebook.index("current")
        if active_index > 0:
            self.notebook.forget(active_index)
        if self.notebook.index("end") <= 1:
            self.remove.state(["disabled"])

    # def _set_settings(self):

    def _build_ui(self):
        self.notebook.add(self.satellite_settings, text="Satellite Settings")

    def _save(self):
        self.on_save(
            {
                "orbits": self.satellite_settings.get_values(),
                "maneuvers": [pane.get_settings() for pane in self.maneuver_settings]
            }
        )
        self.destroy()

    def _center_on_parent(self):
        """
        Helper method to center the window on its parent.
        """
        self.update_idletasks()
        p = self.parent
        x = p.winfo_rootx() + (p.winfo_width() - self.winfo_width()) // 2
        y = p.winfo_rooty() + (p.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
