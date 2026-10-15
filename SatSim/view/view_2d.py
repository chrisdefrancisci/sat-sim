from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from SatSim.view.plot import Plot

class LineView:
    def __init__(self, ax: Axes, times: np.ndarray, pos: np.ndarray, *args, **kwargs):
        self.ax = ax
        self.times = times
        self.pos = pos

        self.args = args
        self.kwargs = kwargs

        colors = ttk.Style().colors

        self.full_path:list[Line2D] = self.ax.plot(self.pos[0, :], self.pos[1, :],
                                      color=colors.border, linewidth=0.7, alpha=0.8, label="Full simulated path")
        self.timed_path:list[Line2D]  = self.ax.plot(self.pos[0, :], self.pos[1, :],
                                       linewidth=3.0, *args, **kwargs)
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

        self.timed_path = self.ax.plot(self.pos[0, indices], self.pos[1, indices], *self.args,
                                       **self.kwargs)
        self.marker = self.ax.scatter(*self.pos[0:2, indices][:, -1], *self.args, **self.kwargs)
        self.ax.redraw_in_frame()

class View2D(ttk.Frame):
    """
    A 2D plot object.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

        self.plot = Plot(self.body)
        self.plot.pack(fill='both', expand=True)

        self.ax = self.plot.ax

        self.t_min = None
        self.t_max = None

        self.paths: list[LineView] = []


    def update_times(self, t_min, t_max):
        self.t_min = t_min
        self.t_max = t_max
        for path in self.paths:
            path.update(t_min, t_max)

        self.plot.set_legend_below()
        self.plot.refresh()

    def add_positions(self, *args, **kwargs) -> None:
        self.paths.append(LineView(self.ax, *args, **kwargs))
        self.t_min = self.paths[-1].times[0]
        self.t_max = self.paths[-1].times[-1]

        self.update_times(self.t_min, self.t_max)

        self.plot.set_legend_below()
        self.plot.refresh()

    def clear(self) -> None:
        for path in self.paths:
            path.clear()
        self.paths = []
        self.plot.ax.redraw_in_frame()
        self.t_min = None
        self.t_max = None
        self.plot.set_legend_below()  # drops the now-empty legend
        self.plot.refresh()
