import ttkbootstrap as ttk

from SatSim.view.plot import Plot
from SatSim.view.view_3d import View3D

class QuadPlotsView(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

        main_pane = ttk.Panedwindow(self.body, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        # 2. Create the Left Vertical PanedWindow (Splits Top-Left and Bottom-Left)
        left_pane = ttk.Panedwindow(main_pane, orient="vertical")
        main_pane.add(left_pane, weight=1)

        # 3. Create the Right Vertical PanedWindow (Splits Top-Right and Bottom-Right)
        right_pane = ttk.Panedwindow(main_pane, orient="vertical")
        main_pane.add(right_pane, weight=1)

        # 4. Create and add widgets to the Left Pane
        q1 = ttk.Label(left_pane, text="Quadrant 1 (Top Left)", bootstyle="primary-inverse", anchor="center")
        q3 = ttk.Label(left_pane, text="Quadrant 3 (Bottom Left)", bootstyle="secondary-inverse", anchor="center")
        left_pane.add(q1, weight=1)
        left_pane.add(q3, weight=1)

        # 5. Create and add widgets to the Right Pane
        q2 = ttk.Label(right_pane, text="Quadrant 2 (Top Right)", bootstyle="success-inverse", anchor="center")
        q4 = ttk.Label(right_pane, text="Quadrant 4 (Bottom Right)", bootstyle="info-inverse", anchor="center")
        right_pane.add(Plot(right_pane), weight=1)
        right_pane.add(Plot(right_pane), weight=1)

class ResultsView(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(self.body)
        self.notebook.pack(fill="both", expand=True)

        self.view3d = View3D(self.notebook)
        self.notebook.add(self.view3d, text="3-D View")

        self.viewQuadPlots = QuadPlotsView(self.notebook)
        self.notebook.add(self.viewQuadPlots, text="Error Plots")