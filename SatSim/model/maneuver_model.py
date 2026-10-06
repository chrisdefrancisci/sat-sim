import numpy as np
import ttkbootstrap as ttk

from SatSim.constants import earth
from SatSim.model.orbit_model import OrbitModel


class OrbitManeuverModel:
    r"""
    Class to model changes to a satellite's orbit.
    """
    def __init__(self, target_model:OrbitModel, chaser_model:OrbitModel):
        self.target_orbit = target_model
        self.chaser_orbit = chaser_model


class HohmannTransferModel(OrbitManeuverModel):
    r"""
    Class to model a Hohmann Transfer.

    Assumes circular and coplanar start and end orbits, with apogee kick exactly at $\nu = 180^\circ$
    """
    def __init__(self, target_model:OrbitModel, chaser_model:OrbitModel, **kwargs):
        super().__init__(target_model, chaser_model)
        self.selection = ttk.StringVar(value=kwargs.pop("selection", "custom"))
        self.r_final = ttk.DoubleVar(value=kwargs.pop("Manual", target_model.get_radius()))

    def get(self) -> dict:
        d = {"Selection": self.selection.get(), "r_final": self.r_final.get()}
        if self.selection.get().lower == "target radius":
            d["r_final"] = self.target_orbit.get_radius()
        return d


    def get_delta_t(self) -> float:
        return np.pi * np.sqrt((self.chaser_orbit.get_radius() + self.r_final.get())**3 / earth.mu) / 2

    def get_delta_v1(self) -> float:
        r1 = self.chaser_orbit.get_radius()
        r2 = self.r_final.get()
        return np.sqrt(earth.mu / r1) * (np.sqrt(2 * r2 / (r1 + r2)) - 1)
    
    def get_delta_v2(self) -> float:
        r1 = self.chaser_orbit.get_radius()
        r2 = self.r_final.get()
        return np.sqrt(earth.mu / r2) * (1 - np.sqrt(2 * r1 / (r1 + r2)))

    def get_delta_v_total(self) -> float:
        return self.get_delta_v1() + self.get_delta_v2()

class BiellipticTransferModel(OrbitManeuverModel):
    r"""
    Class to model a Bi-elliptic Transfer.

    Assumes circular and coplanar start and end orbits, with apogee kick exactly at $\nu = 180^\circ$
    """
    def __init__(self, target_model:OrbitModel, chaser_model:OrbitModel, **kwargs):
        super().__init__(target_model, chaser_model)

def CreateManeuverModel(settings: dict) -> OrbitManeuverModel:
    if "type" not in settings:
        raise ValueError("settings does not contain key\"type\"")

    if settings["type"].lower() == "hohmann":
        return HohmannTransferModel(**settings["params"])
    elif settings["type"].lower() == "bielliptic":
        return BiellipticTransferModel(**settings["params"])
    else:
        raise ValueError(f"Maneuver Type {settings["type"]} is not supported.")