import numpy as np
import queue
import tkinter as tk
import ttkbootstrap as ttk

from SatSim.controller.time_slider import TimeSlider
from SatSim.model.simulate import Simulate
from SatSim.view.view_results import ResultsView


class SimController(ttk.Frame):
    """
    Runs the simulation and distributes the results to different plots.
    """

    def __init__(self, parent, model: Simulate, view: ResultsView, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.model = model
        self.view = view

        self.total_duration = ttk.DoubleVar(value=0)

        # Both start_var and end_var will be in min
        self.start_var = tk.DoubleVar(value=0.0)
        self.end_var = tk.DoubleVar(value=0.0)

        self._build_widgets()
        self._refresh_view()  # initial draw

    def _build_widgets(self):
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)
        self.info = ttk.Label(
            body,
            text=f"Total simulated span ≈ {self.total_duration.get() / 60:.1f} min",
            font=("TkDefaultFont", 10, "italic"),
        )
        self.info.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self.time_slider = TimeSlider(body, self.total_duration, self.start_var, self.end_var, lambda _=None: self._refresh_view())
        self.time_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0,10))
        self.total_duration.trace_add('write', lambda *args: self.time_slider.refresh())
        self.start_var.trace_add('write', lambda *args: self.time_slider.refresh())
        self.end_var.trace_add('write', lambda *args: self.time_slider.refresh())

        button_row = ttk.Frame(body)
        button_row.grid(row=5, column=0, pady=(10, 0), sticky="w")
        self.run_button = ttk.Button(button_row, text="Run Simulation",
                   command=lambda: self._run())
        self.run_button.pack(side="left", padx=4)

        self.progress = ttk.Progressbar(body, maximum=100, bootstyle="success-striped")
        self.progress.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        self.progress_q = queue.Queue()

        body.columnconfigure(0, weight=1)

    def _run(self):
        self.view.view3d.clear()
        self.view.pos_lvlh.clear()
        self.view.vel_lvlh.clear()
        self.view.delta_v.clear()

        # Disable UI elements
        self.run_button.config(state="disabled")
        self.progress["value"] = 0

        # Run model
        self.model.run_simulation()

        # Re-enable UI elements
        self.run_button.config(state="enabled")
        self.progress["value"] = 100

        # Update view - 3D
        palette = [ttk.Style().colors.get(c) for c in ttk.Style().colors]
        labels = ['Target', 'Chaser']
        for idx in range(0, len(self.model.orbits)):
            full_t, full_pos = self.model.get_full_positions(idx)
            self.view.view3d.add_orbit(full_t, full_pos, color=palette[idx % len(palette)], label=labels[idx])

        for impulse in self.model.impulse_results:
            self.view.view3d.add_impulse(impulse.time, impulse.pos, edgecolors=palette[1])

        # Update view - error
        _, pos_lvlh = self.model.get_pos_lvlh()
        self.view.pos_lvlh.add_positions(full_t, pos_lvlh, color=palette[1], label=labels[1])
        _, vel_lvlh = self.model.get_vel_lvlh()
        self.view.vel_lvlh.add_positions(full_t, vel_lvlh, color=palette[1], label=labels[1])

        # Update view - budget
        full_t, full_dv = self.model.get_delta_v()
        self.view.delta_v.add_positions(np.asarray(full_t), np.vstack([full_t, full_dv]), color=palette[1])

        # Update controller
        self.total_duration.set(self.model.get_total_duration())
        self._set_range(0.0, self.total_duration.get())
        self.info.config(text=f"Total simulated span ≈ {self.total_duration.get() / 60:.1f} min")

    def _set_range(self, start, end):
        self.start_var.set(start)
        self.end_var.set(end)
        self._refresh_view()

    def _refresh_view(self):
        """

        """
        t_min = self.start_var.get()
        t_max = self.end_var.get()

        self.view.view3d.update_times(t_min, t_max)
        self.view.pos_lvlh.update_times(t_min, t_max)
        self.view.vel_lvlh.update_times(t_min, t_max)
        self.view.delta_v.update_times(t_min, t_max)
