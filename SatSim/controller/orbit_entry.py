"""
Contains classes for automated label / entry controls
"""

from enum import Enum
import tkinter as tk
import ttkbootstrap as ttk

from SatSim.controller.label_entry import LabelEntryRow
from SatSim.controller.settings import OrbitModel


class OrbitEntry(ttk.Frame):
    """
    Helper class derived from LabelEntryRow for entering orbit parameters with tooltip descriptions.
    """

    class Display(Enum):
        NOMINAL = 1
        CIRCULAR_EQ = 2
        CIRCULAR_INC = 3
        ELLIPTIC_EQ = 4

    def __init__(self, parent, model: OrbitModel, *args, **kwargs):
        """
        Docstring for __init__
        
        Must be kept in sync with SatSim.model.orbit_model.OrbitModel

        :param self: Description
        :param parent: Description
        :param entry_width: Description
        :param padding: Description
        :param kwargs: Description
        """
        padding = kwargs.pop("padding", 5)
        super().__init__(parent, *args, **kwargs)
        self.padding = padding
        self.model = model
        entry_width = 10

        self.alt_label = ttk.Label(self, text="Altitude (km)")
        self.alt_label.grid(row=0, column=0, padx=(padding,2), pady=padding, sticky="e")
        self.alt_entry = ttk.Entry(self, textvariable=model.altitude_km, width=entry_width)
        self.alt_entry.grid(row=0, column=1, padx=(0, padding), pady=padding, sticky="w")
        ttk.ToolTip(self.alt_entry, bootstyle="info", 
                    text='Very low Earth orbit < 450 km\n' +
                         'Low Earth orbit < 2,000 km\n' +
                         'Medium Earth orbit < 35,786 km\n' +
                         'Geosynchronous orbit = 35,786 km\n' +
                         'High Earth orbit >35,786 km')

        self.inc_label = ttk.Label(self, text="Inclination (deg)")
        self.inc_label.grid(row=0, column=2, padx=(padding,2), pady=padding, sticky="e")
        self.inc_entry = ttk.Entry(self, textvariable=model.inclination_deg, width=entry_width)
        self.inc_entry.grid(row=0, column=3, padx=(0, padding), pady=padding, sticky="w")
        
        self.ecc_label = ttk.Label(self, text="Eccentricity")
        self.ecc_label.grid(row=0, column=4, padx=(padding,2), pady=padding, sticky="e")
        self.ecc_entry = ttk.Entry(self, textvariable=model.eccentricity, width=entry_width)
        self.ecc_entry.grid(row=0, column=5, padx=(0, padding), pady=padding, sticky="w")
        
        self.anom_label = ttk.Label(self, text="True Anomaly (deg)")
        self.anom_label.grid(row=1, column=0, padx=(padding,2), pady=padding, sticky="e")
        self.anom_entry = ttk.Entry(self, textvariable=model.true_anomaly, width=entry_width)
        self.anom_entry.grid(row=1, column=1, padx=(0, padding), pady=padding, sticky="w")

        self.node_label = ttk.Label(self, text="RAAN (deg)")
        self.node_label.grid(row=1, column=2, padx=(padding,2), pady=padding, sticky="e")
        ttk.ToolTip(self.node_label, bootstyle="info", text="Right Ascension of the Ascending Node")
        self.node_entry = ttk.Entry(self, textvariable=model.node, width=entry_width)
        self.node_entry.grid(row=1, column=3, padx=(0, padding), pady=padding, sticky="w")

        self.argp_label = ttk.Label(self, text="Argument of Perigee (deg)")
        self.argp_label.grid(row=1, column=4, padx=(padding,2), pady=padding, sticky="e")
        self.argp_entry = ttk.Entry(self, textvariable=model.arg_perigee, width=entry_width)
        self.argp_entry.grid(row=1, column=5, padx=(0, padding), pady=padding, sticky="w")

        self.display_type = self.Display.NOMINAL

        # Special cases for circular orbits and elliptical equatorial orbits
        self.true_long_label = ttk.Label(self, text="True Longitude (deg)")
        self.true_long_entry = ttk.Entry(self, textvariable=model.true_longitude, width=entry_width)
        self.arg_lat_label = ttk.Label(self, text="Argument of Latitude (deg)")
        self.arg_lat_entry = ttk.Entry(self, textvariable=model.arg_latitude, width=entry_width)
        self.long_peri_label = ttk.Label(self, text="Longitude of Periapsis (deg)")
        self.long_peri_entry = ttk.Entry(self, textvariable=model.long_periapsis, width=entry_width)

        model.inclination_deg.trace_add("write", self.check_special_orbits)
        model.eccentricity.trace_add("write", self.check_special_orbits)
        self.check_special_orbits()

    def check_special_orbits(self, *args):
        try:
            if self.model.eccentricity.get() == 0.0 and self.model.inclination_deg.get() == 0.0:
                new_display = self.Display.CIRCULAR_EQ
            elif self.model.eccentricity.get() == 0.0:
                new_display = self.Display.CIRCULAR_INC
            elif self.model.inclination_deg.get() == 0.0:
                new_display = self.Display.ELLIPTIC_EQ
            else:
                new_display = self.Display.NOMINAL
            self.change_display(new_display)
        except tk.TclError:
            pass

    def change_display(self, new_display):
        if new_display == self.display_type:
            return

        self.hide_display()
        if new_display == self.Display.NOMINAL:
            self.show_nominal()
        elif new_display == self.Display.CIRCULAR_EQ:
            self.show_circular_eq()
        elif new_display == self.Display.CIRCULAR_INC:
            self.show_circular_inc()
        elif new_display == self.Display.ELLIPTIC_EQ:
            self.show_elliptic_eq()
        self.display_type = new_display

    def show_nominal(self):
        padding = self.padding
        self.anom_label.grid(row=1, column=0, padx=(padding,2), pady=padding, sticky="e")
        self.anom_entry.grid(row=1, column=1, padx=(0, padding), pady=padding, sticky="w")
        self.node_label.grid(row=1, column=2, padx=(padding,2), pady=padding, sticky="e")
        self.node_entry.grid(row=1, column=3, padx=(0, padding), pady=padding, sticky="w")
        self.argp_label.grid(row=1, column=4, padx=(padding,2), pady=padding, sticky="e")
        self.argp_entry.grid(row=1, column=5, padx=(0, padding), pady=padding, sticky="w")

    def show_circular_eq(self):
        padding = self.padding
        self.true_long_label.grid(row=1, column=0, padx=(padding,2), pady=padding, sticky="e")
        self.true_long_entry.grid(row=1, column=1, padx=(0, padding), pady=padding, sticky="w")

    def show_circular_inc(self):
        padding = self.padding
        self.arg_lat_label.grid(row=1, column=0, padx=(padding,2), pady=padding, sticky="e")
        self.arg_lat_entry.grid(row=1, column=1, padx=(0, padding), pady=padding, sticky="w")

    def show_elliptic_eq(self):
        padding = self.padding
        self.anom_label.grid(row=1, column=0, padx=(padding,2), pady=padding, sticky="e")
        self.anom_entry.grid(row=1, column=1, padx=(0, padding), pady=padding, sticky="w")
        self.long_peri_label.grid(row=1, column=2, padx=(padding,2), pady=padding, sticky="e")
        self.long_peri_entry.grid(row=1, column=3, padx=(0, padding), pady=padding, sticky="w")

    def hide_display(self):
        if self.display_type == self.Display.NOMINAL:
            self.hide_nominal()
        elif self.display_type == self.Display.CIRCULAR_EQ:
            self.hide_circular_eq()
        elif self.display_type == self.Display.CIRCULAR_INC:
            self.hide_circular_inc()
        elif self.display_type == self.Display.ELLIPTIC_EQ:
            self.hide_elliptic_eq()
    
    def hide_nominal(self):
        self.anom_label.grid_forget()
        self.anom_entry.grid_forget()
        self.node_label.grid_forget()
        self.node_entry.grid_forget()
        self.argp_label.grid_forget()
        self.argp_entry.grid_forget()

    def hide_circular_eq(self):
        self.true_long_label.grid_forget()
        self.true_long_entry.grid_forget()

    def hide_circular_inc(self):
        self.arg_lat_label.grid_forget()
        self.arg_lat_entry.grid_forget()

    def hide_elliptic_eq(self):
        self.anom_label.grid_forget()
        self.anom_entry.grid_forget()
        self.long_peri_label.grid_forget()
        self.long_peri_entry.grid_forget()