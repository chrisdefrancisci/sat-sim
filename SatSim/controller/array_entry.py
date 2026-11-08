import numpy as np
import tkinter as tk
import ttkbootstrap as ttk
from typing import Sequence

from SatSim.common.quaternion import Quaternion
from SatSim.model.array_vars import ArrayVars, QuaternionVars


class VectorEntry(ttk.Frame):
    """Frame with N labeled ttk.Entry widgets bound to a VectorVars."""

    def __init__(self, parent, array_vars: ArrayVars|None = None,
                 shape: tuple[int,int]|None = None, labels: Sequence[str] | None = None,
                 width: int = 8, **kwargs):
        super().__init__(parent, **kwargs)

        if array_vars is None:
            if shape is None:
                raise ValueError("Provide either array_vars or n")
            array_vars = ArrayVars(shape)
        else:
            shape = (array_vars.rows, array_vars.cols)
        self.array_vars = array_vars

        n = len(self.array_vars)
        if labels is None:
            labels = [f"v{i + 1}" for i in range(n)]
        if len(labels) != n:
            raise ValueError(f"Expected {n} labels, got {len(labels)}")

        self.entries = []
        cols = shape[1]
        for row in range(0, shape[0]):
            for col in range(0, shape[1]):
                idx = row * cols + col
                entry_frame = ttk.Frame(self)
                entry_frame.grid(row=row, column=col, stick="nsew")
                lbl = ttk.Label(entry_frame, text=labels[idx])
                lbl.pack(side=tk.RIGHT, fill=None, expand=False, padx=(0,5), anchor="w")
                ent = ttk.Entry(entry_frame, textvariable=self.array_vars[idx], width=width)
                ent.pack(side=tk.RIGHT, fill=None, expand=False, anchor="e")

                self.entries.append(ent)

    def get(self) -> np.ndarray:
        return self.array_vars.get()

    def set(self, values) -> None:
        self.array_vars.set(values)


class QuaternionEntry(VectorEntry):
    def __init__(self, parent, quat_vars: QuaternionVars|None = None,
                 width=8, **kwargs):
        if quat_vars is None:
            quat_vars = QuaternionVars()
        super().__init__(parent, array_vars=quat_vars,
                         labels=QuaternionVars.LABELS,
                         width=width, **kwargs)

    def get_quaternion(self) -> Quaternion:
        return self.array_vars.to_quaternion()

    def set_quaternion(self, q: "Quaternion") -> None:
        self.array_vars.set(np.asarray(q))