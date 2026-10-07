import tkinter as tk
import ttkbootstrap as ttk

class DefaultManualEntry(ttk.Frame):
    """
    Allows selection between labeled defaults or manual entry
    """
    CUSTOM = "custom"

    def __init__(self, parent, defaults: dict[str, float], labels: list[str]|None = None, *args, **kwargs):
        self.selection = kwargs.pop("selection_var", ttk.StringVar(value=str(list(defaults.values())[0])))
        self.entry_text = kwargs.pop("entry_var",ttk.DoubleVar())
        super().__init__(parent, *args, **kwargs)

        self.defaults = defaults
        self.radiobuttons:dict[str,ttk.Radiobutton] = {}
        if labels == None or len(labels) != len(defaults.keys()):
            labels = [key.capitalize() for key in defaults.keys()]
        for idx, key in enumerate(self.defaults.keys()):
            self.radiobuttons[key] = ttk.Radiobutton(self, text=labels[idx], variable=self.selection, value=key,
                                                     command=self._on_mode_change)
            self.radiobuttons[key].grid(row=0, column=idx, padx=(5, 0))

        self.custom_col = ttk.Frame(self)
        self.custom_col.grid(row=0, sticky="ew", column=len(self.defaults), padx=(5, 0))
        self.columnconfigure(len(self.defaults), weight=1)

        self.custom_radiobuttons = ttk.Radiobutton(self.custom_col, text="Custom:", variable=self.selection,
                                                   value=self.CUSTOM,
                                                   command=self._on_mode_change)
        self.custom_radiobuttons.pack(side="left")
        self.entry = ttk.Entry(self.custom_col, textvariable=self.entry_text, state="disabled")
        self.entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        self.entry.bind("<Button-1>", self._on_entry_click)
        self.entry_text.trace_add("write", lambda *_: self._validate())

        self._on_mode_change()

    def _on_mode_change(self) -> None:
        """
        Disables entry box if not using custom input.
        """
        if self.selection.get() == self.CUSTOM:
            self.entry.configure(state="normal")
            self.entry.focus_set()
            self.entry.selection_range(0, "end")
            self._validate()
        else:
            self.entry.configure(state="disabled", bootstyle="default")

    def _on_entry_click(self, _event) -> None:
        """
        Convenience function to select custom if entry box is clicked
        :param _event: Unused
        """
        if self.selection.get() != self.CUSTOM:
            self.selection.set(self.CUSTOM)
            self._on_mode_change()

    def _validate(self) -> None:
        """
        Indicates invalid input.
        """
        if self.selection.get() == self.CUSTOM:
            valid = True
            try:
                float(self.entry_text.get())
            except (ValueError, TypeError, tk.TclError):
                valid = False
            self.entry.configure(bootstyle="default" if valid else "danger")

    def get(self) -> dict:
        """
        Gets the selected value.
        :return: UI selection and the effective value
        """
        return {"selection": self.selection.get(), 
                "effective_value": self.defaults[self.selection.get()] if 
                self.selection != self.CUSTOM else float(self.entry_text.get())}

    def set(self, value, key=None) -> None:
        """
        Sets the selected value.
        :param value: Key to select
        :param key: Key to replace value with value
        """
        if value in self.defaults.keys():
            self.selection.set(value)
        else:
            self.selection.set(self.CUSTOM)
            self.entry_text.set(str(value))
        self._on_mode_change()
