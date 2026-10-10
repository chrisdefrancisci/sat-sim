from dataclasses import asdict
import copy
from typing import Any
import tkinter as tk
import ttkbootstrap as ttk

from SatSim.model.settings_model import SettingsModel, HohmannModel, BiellipticModel, OrbitModel
from SatSim.controller.orbit_entry import OrbitEntry
from SatSim.controller.defaults_manual_entry import DefaultManualEntry


class SatelliteSettings(ttk.Frame):
    """
    Options for the target and interceptor satellites.

    The target satellite will only have orbit parameters, while the interceptor satellite will have initial orbit parameters
    and sensor and thruster parameters.
    """

    def __init__(self, parent, target_model: OrbitModel, interceptor_model: OrbitModel):
        super().__init__(parent)
        target_frame = ttk.LabelFrame(self, text="Target")
        target_frame.pack(side="top", fill="both", expand=True, pady=5)
        self.target_entry = OrbitEntry(target_frame, target_model)
        self.target_entry.pack(side="top", fill="both", expand=True)
        interceptor_frame = ttk.LabelFrame(self, text="Interceptor")
        interceptor_frame.pack(side="top", fill="both", expand=True, pady=5)
        self.interceptor_entry = OrbitEntry(interceptor_frame, interceptor_model)
        self.interceptor_entry.pack(side="top", fill="both", expand=True)


class HohmannSettings(ttk.Frame):
    def __init__(self, parent, model: HohmannModel, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.model = model
        ttk.Label(self, text="Final Radius (km):").grid(row=0, column=0, padx=(5, 0), sticky="e")
        self.radiusEntry = DefaultManualEntry(self, {"target": 0.0}, ["Target Orbit Radius", ],
                                              selection_var=model.r_selection, entry_var=model.r_custom)
        self.radiusEntry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ttk.Label(self, text="Maneuver Time (s):").grid(row=1, column=0, padx=(5, 0), sticky="e")
        self.timeEntry = DefaultManualEntry(self, {"immediate": 0.0, "rendezvous": 0.0},
                                            selection_var=model.t_selection, entry_var=model.t_custom)
        self.timeEntry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

        self.columnconfigure(1, weight=1)

        result_row = ttk.Frame(self)
        result_row.grid(row=2, column=1, columnspan=2, sticky="ew")
        ttk.Label(result_row, text="Delta-v = ").pack(side="left", padx=(5, 0), pady=5)
        self.delta_v_total = ttk.StringVar(value="Unknown")
        ttk.Label(result_row, textvariable=self.delta_v_total, bootstyle="secondary").pack(side="left", padx=(5, 0),
                                                                                           pady=5)
        ttk.Label(result_row, text="(km/s)").pack(side="left", padx=5, pady=5)
        ttk.Label(result_row, text="Delta-t = ").pack(side="left", padx=(5, 0), pady=5)
        self.delta_t_total = ttk.StringVar(value="Unknown")
        ttk.Label(result_row, textvariable=self.delta_t_total, bootstyle="secondary").pack(side="left", padx=(5, 0),
                                                                                           pady=5)
        ttk.Label(result_row, text="(s)").pack(side="left", padx=5, pady=5)

        # Register the callback and set the "view" - populate the calculated values
        self._traces = model.register_cb(self.refresh)
        self.refresh()
        # Remove traces when this page is destroyed.
        self.bind("<Destroy>", self._on_destroy)

    def refresh(self, *_):
        """
        Callback to handle any changes in the Hohmann settings model.
        :param _: Description
        """
        self.delta_v_total.set(str(self.model.delta_v_total))
        self.delta_t_total.set(str(self.model.delta_t))

    def _on_destroy(self, event):
        # <Destroy> event also fires for child widgets; only react to this frame.
        if event.widget is not self:
            return
        for var, trace_id in self._traces:
            var.trace_remove("write", trace_id)


class BiellipticSettings(ttk.Frame):
    def __init__(self, parent, model: BiellipticModel, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.model = model
        ttk.Label(self, text="Intermediate Radius Ratio:").grid(row=0, column=0, padx=(5, 0), sticky="e")
        self.radiusIntEntry = DefaultManualEntry(self, {"target": 15.0}, ["15x Target Orbit Radius", ],
                                                 selection_var=model.ratio_int_selection,
                                                 entry_var=model.ratio_int_custom)
        self.radiusIntEntry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ttk.Label(self, text="Final Radius Ratio:").grid(row=1, column=0, padx=(5, 0), sticky="e")
        self.radiusFinalEntry = DefaultManualEntry(self, {"target": 1.0}, ["Target Orbit Radius", ],
                                                   selection_var=model.ratio_final_selection,
                                                   entry_var=model.ratio_final_custom)
        self.radiusFinalEntry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

        ttk.Label(self, text="Maneuver Time (s):").grid(row=2, column=0, padx=(5, 0), sticky="e")
        self.timeEntry = DefaultManualEntry(self, {"immediate": 0.0, "rendezvous": 0.0},
                                            selection_var=model.t_selection, entry_var=model.t_custom)
        self.timeEntry.grid(row=2, column=1, sticky="ew", pady=(0, 5))

        self.columnconfigure(1, weight=1)

        result_row = ttk.Frame(self)
        result_row.grid(row=3, column=1, columnspan=2, sticky="ew")
        ttk.Label(result_row, text="Delta-v = ").pack(side="left", padx=(5, 0), pady=5)
        self.delta_v_total = ttk.StringVar(value="Unknown")
        ttk.Label(result_row, textvariable=self.delta_v_total, bootstyle="secondary").pack(side="left", padx=(5, 0),
                                                                                           pady=5)
        ttk.Label(result_row, text="(km/s)").pack(side="left", padx=5, pady=5)
        ttk.Label(result_row, text="Delta-t = ").pack(side="left", padx=(5, 0), pady=5)
        self.delta_t_total = ttk.StringVar(value="Unknown")
        ttk.Label(result_row, textvariable=self.delta_t_total, bootstyle="secondary").pack(side="left", padx=(5, 0),
                                                                                           pady=5)
        ttk.Label(result_row, text="(s)").pack(side="left", padx=5, pady=5)

        # Register the callback and set the "view" - populate the calculated values
        self._traces = model.register_cb(self.refresh)
        self.refresh()
        # Remove traces when this page is destroyed.
        self.bind("<Destroy>", self._on_destroy)

    def refresh(self, *_):
        """
        Callback to handle any changes in the Hohmann settings model.
        :param _: Description
        """
        try:
            self.delta_v_total.set(str(self.model.delta_v_total))
            self.delta_t_total.set(str(self.model.delta_t))
        except (tk.TclError, ZeroDivisionError):
            self.delta_v_total.set("---")
            self.delta_t_total.set("---")

    def _on_destroy(self, event):
        # <Destroy> event also fires for child widgets; only react to this frame.
        if event.widget is not self:
            return
        for var, trace_id in self._traces:
            var.trace_remove("write", trace_id)


class ManeuverSettings(ttk.Frame):
    PAGES = {
        "Hohmann": HohmannSettings,
        "Bielliptic": BiellipticSettings
    }
    MODELS = {
        "Hohmann": HohmannModel,
        "Bielliptic": BiellipticModel
    }

    def __init__(self, parent, settings: SettingsModel, maneuver_idx: int):
        super().__init__(parent)

        self.settings = settings
        self.maneuver_idx = maneuver_idx

        self.page_name = ttk.StringVar(value=list(self.PAGES.keys())[0])
        ttk.OptionMenu(self, self.page_name, self.page_name.get(),
                       *list(self.PAGES.keys()), command=self.change_page
                       ).grid(row=0, column=0, sticky="", padx=5, pady=5)
        self.content = ttk.Frame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.current_page = None
        model = self.settings.orbit_maneuvers[self.maneuver_idx]
        if isinstance(model, HohmannModel):
            self.current_page = HohmannSettings(self.content, model)
            self.current_page.pack(fill="both", expand=True)
            self.page_name.set("Hohmann")
        elif isinstance(model, BiellipticModel):
            self.current_page = BiellipticSettings(self.content, model)
            self.current_page.pack(fill="both", expand=True)
            self.page_name.set("Bielliptic")

    @staticmethod
    def create_new(parent, settings: SettingsModel) -> 'ManeuverSettings':
        idx = len(settings.orbit_maneuvers)
        settings.orbit_maneuvers.append(None)
        new_page = ManeuverSettings(parent, settings, idx)
        new_page.change_page(new_page.page_name.get())
        return new_page

    def change_page(self, name) -> None:
        if self.current_page is not None:
            self.current_page.destroy()

        # Build and show the new page
        new_model = self.MODELS[name](self.settings.target_orbit, self.settings.interceptor_orbit)
        self.current_page = self.PAGES[name](self.content, new_model)
        self.settings.orbit_maneuvers[self.maneuver_idx] = new_model
        self.current_page.pack(fill="both", expand=True)


class SettingsDialog(ttk.Toplevel):
    """
    Modal window for displaying and editing settings.
    """

    def __init__(self, parent, settings: SettingsModel):
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
        self.status_text = ttk.Label(self.body, width=50)
        self.status_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        buttons = ttk.Frame(self.body)
        buttons.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
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

        self.settings_permanent = settings
        self.settings = copy.deepcopy(settings)
        self.parent = parent

        self.satellite_settings = SatelliteSettings(self.notebook, self.settings.target_orbit,
                                                    self.settings.interceptor_orbit)
        self.maneuver_settings = []

        self._build_ui()
        self._center_on_parent()

        # Make it modal: block interaction with the main window until closed
        self.grab_set()
        self.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _load_maneuvers(self):
        for idx in range(0, len(self.settings.orbit_maneuvers)):
            self.maneuver_settings.append(ManeuverSettings(self.notebook, self.settings, idx))
            self.notebook.add(self.maneuver_settings[-1], text=f"Maneuver {len(self.maneuver_settings)} Settings")
        if len(self.settings.orbit_maneuvers) > 0:
            self.remove.state(["!disabled"])

    def _add_maneuver(self):
        self.maneuver_settings.append(ManeuverSettings.create_new(self.notebook, self.settings))
        self.notebook.add(self.maneuver_settings[-1], text=f"Maneuver {len(self.maneuver_settings)} Settings")
        self.remove.state(["!disabled"])
        self.status_text.config(text="Maneuver Added", bootstyle="info")

    def _delete_maneuver(self):
        active_index = self.notebook.index("current")
        if active_index > 0:
            self.notebook.forget(active_index)
        if self.notebook.index("end") <= 1:
            self.remove.state(["disabled"])
        self.status_text.config(text="Maneuver Removed", bootstyle="warning")

    def _build_ui(self):
        self.notebook.add(self.satellite_settings, text="Satellite Settings")
        self._load_maneuvers()

    def _save(self):
        self.settings_permanent.__dict__.clear()
        self.settings_permanent.__dict__.update(self.settings.__dict__)
        self.destroy()

    def _center_on_parent(self):
        """
        Helper method to center the window on its parent. 

        Centered in the x direction, aligned to the top of the window in the y direction.
        """
        self.update_idletasks()
        p = self.parent
        x = p.winfo_rootx() + (p.winfo_width() - self.winfo_width()) // 2
        y = p.winfo_rooty()
        self.geometry(f"+{x}+{y}")
