from dataclasses import asdict
import copy
from typing import Any
import tkinter as tk
import ttkbootstrap as ttk

from SatSim.model.settings_model import SettingsModel, HohmannSettingsModel, BiellipticSettingsModel, \
    PhasingSettingsModel, OrbitSettingsModel
from SatSim.controller.orbit_entry import OrbitEntry
from SatSim.controller.defaults_manual_entry import DefaultManualEntry


class SatelliteSettings(ttk.Frame):
    """
    Options for the target and chaser satellites.

    The target satellite will only have orbit parameters, while the chaser satellite will have initial orbit parameters
    and sensor and thruster parameters.
    """

    def __init__(self, parent, target_model: OrbitSettingsModel, chaser_model: OrbitSettingsModel):
        super().__init__(parent)
        target_frame = ttk.LabelFrame(self, text="Target")
        target_frame.pack(side="top", fill="both", expand=True, pady=5)
        self.target_entry = OrbitEntry(target_frame, target_model)
        self.target_entry.pack(side="top", fill="both", expand=True)
        chaser_frame = ttk.LabelFrame(self, text="Chaser")
        chaser_frame.pack(side="top", fill="both", expand=True, pady=5)
        self.chaser_entry = OrbitEntry(chaser_frame, chaser_model)
        self.chaser_entry.pack(side="top", fill="both", expand=True)


class HohmannSettings(ttk.Frame):
    def __init__(self, parent, model: HohmannSettingsModel, *args, **kwargs):
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
        """
        try:
            self.delta_v_total.set(str(self.model.delta_v_total))
            self.delta_t_total.set(str(self.model.delta_t))
        except (tk.TclError, ZeroDivisionError):
            self.delta_v_total.set("---")
            self.delta_t_total.set("---")
        if self.model.r_selection.get().lower() == "target":
            self.model.r_custom.set(self.model.target_init_orbit.to_orbit().radius)

    def _on_destroy(self, event):
        # <Destroy> event also fires for child widgets; only react to this frame.
        if event.widget is not self:
            return
        for var, trace_id in self._traces:
            var.trace_remove("write", trace_id)


class BiellipticSettings(ttk.Frame):
    def __init__(self, parent, model: BiellipticSettingsModel, *args, **kwargs):
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
        self.timeEntry = DefaultManualEntry(self, {"immediate": 0.0},
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
        if self.model.ratio_final_selection.get().lower() == "target":
            self.model.ratio_final_custom.set(1.0)

    def _on_destroy(self, event):
        # <Destroy> event also fires for child widgets; only react to this frame.
        if event.widget is not self:
            return
        for var, trace_id in self._traces:
            var.trace_remove("write", trace_id)


class PhasingSettings(ttk.Frame):
    def __init__(self, parent, model: PhasingSettingsModel, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.model = model

        ttk.Label(self, text="Intermediate Radius Ratio:").grid(row=0, column=0, padx=(5, 0), sticky="e")
        self.radiusIntEntry = ttk.Entry(self, textvariable=model.orbit_count)
        self.radiusIntEntry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

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
        Callback to handle any changes in the Phasing settings model.
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
        "Bielliptic": BiellipticSettings,
        "Phasing": PhasingSettings
    }
    MODELS = {
        "Hohmann": HohmannSettingsModel,
        "Bielliptic": BiellipticSettingsModel,
        "Phasing": PhasingSettingsModel
    }

    def __init__(self, parent, settings: SettingsModel, maneuver_idx: int):
        super().__init__(parent)

        self.settings = settings
        self.maneuver_idx = maneuver_idx

        self.page_label = ttk.Label(self)
        self.page_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.content = ttk.Frame(self)
        self.content.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.current_page: HohmannSettings | BiellipticSettings | PhasingSettings = None

        model = self.settings.orbit_maneuvers[self.maneuver_idx]
        if isinstance(model, HohmannSettingsModel):
            self.current_page = HohmannSettings(self.content, model)
            self.current_page.pack(fill="both", expand=True)
            self.page_label.config(text="Hohmann Transfer")
        elif isinstance(model, BiellipticSettingsModel):
            self.current_page = BiellipticSettings(self.content, model)
            self.current_page.pack(fill="both", expand=True)
            self.page_label.config(text="Bielliptic Transfer")
        elif isinstance(model, PhasingSettingsModel):
            self.current_page = PhasingSettings(self.content, model)
            self.current_page.pack(fill="both", expand=True)
            self.page_label.config(text="Phasing Orbit Transfer")
        else:
            raise ValueError("Unknown Maneuver Model")

        self.traces = []

        self.bind("<Destroy>", self._on_destroy)

    @staticmethod
    def create_new(parent, settings: SettingsModel, type: str) -> 'ManeuverSettings':
        """
        Factory function to create a new page from string.
        
        :param parent: Description
        :param settings: Description
        :param type: Description
        :return: ManeuverSettings page
        """
        if len(settings.orbit_maneuvers) == 0:
            chaser = settings.chaser_orbit
            target = settings.target_orbit
        else:
            chaser = settings.orbit_maneuvers[-1].chaser_model
            target = settings.orbit_maneuvers[-1].target_model
        settings.orbit_maneuvers.append(ManeuverSettings.MODELS[type](target, chaser))
        return ManeuverSettings(parent, settings, len(settings.orbit_maneuvers) - 1)

    def clear_traces(self) -> None:
        for var, trace_id in self.traces:
            try:
                var.trace_remove("write", trace_id)
            except tk.TclError:
                pass  # already gone
        self.traces.clear()

    def refresh(self, *args):
        if self.current_page is not None:
            self.current_page.refresh()

    def _on_destroy(self, event) -> None:
        # <Destroy> event also fires for child widgets, only react to this frame.
        if event.widget is not self:
            return
        self.clear_traces()


class ManeuverDialog(ttk.Toplevel):
    def __init__(self, parent, options=None):
        super().__init__(parent,
                         transient=parent,  # stays on top of the parent
                         resizable=(False, False)
                         )
        # self.geometry("250x150")
        self.title('Manuever Selection')
        self.parent = parent
        self.grab_set()  # Make window modal
        self.focus_set()

        self.selected_value = None
        options = list(ManeuverSettings.PAGES.keys())

        ttk.Label(self, text="Add Maneuver:", padding=10).pack()

        self.combo = ttk.Combobox(self, values=options, state="readonly")
        if options:
            self.combo.current(0)
        self.combo.pack(pady=10)

        btn_ok = ttk.Button(self, text="OK", command=self.on_ok, bootstyle="primary")
        btn_ok.pack(pady=5)

        # Wait here until this window is destroyed
        self._center_on_parent()
        parent.wait_window(self)

    def on_ok(self):
        self.selected_value = self.combo.get()
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
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.status_text = ttk.Label(self.body, width=50)
        self.status_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        buttons = ttk.Frame(self.body)
        buttons.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(buttons, icon="plus-circle", text="Add Maneuver", bootstyle="info",
                   command=self._add_maneuver).pack(
            side="left", padx=(5, 0)
        )
        self.remove = ttk.Button(buttons, icon="dash-circle", text="Delete Maneuver", bootstyle="info",
                                 command=self._delete_maneuver)
        self.remove.pack(
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
                                                    self.settings.chaser_orbit)
        self.maneuver_settings = []

        self._build_ui()
        self._center_on_parent()

        # Make it modal: block interaction with the main window until closed
        self.grab_set()
        self.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _link_maneuver(self, idx: int) -> None:
        """
        Wire maneuver page `idx` to the things it depends on.

        idx == 0: chaser is settings.chaser_init_orbit itself, so the page only needs refreshing.
        idx > 0:  chaser is a private OrbitModel derived from the previous maneuver's result; keep it in sync.
                Chaining handles the rest: updating maneuver k's chaser fires maneuver k+1's sync.
        """
        page = self.maneuver_settings[idx]
        model = self.settings.orbit_maneuvers[idx]
        if model is None:
            return

        if idx == 0:
            page.traces.extend(model.target_init_orbit.register_cb(page.refresh))
            page.traces.extend(model.chaser_init_orbit.register_cb(page.refresh))
            return

        prev = self.settings.orbit_maneuvers[idx - 1]
        if prev is None:
            return

        def sync(*_):
            try:
                model.chaser_init_orbit.copy_from(prev.chaser_model)
            except (tk.TclError, ZeroDivisionError, ValueError):
                return  # previous page is mid-edit or invalid; keep the last good values
            page.refresh()

        # Everything prev.result_model depends on:
        page.traces.extend(prev.register_cb(sync))  # its own selections / custom values
        page.traces.extend(prev.chaser_init_orbit.register_cb(sync))  # previous link in the chain
        page.traces.extend(prev.target_init_orbit.register_cb(sync))  # r_final when set to "target"
        sync()

    def _load_maneuvers(self):
        for idx in range(len(self.settings.orbit_maneuvers)):
            self.maneuver_settings.append(ManeuverSettings(self.notebook, self.settings, idx))
            self._link_maneuver(idx)
            self.notebook.add(self.maneuver_settings[-1], text=f"Maneuver {len(self.maneuver_settings)} Settings")
        if len(self.settings.orbit_maneuvers) > 0:
            self.remove.state(["!disabled"])

    def _add_maneuver(self):
        dialog = ManeuverDialog(self)
        type = dialog.selected_value
        if type is None:
            return

        new_maneuver = ManeuverSettings.create_new(self.notebook, self.settings, type)
        self.maneuver_settings.append(new_maneuver)
        self._link_maneuver(len(self.maneuver_settings) - 1)

        self.notebook.add(new_maneuver, text=f"Maneuver {len(self.maneuver_settings)} Settings")
        self.remove.state(["!disabled"])
        self.notebook.select(self.notebook.index("end") - 1)
        self.status_text.config(text="Maneuver Added", bootstyle="info")

    def _delete_maneuver(self):
        active_index = self.notebook.index("current")

        if active_index == 0:
            return
        maneuver_idx = active_index - 1  # assumes tab 0 is the satellite page
        page = self.maneuver_settings.pop(maneuver_idx)
        self.settings.orbit_maneuvers.pop(maneuver_idx)
        self.notebook.forget(active_index)
        page.destroy()

        # The successor has shifted into slot idx, but its traces still point at the deleted model.
        if maneuver_idx < len(self.maneuver_settings):
            successor = self.maneuver_settings[maneuver_idx]
            successor.clear_traces()
            if maneuver_idx == 0:
                # It's now first in the chain, so its chaser is the satellite page's chaser again.
                self.settings.orbit_maneuvers[0].chaser_init_orbit = self.settings.chaser_orbit
            self._link_maneuver(maneuver_idx)  # rewires to the new predecessor and re-syncs its chaser
            successor.refresh()

        # Tab titles are numbered, so renumber them.
        for n, p in enumerate(self.maneuver_settings, start=1):
            self.notebook.tab(p, text=f"Maneuver {n} Settings")

        if self.notebook.index("end") <= 1:
            self.remove.state(["disabled"])
        self.status_text.config(text="Maneuver Removed", bootstyle="warning")

    def _on_tab_changed(self, event):
        if self.notebook.index("current") == 0:
            self.remove.state(["disabled"])
        else:
            self.remove.state(["!disabled"])

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
