import ttkbootstrap as ttk

class TimeSlider(ttk.Frame):
    def __init__(self, parent, duration: ttk.DoubleVar, start: ttk.DoubleVar, end: ttk.DoubleVar, command, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.duration = duration
        self.start = start
        self.end = end
        total_min = duration.get() / 60.0

        self.command = command

        ttk.Label(self, text="Start time (min):").grid(row=1, column=0, sticky="w")
        self.start_scale = ttk.Scale(
            self, from_=0.0, to=total_min, variable=self.start,
            orient="horizontal", command=command,
            length=320,
        )
        self.start_scale.grid(row=1, column=1, sticky="ew", padx=8)
        self.start_label = ttk.Label(self, text=f"{self.start.get():.1f}")
        self.start_label.grid(row=1, column=2, sticky="w")

        # --- End time slider ---
        ttk.Label(self, text="End time (min):").grid(row=2, column=0, sticky="w")
        self.end_scale = ttk.Scale(
            self, from_=0.0, to=total_min, variable=self.end,
            orient="horizontal", command=command,
            length=320,
        )
        self.end_scale.grid(row=2, column=1, sticky="ew", padx=8)
        self.end_label = ttk.Label(self, text=f"{self.end.get():.1f}")
        self.end_label.grid(row=2, column=2, sticky="w")

        self.columnconfigure(1, weight=1)

    def _on_slide(self, *args):
        # Enforce start <= end so the selected window is always valid.
        start = self.start.get()
        end = self.end.get()
        if start > end:
            # Snap the slider that was just moved back so the range stays valid.
            if float(self.start_scale.get()) != start:
                pass
            start, end = min(start, end), max(start, end)
            self.start.set(start)
            self.end.set(end)

        self.start_label.config(text=f"{start / 60.0:.1f}")
        self.end_label.config(text=f"{end / 60.0:.1f}")

        self.command()

    def refresh(self):
        start_min = self.start.get() / 60.0
        end_min = self.end.get() / 60.0
        self.start_label.config(text=f"{start_min:.1f}")
        self.end_label.config(text=f"{end_min:.1f}")
        self.start_scale.configure(to=self.duration.get())
        self.end_scale.configure(to=self.duration.get())
        

    