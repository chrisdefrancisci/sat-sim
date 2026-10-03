"""
Contains classes for automated label / entry controls
"""

import tkinter as tk
import ttkbootstrap as ttk

from SatSim.controller.label_entry import LabelEntryRow


class OrbitEntry(LabelEntryRow):
    """
    Helper class derived from LabelEntryRow for entering orbit parameters with tooltip descriptions.
    """

    def __init__(self, parent, entry_width=15, padding=5, **kwargs):
        """
        Docstring for __init__
        
        Must be kept in sync with SatSim.model.orbit_model.OrbitModel

        :param self: Description
        :param parent: Description
        :param entry_width: Description
        :param padding: Description
        :param kwargs: Description
        """
        super().__init__(parent, 
                         fields=['altitude_km', 'inclination_deg', 'eccentricity'],
                         labels=['Altitude (km)', 'Inclination (deg)', 'Eccentricity'],
                         tooltips=['Very low Earth orbit < 450 km\n' +
                                   'Low Earth orbit < 2,000 km\n' +
                                   'Medium Earth orbit < 35,786 km\n' + 
                                   'Geosynchronous orbit = 35,786 km\n' + 
                                   'High Earth orbit >35,786 km', 
                                   None, None],
                         **kwargs)

