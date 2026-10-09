"""
Contains classes for automated label / entry controls
"""

import tkinter as tk
import ttkbootstrap as ttk

from SatSim.controller.label_entry import LabelEntryRow
from SatSim.model.maneuver_model import OrbitElements


class OrbitEntry(ttk.Frame):
    """
    Helper class derived from LabelEntryRow for entering orbit parameters with tooltip descriptions.
    """

    def __init__(self, parent, model: OrbitElements, *args, **kwargs):
        """
        Docstring for __init__
        
        Must be kept in sync with SatSim.model.orbit_model.OrbitModel

        :param self: Description
        :param parent: Description
        :param entry_width: Description
        :param padding: Description
        :param kwargs: Description
        """
        super().__init__(parent, *args, **kwargs)
        altitude = ttk.DoubleVar()  # TODO how to get altitude to propagate into semimajor?
        # TODO how to get label entry row to change as things are added?

        top_row = LabelEntryRow(self,
                                fields=['altitude_km', 'inclination_deg', 'eccentricity'],
                                labels=['Altitude (km)', 'Inclination (deg)', 'Eccentricity'],
                                tooltips=['Very low Earth orbit < 450 km\n' +
                                          'Low Earth orbit < 2,000 km\n' +
                                          'Medium Earth orbit < 35,786 km\n' +
                                          'Geosynchronous orbit = 35,786 km\n' +
                                          'High Earth orbit >35,786 km',
                                          None, None],
                                variables=[altitude, model.inclination, model.eccentricity])
        top_row.pack(side="top", fill="x", expand=True)
        bottom_row = LabelEntryRow(self,
                                   fields=['node', 'arg_perigee', 'true_anomaly'],
                                   labels=['Right Ascension of Ascending Node (deg)', 'Argument of Perigee (deg)',
                                           'True Anomaly'],
                                   variables=[altitude, model.inclination, model.eccentricity])
        bottom_row.pack(side="top", fill="x", expand=True)
