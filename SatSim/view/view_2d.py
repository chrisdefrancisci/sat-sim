from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from SatSim.view.plot import Plot, PlotSubplots


class LineView:
    def __init__(self, ax: Axes, times: np.ndarray, pos: np.ndarray, *args, **kwargs):
        self.ax = ax
        self.times = times
        self.pos = pos

        self.args = args
        self.kwargs = kwargs

        colors = ttk.Style().colors

        self.full_path: list[Line2D] = self.ax.plot(self.pos[0, :], self.pos[1, :],
                                                    color=colors.border, linewidth=0.7, alpha=0.8,
                                                    label="Full simulated path")
        self.timed_path: list[Line2D] = self.ax.plot(self.pos[0, :], self.pos[1, :],
                                                     linewidth=3.0, *args, **kwargs)
        self.marker: PathCollection | None = self.ax.scatter(*pos[:, -1], *args, **kwargs)

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

        self.plot.set_legend_below(bottom=0.2)
        self.plot.refresh()

    def add_positions(self, *args, **kwargs) -> None:
        self.paths.append(LineView(self.ax, *args, **kwargs))
        self.t_min = self.paths[-1].times[0]
        self.t_max = self.paths[-1].times[-1]

        self.update_times(self.t_min, self.t_max)

        self.plot.set_legend_below(bottom=0.2)
        self.plot.refresh()

    def clear(self) -> None:
        for path in self.paths:
            path.clear()
        self.paths = []
        self.plot.ax.redraw_in_frame()
        self.t_min = None
        self.t_max = None
        self.plot.set_legend_below(bottom=0.2)  # drops the now-empty legend
        self.plot.refresh()


class ViewRpy(ttk.Frame):
    """
    A plot object to hold roll, pitch and yaw displays.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

        self.plot = PlotSubplots(self.body, nrows=3, ncols=1)
        self.plot.pack(fill='both', expand=True)

        self.ax_roll: Axes = self.plot.axs[0]
        self.ax_pitch: Axes = self.plot.axs[1]
        self.ax_yaw: Axes = self.plot.axs[2]

        self.t_min = None
        self.t_max = None

        self.paths_roll: list[LineView] = []
        self.paths_pitch: list[LineView] = []
        self.paths_yaw: list[LineView] = []

        self.ax_roll.set_ylabel("Roll")
        self.ax_pitch.set_ylabel("Pitch")
        self.ax_yaw.set_ylabel("Yaw")

    def update_times(self, t_min, t_max):
        self.t_min = t_min
        self.t_max = t_max
        for path in self.paths_roll + self.paths_pitch + self.paths_yaw:
            path.update(t_min, t_max)

        self.plot.set_legend_below(bottom=0.2)
        self.plot.refresh()

    def _add(self, ax: Axes, t: np.ndarray, x: np.ndarray, *args, **kwargs) -> None:
        data = np.vstack([t, x])
        if ax == self.ax_roll:
            paths = self.paths_roll
        elif ax == self.ax_pitch:
            paths = self.paths_pitch
        elif ax == self.ax_yaw:
            paths = self.paths_yaw
        else:
            raise NotImplementedError
        paths.append(LineView(ax, t, data, *args, **kwargs))
        self.t_min = paths[-1].times[0]
        self.t_max = paths[-1].times[-1]

        self.update_times(self.t_min, self.t_max)

        self.plot.set_legend_below(bottom=0.2)
        self.plot.refresh()

    def add_roll(self, t: np.ndarray, x: np.ndarray, *args, **kwargs) -> None:
        self._add(self.ax_roll, t, x, *args, **kwargs)

    def add_pitch(self, t: np.ndarray, x: np.ndarray, *args, **kwargs) -> None:
        self._add(self.ax_pitch, t, x, *args, **kwargs)

    def add_yaw(self, t: np.ndarray, x: np.ndarray, *args, **kwargs) -> None:
        self._add(self.ax_yaw, t, x, *args, **kwargs)

    def add_rpy(self, t: np.ndarray, rpy: np.ndarray, *args, **kwargs) -> None:
        self.add_roll(t, rpy[0, :], *args, **kwargs)
        self.add_pitch(t, rpy[1, :], *args, **kwargs)
        self.add_yaw(t, rpy[2, :], *args, **kwargs)

    def clear(self) -> None:
        for path in self.paths_roll + self.paths_pitch + self.paths_yaw:
            path.clear()
        self.paths_roll = []
        self.paths_pitch = []
        self.paths_yaw = []
        for ax in [self.ax_roll, self.ax_pitch, self.ax_yaw]:
            ax.redraw_in_frame()
        self.t_min = None
        self.t_max = None
        self.plot.set_legend_below(bottom=0.2)  # drops the now-empty legend
        self.plot.refresh()
