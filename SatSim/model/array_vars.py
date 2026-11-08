import copy
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk
from typing import Iterable

from SatSim.common.quaternion import Quaternion


class ArrayVars:
    """Copyable container of N tk.DoubleVar's."""

    def __init__(self, shape: tuple[int, int] | None = None,
                 values: Iterable[np.floating]|None = None):
        if values is None:
            if shape is None:
                raise ValueError("Provide either shape or values")
            rows = shape[0]
            cols = shape[1]
            values = np.zeros((rows, cols))
        elif isinstance(values, np.ndarray):
            rows, cols = np.shape(values)
        else:
            rows = len(np.asarray(values))
            cols = 1

        values = np.asarray(values, dtype=float).reshape(-1)
        n = rows * cols
        if shape is not None and values.size != n:
            raise ValueError(f"Expected {n} values, got {values.size}")

        self.vars = [tk.DoubleVar(value=float(v)) for v in values]
        self.rows:int = rows
        self.cols:int = cols

    def __len__(self) -> int:
        return len(self.vars)

    def __getitem__(self, key) -> tk.DoubleVar:
        if isinstance(key, tuple) and len(key) == 2:
            row, col = key
            return self.vars[row * self.cols + col]
        elif isinstance(key, int):
            return self.vars[key]
        raise TypeError("Invalid index type. Use vars[row, col] or vars[index]")

    def __iter__(self):
        return iter(self.vars)

    def get(self) -> np.ndarray:
        """Return the values as a (N,M) array. Raises ValueError on bad input."""
        try:
            return np.array([v.get() for v in self.vars], dtype=float).reshape((self.rows, self.cols))
        except tk.TclError as e:
            raise ValueError("All entries must be valid numbers") from e

    def set(self, values) -> None:
        values = np.asarray(values, dtype=float).reshape((self.rows, self.cols))
        if values.size != len(self):
            raise ValueError(f"Expected {len(self)} values, got {values.size}")
        for var, val in zip(self.vars, values):
            var.set(float(val))

    def __copy__(self):
        result = self.__class__.__new__(self.__class__)
        result.__dict__.update(self.__dict__)
        result.vars = [tk.DoubleVar(value=v) for v in self.get()]
        result.rows = self.rows
        result.cols = self.cols
        return result

    def __deepcopy__(self, memo):
        if id(self) in memo:
            return memo[id(self)]
        return self.__copy__()


class QuaternionVars(ArrayVars):
    LABELS = ("q1", "q2", "q3", "q4")

    def __init__(self, values=(0.0, 0.0, 0.0, 1.0)):
        super().__init__(shape=(4,1), values=values)

    def to_quaternion(self) -> Quaternion:
        return Quaternion(self.get())

    @classmethod
    def from_quaternion(cls, q: Quaternion) -> 'QuaternionVars':
        return cls(values=np.asarray(q))