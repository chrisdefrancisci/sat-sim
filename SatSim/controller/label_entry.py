"""
Contains classes for automated label / entry controls
"""

import tkinter as tk
from tkinter import ttk


class LabelEntryRow(ttk.Frame):
    """
    A horizontal row of label-entry pairs.

    Example:
        row = LabelEntryRow(parent, fields=["First Name", "Last Name", "Age"])
        row.pack(fill="x", padx=10, pady=10)
        print(row.get_values())
    """

    def __init__(self, parent, fields, entry_width=15, padding=5, **kwargs):
        super().__init__(parent, **kwargs)

        self.fields = fields
        self.entries = {}  # field name -> ttk.Entry widget

        for i, field_name in enumerate(fields):
            label = ttk.Label(self, text=field_name)
            label.grid(row=0, column=2 * i, padx=(padding, 2), pady=padding, sticky="e")

            entry = ttk.Entry(self, width=entry_width)
            entry.grid(row=0, column=2 * i + 1, padx=(0, padding), pady=padding, sticky="w")

            self.entries[field_name] = entry

    def get_values(self):
        """Return a dict of {field_name: entry_text}."""
        # TODO also consider using tk.DoubleVar() with the entry box
        return {name: float(entry.get()) for name, entry in self.entries.items()}

    def set_values(self, values: dict):
        """Set entry values from a dict of {field_name: value}."""
        for name, value in values.items():
            if name in self.entries:
                self.entries[name].delete(0, tk.END)
                self.entries[name].insert(0, str(value))

    def clear(self):
        """Clear all entries in the row."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def get_entry(self, field_name):
        """Access a specific entry widget directly."""
        return self.entries.get(field_name)
