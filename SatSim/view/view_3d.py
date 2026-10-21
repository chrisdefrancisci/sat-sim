import tkinter as tk
import ttkbootstrap as ttk

from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
# from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers the 3D projection)
import numpy as np

from SatSim.common import earth
from SatSim.view.plot import Plot


class OrbitView:
    def __init__(self, ax: Axes, times: np.ndarray, pos: np.ndarray, *args, **kwargs):
        self.ax = ax
        self.times = times
        self.pos = pos
        self.args = args
        self.kwargs = kwargs

        colors = ttk.Style().colors

        self.full_path:list[Line2D] = self.ax.plot(self.pos[0, :], self.pos[1, :], self.pos[2, :],
                                      color=colors.border, linewidth=0.7, alpha=0.8, label="Full simulated path")
        self.timed_path:list[Line2D] = self.ax.plot(self.pos[0, :], self.pos[1, :], self.pos[2, :], *args,
                                       linewidth=3.0, **kwargs)
        self.marker:PathCollection|None = self.ax.scatter(*pos[:,-1], *args, **kwargs)

    def clear(self):
        """
        Clears all plots and markers.
        """
        self.full_path[0].remove()
        self.full_path = []
        self.timed_path[0].remove()
        self.timed_path = []
        if self.marker is not None:
            self.marker.remove()
        self.marker = None
        self.ax.redraw_in_frame()

    def update(self, t_min, t_max):
        """
        Updates the plots and markers based on display times.

        :param t_min: Minimum time to display.
        :param t_max: Maximum time to display. Marker is also displayed at this time.
        """
        indices = (t_min <= self.times) & (self.times <= t_max)
        if not indices.any():
            indices = np.zeros_like(self.times, dtype=bool)
            indices[np.argmin(np.abs(self.times - t_max))] = True
        if len(self.timed_path) != 0:
            self.timed_path[0].remove()
        if self.marker is not None:
            self.marker.remove()

        self.timed_path = self.ax.plot(self.pos[0, indices], self.pos[1, indices], self.pos[2, indices], *self.args,
                                       **self.kwargs)
        self.marker = self.ax.scatter(*self.pos[:, indices][:, -1], *self.args, **self.kwargs)
        self.ax.redraw_in_frame()

class ImpulseView:
    
    def __init__(self, ax: Axes, time: np.ndarray|float, pos: np.ndarray, *args, **kwargs):
        self.ax = ax
        self.time = time
        self.pos = pos
        self.args = args
        self.kwargs = kwargs
        colors = ttk.Style().colors
        self.full_impulse: PathCollection = self.ax.scatter(*pos, marker='^', facecolors='none', edgecolors=colors.border, linewidth=0.7, alpha=0.8, label="All Impulse")
        self.time_impulse: PathCollection|None = None

    def clear(self):
        self.full_impulse.remove()
        if self.time_impulse is not None:
            self.time_impulse.remove()
            self.time_impulse = None
    
    def update(self, t_min, t_max):
        if t_min <= self.time <= t_max:
            if self.time_impulse is None:
                self.time_impulse = self.ax.scatter(*self.pos, *self.args, **self.kwargs, marker='^', facecolors='none', label="Impulse")
        elif self.time_impulse is not None:
            self.time_impulse.remove()
            self.time_impulse = None

class View3D(ttk.Frame):
    """
    Presents a 3D view of the Earth and satellite orbits.
    """

    def __init__(self, parent):
        """
        Constructor.
        :param parent: Parent frame.
        """
        super().__init__(parent)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

        self.plot = Plot(self.body, projection='3d')
        self.plot.pack(fill='both', expand=True)

        self.ax = self.plot.ax

        self._draw_earth()

        self.t_min = None
        self.t_max = None

        self.orbits: list[OrbitView] = []
        self.impulses: list[ImpulseView] = []

    def _draw_earth(self):
        """
        Draw a translucent sphere representing the Earth.
        """
        palette = [ttk.Style().colors.get(c) for c in ttk.Style().colors]
        u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:20j]
        x = earth.radius * np.cos(u) * np.sin(v)
        y = earth.radius * np.sin(u) * np.sin(v)
        z = earth.radius * np.cos(v)
        self._earth_surface = self.ax.plot_surface(
            x, y, z, color=ttk.Style().colors.inputfg, alpha=0.35, linewidth=0, antialiased=True
        )
        self.ax.set_aspect("equal")
        self.ax.set_box_aspect([1, 1, 1])

    def _refresh(self):
        """
        Refresh the plot, ensuring uniform aspect is maintained.
        """

        extents = np.array(
            [self.ax.xaxis.get_data_interval(), self.ax.yaxis.get_data_interval(), self.ax.zaxis.get_data_interval()])
        centers = np.mean(extents, axis=1)
        max_range = max(extents[:, 1] - extents[:, 0])
        half_range = max_range / 2

        self.ax.set_xlim3d(centers[0] - half_range, centers[0] + half_range)
        self.ax.set_ylim3d(centers[1] - half_range, centers[1] + half_range)
        self.ax.set_zlim3d(centers[2] - half_range, centers[2] + half_range)
        self.ax.set_box_aspect([1, 1, 1])

        self.plot.set_legend_below()
        self.plot.refresh()

    def update_times(self, t_min, t_max):
        self.t_min = t_min
        self.t_max = t_max
        for orbit in self.orbits:
            orbit.update(t_min, t_max)
        for impulse in self.impulses:
            impulse.update(t_min, t_max)
        self._refresh()

    def add_orbit(self, *args, **kwargs):
        self.orbits.append(OrbitView(self.ax, *args, **kwargs))
        self.t_min = self.orbits[-1].times[0]
        self.t_max = self.orbits[-1].times[-1]

        self.update_times(self.t_min, self.t_max)
        self._refresh()

    def add_impulse(self, *args, **kwargs):
        self.impulses.append(ImpulseView(self.ax, *args, **kwargs))
        self.update_times(self.t_min, self.t_max)
        self._refresh()

    def clear(self):
        for orbit in self.orbits:
            orbit.clear()
        for impulse in self.impulses:
            impulse.clear()
        self.impulses = []

        self.orbits = []
        self.plot.ax.redraw_in_frame()
        self.t_min = None
        self.t_max = None
        self.plot.set_legend_below()  # drops the now-empty legend
        self.plot.refresh()
