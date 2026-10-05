import ttkbootstrap as ttk


class DefaultManualEntry(ttk.Frame):
    """
    Allows selection between labeled defaults or manual entry
    """
    CUSTOM = "custom"

    def __init__(self, parent, label, defaults: dict[str, float], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.defaults = defaults

        self.selection = ttk.StringVar(value=str(list(self.defaults.values())[0]))
        self.entry_text = ttk.StringVar()

        self.radiobuttons = {}
        for idx, (key, value) in enumerate(self.defaults.items()):
            self.radiobuttons[key] = ttk.Radiobutton(self, text=key, variable=self.selection, value=key,
                                                     command=self._on_mode_change)
            self.radiobuttons[key].grid(row=0, column=idx, padx=(5, 0))

        self.custom_col = ttk.Frame(self)
        self.custom_col.grid(row=0, column=len(self.defaults), padx=(5, 0))

        self.custom_radiobuttons = ttk.Radiobutton(self.custom_col, text="Custom:", variable=self.selection,
                                                   value=self.CUSTOM,
                                                   command=self._on_mode_change)
        self.custom_radiobuttons.pack(side="left")
        self.entry = ttk.Entry(self.custom_col, textvariable=self.entry_text, state="disabled")
        self.entry.pack(side="left", padx=(5, 0))

        self.entry.bind("<Button-1>", self._on_entry_click)
        self.entry_text.trace_add("write", lambda *_: self._validate())

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
            except (ValueError, TypeError):
                valid = False
            self.entry.configure(bootstyle="normal" if valid else "danger")

    def get(self) -> float:
        """
        Gets the selected value.
        :return: Selected value
        """
        if self.selection.get() == self.CUSTOM:
            return float(self.entry_text.get())
        else:
            return self.defaults[self.selection.get()]

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
