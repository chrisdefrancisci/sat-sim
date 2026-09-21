import tkinter as tk
from tkinter import ttk
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers the 3D projection)
import numpy as np

from constants import earth


class View3D(ttk.Frame):
    """
    Presents a 3D view of the Earth and satellite orbits.
    """

    def __init__(self, parent: ttk.Frame):
        """
        Constructor.
        :param parent: Parent frame.
        """
        super().__init__(parent)

        self.figure = Figure(figsize=(6.5, 6.5), dpi=100)
        self.ax = self.figure.add_subplot(111, projection="3d")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        self._draw_earth()

        self.orbits = []

    def _draw_earth(self):
        """
        Draw a translucent sphere representing the Earth.
        """
        u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:20j]
        x = earth.radius * np.cos(u) * np.sin(v)
        y = earth.radius * np.sin(u) * np.sin(v)
        z = earth.radius * np.cos(v)
        self._earth_surface = self.ax.plot_surface(
            x, y, z, color="steelblue", alpha=0.35, linewidth=0, antialiased=True
        )
        self.ax.set_aspect("equal")
        self.ax.set_box_aspect([1, 1, 1])


class OrbitView:
    def __init__(self, ax: Axes, times: np.ndarray, pos: np.ndarray, *args, **kwargs):
        self.ax = ax
        self.times = times
        self.pos = pos
