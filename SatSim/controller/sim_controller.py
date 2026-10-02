import tkinter as tk
import ttkbootstrap as ttk

from SatSim.controller.label_entry import LabelEntryRow
from SatSim.model import simulate
from SatSim.model.orbit_model import OrbitModel
from SatSim.model.simulate import Simulate
# from SatSim.view import palette
from SatSim.view.view_3d import View3D


class SimController(ttk.Frame):
    """

    """

    def __init__(self, parent, model: Simulate, view3d: View3D, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.model = model
        self.chaser_idx = model.add_orbit(OrbitModel())
        self.target_idx = model.add_orbit(OrbitModel())

        self.view3d = view3d

        self.total_duration = 0

        # Both start_var and end_var will be in min
        self.start_var = tk.DoubleVar(value=0.0)
        self.end_var = tk.DoubleVar(value=0.0)

        self._build_widgets()
        self._refresh_view()  # initial draw

    def _build_widgets(self):
        info = ttk.Label(
            self,
            text=f"Total simulated span ≈ {self.total_duration / 60:.1f} min",
            font=("TkDefaultFont", 10, "italic"),
        )
        info.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        total_min = self.total_duration / 60.0

        # --- Start time slider ---
        ttk.Label(self, text="Start time (min):").grid(row=1, column=0, sticky="w")
        self.start_scale = ttk.Scale(
            self, from_=0.0, to=total_min, variable=self.start_var,
            orient="horizontal", command=lambda _=None: self._on_slide(),
            length=320,
        )
        self.start_scale.grid(row=1, column=1, sticky="ew", padx=8)
        self.start_label = ttk.Label(self, text=f"{self.start_var.get():.1f}")
        self.start_label.grid(row=1, column=2, sticky="w")

        # --- End time slider ---
        ttk.Label(self, text="End time (min):").grid(row=2, column=0, sticky="w")
        self.end_scale = ttk.Scale(
            self, from_=0.0, to=total_min, variable=self.end_var,
            orient="horizontal", command=lambda _=None: self._on_slide(),
            length=320,
        )
        self.end_scale.grid(row=2, column=1, sticky="ew", padx=8)
        self.end_label = ttk.Label(self, text=f"{self.end_var.get():.1f}")
        self.end_label.grid(row=2, column=2, sticky="w")

        self.chaser_entry = LabelEntryRow(self, self.model.orbits[self.chaser_idx].get_params().keys())
        self.chaser_entry.grid(row=3, column=0, sticky="ew")
        self.chaser_entry.set_values(self.model.orbits[self.chaser_idx].get_params())
        self.target_entry = LabelEntryRow(self, self.model.orbits[self.target_idx].get_params().keys())
        self.target_entry.grid(row=4, column=0, sticky="ew")
        self.target_entry.set_values(self.model.orbits[self.target_idx].get_params())

        button_row = ttk.Frame(self)
        button_row.grid(row=5, column=0, columnspan=3, pady=(10, 0), sticky="w")
        ttk.Button(button_row, text="Run Simulation",
                   command=lambda: self._run()).pack(side="left", padx=4)

        self.columnconfigure(1, weight=1)

    def _run(self):
        self.view3d.clear()
        self.model.orbits[self.chaser_idx].set_params(**(self.chaser_entry.get_values()))
        self.model.orbits[self.target_idx].set_params(**(self.target_entry.get_values()))

        self.model.run_simulation()
        palette = [ttk.Style().colors.get(c) for c in ttk.Style().colors]
        for idx in [self.chaser_idx, self.target_idx]:
            full_t, full_pos = self.model.get_full_positions(idx)
            self.view3d.add_orbit(full_t, full_pos, color=palette[idx % len(palette)])

        self.total_duration = self.model.get_total_duration()
        self.start_scale.configure(to=self.total_duration / 60)
        self.end_scale.configure(to=self.total_duration / 60)
        self._set_range(0.0, self.total_duration / 60)

    def _on_slide(self):
        # Enforce start <= end so the selected window is always valid.
        start = self.start_var.get()
        end = self.end_var.get()
        if start > end:
            # Snap the slider that was just moved back so the range stays valid.
            if float(self.start_scale.get()) != start:
                pass
            start, end = min(start, end), max(start, end)
            self.start_var.set(start)
            self.end_var.set(end)

        self.start_label.config(text=f"{start:.1f}")
        self.end_label.config(text=f"{end:.1f}")
        self._refresh_view()

    def _set_range(self, start_min, end_min):
        self.start_var.set(start_min)
        self.end_var.set(end_min)
        self.start_label.config(text=f"{start_min:.1f}")
        self.end_label.config(text=f"{end_min:.1f}")
        self._refresh_view()

    def _refresh_view(self):
        """

        """
        # *60 because slider is in minutes, but data is in seconds
        t_min = self.start_var.get() * 60.0
        t_max = self.end_var.get() * 60.0

        self.view3d.update_times(t_min, t_max)
