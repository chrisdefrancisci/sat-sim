import ttkbootstrap as ttk


class DefaultOrManual(ttk.Frame):
    """A labeled parameter input: pick the default, or enter a custom value."""

    DEFAULT = "default"
    CUSTOM = "custom"

    def __init__(self, master, label, default, cast=str, command=None, **kwargs):
        """
        label    -- text shown to the left of the radiobuttons
        default  -- the default value
        cast     -- callable converting entry text to a value (int, float, str...)
        command  -- optional callback, called with no args whenever the choice changes
        """
        super().__init__(master, **kwargs)
        self.default = default
        self.cast = cast
        self.command = command

        self.mode = ttk.StringVar(value=self.DEFAULT)
        self.text = ttk.StringVar(value=str(default))

        ttk.Label(self, text=label).grid(row=0, column=0, rowspan=2,
                                         sticky="nw", padx=(0, 15))

        self.default_rb = ttk.Radiobutton(
            self, text=f"Default ({default})", variable=self.mode,
            value=self.DEFAULT, command=self._on_mode_change)
        self.default_rb.grid(row=0, column=1, sticky="w")

        custom_row = ttk.Frame(self)
        custom_row.grid(row=1, column=1, sticky="w", pady=(4, 0))

        self.custom_rb = ttk.Radiobutton(
            custom_row, text="Custom:", variable=self.mode,
            value=self.CUSTOM, command=self._on_mode_change)
        self.custom_rb.pack(side="left")

        self.entry = ttk.Entry(custom_row, textvariable=self.text,
                               width=10, state="disabled")
        self.entry.pack(side="left", padx=(5, 0))

        # Clicking the entry while disabled-by-default switches to custom mode
        self.entry.bind("<Button-1>", self._on_entry_click)
        self.text.trace_add("write", lambda *_: self._validate())

    # ---- internal ----
    def _on_mode_change(self):
        if self.mode.get() == self.DEFAULT:
            self.text.set(str(self.default))
            self.entry.configure(state="disabled", bootstyle="default")
        else:
            self.entry.configure(state="normal")
            self.entry.focus_set()
            self.entry.select_range(0, "end")
            self._validate()
        if self.command:
            self.command()

    def _on_entry_click(self, _event):
        if self.mode.get() == self.DEFAULT:
            self.mode.set(self.CUSTOM)
            self._on_mode_change()

    def _validate(self):
        if self.mode.get() == self.CUSTOM:
            self.entry.configure(bootstyle="default" if self.is_valid() else "danger")

    # ---- public API ----
    def is_default(self):
        return self.mode.get() == self.DEFAULT

    def is_valid(self):
        if self.is_default():
            return True
        try:
            self.cast(self.text.get())
            return True
        except (ValueError, TypeError):
            return False

    def get(self):
        """Return None if default is selected, otherwise the cast custom value."""
        if self.is_default():
            return None
        return self.cast(self.text.get())  # raises ValueError if invalid

    def resolved(self):
        """Return the effective value: the default, or the cast custom value."""
        value = self.get()
        return self.default if value is None else value

    def set(self, value):
        """Set programmatically. None selects the default."""
        if value is None:
            self.mode.set(self.DEFAULT)
        else:
            self.mode.set(self.CUSTOM)
            self.text.set(str(value))
        self._on_mode_change()


if __name__ == "__main__":
    root = ttk.Window(themename="flatly", title="Settings")

    form = ttk.Frame(root, padding=20)
    form.pack(fill="both", expand=True)

    timeout = DefaultOrManual(form, "Timeout (s):", 30, cast=float)
    retries = DefaultOrManual(form, "Retries:", 3, cast=int)
    timeout.pack(anchor="w", pady=8)
    retries.pack(anchor="w", pady=8)


    def show():
        if not (timeout.is_valid() and retries.is_valid()):
            print("Fix invalid fields first")
            return
        print("timeout:", timeout.get(), "->", timeout.resolved())
        print("retries:", retries.get(), "->", retries.resolved())


    ttk.Button(form, text="Apply", command=show).pack(anchor="e", pady=(10, 0))

    root.mainloop()
