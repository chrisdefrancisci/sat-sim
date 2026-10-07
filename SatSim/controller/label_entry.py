"""
Contains classes for automated label / entry controls
"""

import tkinter as tk
import ttkbootstrap as ttk


class LabelEntryRow(ttk.Frame):
    """
    A horizontal row of label-entry pairs.

    Example:
        row = LabelEntryRow(parent, fields=["First Name", "Last Name", "Age"])
        row.pack(fill="x", padx=10, pady=10)
        print(row.get_values())
    """

    def __init__(self, parent, fields, labels=None, tooltips=None, variables=None, entry_width=15, padding=5, **kwargs):
        super().__init__(parent, **kwargs)

        if labels is None:
            labels = [None] * len(fields)
        if tooltips is None:
            tooltips = [None] * len(fields)
        if variables is None:
            variables = [None] * len(fields)
        
        self.entries = {}  # field name -> ttk.Entry widget

        for i, (field_name, label_text, tooltip_text, var) in enumerate(zip(fields, labels, tooltips, variables)):
            if label_text is None:
                label_text = field_name
            label = ttk.Label(self, text=label_text)
            label.grid(row=0, column=2 * i, padx=(padding, 2), pady=padding, sticky="e")

            if var is not None:
                entry = ttk.Entry(self, textvariable=var, width=entry_width)
            else:
                entry = ttk.Entry(self, width=entry_width)
            entry.grid(row=0, column=2 * i + 1, padx=(0, padding), pady=padding, sticky="w")
            if tooltip_text is not None:
                ttk.ToolTip(entry, text=tooltip_text, bootstyle="info")

            self.entries[field_name] = entry
