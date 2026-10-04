"""
Classes to use ttkbootstrap themes with plots
"""
import tkinter as tk
import ttkbootstrap as ttk
from mpl_toolkits.mplot3d import Axes3D
from ttkbootstrap.constants import *
import matplotlib

matplotlib.use("TkAgg")
matplotlib.rcParams['axes3d.mouserotationstyle'] = 'azel'
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np


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
    def __init__(self, master, **kwargs):
        projection = kwargs.pop("projection", None)
        super().__init__(master, **kwargs)
        self.style = ttk.Style()

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111, projection=projection)
        if isinstance(self.ax, Axes3D):
            self.ax.xaxis.pane.fill = False
            self.ax.yaxis.pane.fill = False
            self.ax.zaxis.pane.fill = False

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)

        # pack_toolbar=False lets us control packing order
        self.toolbar = ThemedToolbar(self.canvas, self, pack_toolbar=False)
        self.toolbar.pack(side=BOTTOM, fill=X)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=YES)

        self.apply_theme()

    def apply_theme(self):
        c = self.style.colors

        # Plot
        self.figure.set_facecolor(c.bg)
        if isinstance(self.ax, Axes3D):
            self.ax.set_facecolor(c.bg)
        else:
            self.ax.set_facecolor(c.inputbg)
        for item in (self.ax.xaxis.label, self.ax.yaxis.label, self.ax.title):
            item.set_color(c.fg)
        self.ax.tick_params(colors=c.fg)
        for spine in self.ax.spines.values():
            spine.set_color(c.border)
        self.ax.grid(True, color=c.border, alpha=0.5)

        legend = self.ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor(c.bg)
            legend.get_frame().set_edgecolor(c.border)
            for text in legend.get_texts():
                text.set_color(c.fg)

        # Toolbar
        self.toolbar.apply_theme(c)

        self.canvas.draw_idle()

    def refresh(self):
        self.canvas.draw_idle()
