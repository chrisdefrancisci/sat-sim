import ttkbootstrap as ttk

from SatSim.view import plot
from SatSim.view.plot import Plot
from SatSim.view.view_3d import View3D

class QuadPlotsView(ttk.Frame):
    def __init__(self, parent,  *args, **kwargs):
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

        self.plot_ne = Plot(right_pane)
        self.plot_nw = Plot(left_pane)
        self.plot_se = Plot(right_pane)
        self.plot_sw = Plot(left_pane)

        # 4. Create and add widgets to the Left Pane
        q1 = ttk.Label(left_pane, text="Quadrant 1 (Top Left)", bootstyle="primary-inverse", anchor="center")
        q3 = ttk.Label(left_pane, text="Quadrant 3 (Bottom Left)", bootstyle="secondary-inverse", anchor="center")
        left_pane.add(self.plot_nw, weight=1)
        left_pane.add(self.plot_sw, weight=1)

        right_pane.add(self.plot_ne, weight=1)
        right_pane.add(self.plot_se, weight=1)

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

        self.ax_lvlh = self.viewQuadPlots.plot_ne.ax
        self.ax_lvlh.set_title('Target Local Vertical, Local Horizontal')