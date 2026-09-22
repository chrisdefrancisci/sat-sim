import tkinter as tk
from tkinter import ttk
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers the 3D projection)
import numpy as np

from SatSim.constants import earth


class OrbitView:
    def __init__(self, ax: Axes, times: np.ndarray, pos: np.ndarray, *args, **kwargs):
        self.ax = ax
        self.times = times
        self.pos = pos

        self.args = args
        self.kwargs = kwargs

        self.full_path = self.ax.plot(self.pos[:, 0], self.pos[:, 1], self.pos[:, 2],
                                      color="gray", linewidth=0.7, alpha=0.4, label="Full simulated path")
        self.timed_path = self.ax.plot(self.pos[:, 0], self.pos[:, 1], self.pos[:, 2],
                                       *args, **kwargs)
        self.marker = self.ax.scatter(pos[-1], *args, **kwargs)

    def clear(self):
        """
        Clears all plots and markers.
        """
        self.full_path.clear()
        self.timed_path.clear()
        self.marker.remove()

    def update(self, t_min, t_max):
        """
        Updates the plots and markers based on display times.

        :param t_min: Minimum time to display.
        :param t_max: Maximum time to display. Marker is also displayed at this time.
        """
        indices = np.where(t_min <= self.times <= t_max)
        self.timed_path.clear()
        self.marker.remove()
        self.timed_path = self.ax.plot(self.pos[indices, 0], self.pos[indices, 1], self.pos[indices, 2], *self.args,
                                       **self.kwargs)
        self.marker = self.ax.scatter(self.pos[indices[-1]], *self.args, **self.kwargs)
        self.ax.redraw_in_frame()


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

        self.t_min = None
        self.t_max = None

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

    def update_times(self, t_min, t_max):
        self.t_min = t_min
        self.t_max = t_max
        for orbit in self.orbits:
            orbit.update(t_min, t_max)
        self.canvas.draw_idle()

    def add_orbit(self, *args, **kwargs):
        self.orbits.append(OrbitView(self.ax, *args, **kwargs))
        # TODO: get max orbit and set window
        self.update_times(self.t_min, self.t_max)
