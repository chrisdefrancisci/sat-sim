import ttkbootstrap as ttk

from SatSim.view.plot import Plot
from SatSim.view.view_3d import View3D
from SatSim.view.view_2d import View2D, ViewRpy
from SatSim.view.plot import PlotSubplots


class LrPlotsView(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

        main_pane = ttk.Panedwindow(self.body, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        left_pane = ttk.Panedwindow(main_pane, orient="vertical")
        main_pane.add(left_pane, weight=1)

        right_pane = ttk.Panedwindow(main_pane, orient="vertical")
        main_pane.add(right_pane, weight=1)

        self.plot_left = View2D(left_pane)
        self.plot_right = View2D(right_pane)

        left_pane.add(self.plot_left, weight=1)
        right_pane.add(self.plot_right, weight=1)


class QuadPlotsView(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
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
        # self.plot_nw = View2D(left_pane)
        self.plot_nw = ViewRpy(left_pane)
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

        # 3-D view
        self.view3d = View3D(self.notebook)
        self.notebook.add(self.view3d, text="3-D View")

        # 2-D error plots view
        self.viewError = QuadPlotsView(self.notebook)
        self.notebook.add(self.viewError, text="Error Plots")

        self.pos_lvlh = self.viewError.plot_ne
        self.pos_lvlh.ax.set_title('Chaser Pos in Target Local Vertical, Local Horizontal')
        self.pos_lvlh.ax.set_xlabel('Radial (km)')
        self.pos_lvlh.ax.set_ylabel('In-track (km)')

        self.vel_lvlh = self.viewError.plot_se
        self.vel_lvlh.ax.set_title('Chaser Vel in Target Local Vertical, Local Horizontal')
        self.vel_lvlh.ax.set_xlabel('Radial (km/s)')
        self.vel_lvlh.ax.set_ylabel('In-track (km/s)')

        # Angle plots view
        self.view_rpy = self.viewError.plot_nw

        # Fuel consumption view
        self.viewBudget = LrPlotsView(self.notebook)
        self.notebook.add(self.viewBudget, text="Budget Plots")
        self.delta_v = self.viewBudget.plot_right
        self.delta_v.ax.set_title('Delta-v plot')
        self.delta_v.ax.set_xlabel('Time (min)')
        self.delta_v.ax.set_ylabel('Delta v (km/s)')
