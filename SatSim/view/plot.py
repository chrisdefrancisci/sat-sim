"""
Classes to use ttkbootstrap themes with plots
"""
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk
from mpl_toolkits.mplot3d import Axes3D
from ttkbootstrap.constants import *
import matplotlib

matplotlib.use("TkAgg")
matplotlib.rcParams['axes3d.mouserotationstyle'] = 'azel'
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class ThemedToolbar(NavigationToolbar2Tk):
    def apply_theme(self, colors):
        bg, fg = colors.bg, colors.fg

        self.config(background=bg)

        for child in self.winfo_children():
            if isinstance(child, (tk.Button, tk.Checkbutton)):
                child.config(
                    background=bg,
                    foreground=fg,
                    activebackground=colors.active,
                    activeforeground=fg,
                    highlightbackground=bg,
                )
                if isinstance(child, tk.Checkbutton):
                    child.config(selectcolor=colors.selectbg)  # "pressed" look for pan/zoom

                # Re-generate the icon so it matches the new foreground color
                if getattr(child, "_image_file", None) is not None:
                    try:
                        NavigationToolbar2Tk._set_image_for_button(self, child)
                    except Exception:
                        pass  # older matplotlib versions

            elif isinstance(child, tk.Label):  # coordinate readout
                child.config(background=bg, foreground=fg)

            elif isinstance(child, tk.Frame):  # separators
                child.config(background=colors.border)


class Plot(ttk.Frame):
    """
    Themed matplotlib frame. Works for a single axes or a grid of subplots.

        Plot(parent)                         -> one axes, use self.ax
        Plot(parent, projection="3d")        -> one 3D axes
        Plot(parent, nrows=2, ncols=2)       -> grid, use self.axs (2D array)
    """

    def __init__(self, parent, nrows=1, ncols=1, projection=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.style = ttk.Style()

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.axs = self.figure.subplots(
            nrows=nrows, ncols=ncols,
            sharex=nrows > 1, sharey=ncols > 1,
            squeeze=False,                       # always a 2D array
            subplot_kw={"projection": projection},
        )
        self.ax = self.axs[0, 0]                 # convenience for the single-axes case
        self._legend_bottom = None

        for ax in self.axs.flat:
            if isinstance(ax, Axes3D):
                ax.xaxis.pane.fill = False
                ax.yaxis.pane.fill = False
                ax.zaxis.pane.fill = False

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self._legend_map = {}
        self.canvas.mpl_connect("pick_event", self._on_legend_pick)

        self.toolbar = ThemedToolbar(self.canvas, self, pack_toolbar=False)
        self.toolbar.pack(side=BOTTOM, fill=X)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=YES)

        self.apply_theme()

    # ---- legends -------------------------------------------------------

    def _style_legends(self):
        c = self.style.colors
        legends = [*self.figure.legends]
        legends += [ax.get_legend() for ax in self.axs.flat]
        for legend in filter(None, legends):
            frame = legend.get_frame()
            frame.set_facecolor(c.bg)
            frame.set_edgecolor(c.border)
            for text in legend.get_texts():
                text.set_color(c.fg)

    def set_legend_below(self, bottom=0.1):
        """
        Single-row legend beneath the figure, built from all axes' labeled
        artists. Duplicate labels are collapsed; clicking an entry toggles
        every artist that shares that label.
        """
        entries = {}  # label -> [artists]
        for ax in self.axs.flat:
            for handle, label in zip(*ax.get_legend_handles_labels()):
                if label and not label.startswith("_"):
                    entries.setdefault(label, []).append(handle)

        for legend in list(self.figure.legends):
            legend.remove()
        for ax in self.axs.flat:
            if ax.get_legend():
                ax.get_legend().remove()

        self._legend_map = {}
        if entries:
            legend = self.figure.legend(
                [a[0] for a in entries.values()], list(entries.keys()),
                loc="lower center", ncol=len(entries), frameon=True,
            )
            self.figure.subplots_adjust(bottom=bottom)
            self._legend_bottom = bottom

            for handle, text, artists in zip(legend.legend_handles,
                                             legend.get_texts(),
                                             entries.values()):
                handle.set_picker(5)
                text.set_picker(True)
                self._legend_map[handle] = (artists, handle, text)
                self._legend_map[text] = (artists, handle, text)
        else:
            self._legend_bottom = None

        self._style_legends()

    def _on_legend_pick(self, event):
        item = self._legend_map.get(event.artist)
        if item is None:
            return
        artists, handle, text = item
        visible = not artists[0].get_visible()
        for a in artists:
            a.set_visible(visible)
        alpha = 1.0 if visible else 0.3
        handle.set_alpha(alpha)
        text.set_alpha(alpha)
        self.canvas.draw_idle()

    # ---- theming / refresh --------------------------------------------

    def apply_theme(self):
        c = self.style.colors
        self.figure.set_facecolor(c.bg)

        for ax in self.axs.flat:
            ax.set_facecolor(c.bg if isinstance(ax, Axes3D) else c.inputbg)
            for item in (ax.xaxis.label, ax.yaxis.label, ax.title):
                item.set_color(c.fg)
            ax.tick_params(colors=c.fg)
            for spine in ax.spines.values():
                spine.set_color(c.border)
            ax.grid(True, color=c.border, alpha=0.5)

        self._style_legends()
        self.toolbar.apply_theme(c)
        self.canvas.draw_idle()

    def refresh(self):
        if self.axs.size > 1:
            # Respect the room reserved for the legend, if there is one
            rect = (0, self._legend_bottom or 0, 1, 1)
            self.figure.tight_layout(rect=rect)
        self.canvas.draw_idle()
