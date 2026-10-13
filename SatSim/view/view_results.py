import ttkbootstrap as ttk

from SatSim.view.plot import Plot
from SatSim.view.view_3d import View3D
from SatSim.view.view_2d import View2D

class QuadPlotsView(ttk.Frame):
    def __init__(self, parent,  *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

        main_pane = ttk.Panedwindow(self.body, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        left_pane = ttk.Panedwindow(main_pane, orient="vertical")
        main_pane.add(left_pane, weight=1)

        right_pane = ttk.Panedwindow(main_pane, orient="vertical")
        main_pane.add(right_pane, weight=1)

        self.plot_ne = View2D(right_pane)
        self.plot_nw = View2D(left_pane)
        self.plot_se = View2D(right_pane)
        self.plot_sw = View2D(left_pane)

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

        self.ax_lvlh = self.viewQuadPlots.plot_ne
        self.ax_lvlh.ax.set_title('Target Local Vertical, Local Horizontal')