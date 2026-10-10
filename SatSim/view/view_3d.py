import tkinter as tk
import traceback
import ttkbootstrap as ttk

from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
# from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers the 3D projection)
import numpy as np

from SatSim.common import earth
from SatSim.view.plot import Plot

import traceback


class OrbitView:
    def __init__(self, ax: Axes, times: np.ndarray, pos: np.ndarray, *args, **kwargs):
        self.ax = ax
        self.times = times
        self.pos = pos

        self.args = args
        self.kwargs = kwargs

        colors = ttk.Style().colors

        self.full_path = self.ax.plot(self.pos[:, 0], self.pos[:, 1], self.pos[:, 2],
                                      color=colors.border, linewidth=0.7, alpha=0.8, label="Full simulated path")
        self.timed_path = self.ax.plot(self.pos[:, 0], self.pos[:, 1], self.pos[:, 2],
                                       linewidth=3.0, *args, **kwargs)
        # kwargs.pop('label')
        # , label='_nolegend_'
        self.marker = self.ax.scatter(*pos[-1], *args, **kwargs)

    def clear(self):
        """
        Clears all plots and markers.
        """
        self.full_path[0].remove()
        self.full_path = None
        self.timed_path[0].remove()
        self.timed_path = None
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
        if self.timed_path is not None:
            self.timed_path[0].remove()  # error here when timed_path is 0 length or small? I.e., when end <= begin
        if self.marker is not None:
            self.marker.remove()

        self.timed_path = self.ax.plot(self.pos[indices, 0], self.pos[indices, 1], self.pos[indices, 2], *self.args,
                                       **self.kwargs)
        self.marker = self.ax.scatter(*self.pos[indices][-1], *self.args, **self.kwargs)
        self.ax.redraw_in_frame()


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

        self.orbits = []
        self.impulses: list[PathCollection] = []

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
        self._refresh()

    def add_orbit(self, *args, **kwargs):
        self.orbits.append(OrbitView(self.ax, *args, **kwargs))
        self.t_min = self.orbits[-1].times[0]
        self.t_max = self.orbits[-1].times[-1]

        self.update_times(self.t_min, self.t_max)
        self._refresh()

    def add_impulse(self, xs, ys, zs, *args, **kwargs):
        self.impulses.append(
            self.plot.ax.scatter(xs, ys, zs, *args, **kwargs, marker='^', facecolors='none', label="Impulse"))

    def clear(self):
        for orbit in self.orbits:
            orbit.clear()
        for impulse in self.impulses:
            impulse.remove()
        self.impulses = []

        self.orbits = []
        self.plot.ax.redraw_in_frame()
        self.t_min = None
        self.t_max = None
        self.plot.set_legend_below()  # drops the now-empty legend
        self.plot.refresh()
