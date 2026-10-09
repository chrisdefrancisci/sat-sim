import copy
import ttkbootstrap as ttk
import numpy as np

from SatSim.common import earth
from SatSim.model.maneuver_model import ImpulseConfig, OrbitConfig, SimConfig


class OrbitModel:
    r"""
    Hold the settings data for orbit parameters.
    """

    def __init__(self, **kwargs):
        self.altitude_km = ttk.DoubleVar(value=kwargs.pop("altitude_km", 450))
        self.inclination_deg = ttk.DoubleVar(value=kwargs.pop("inclination_deg", 30))
        self.eccentricity = ttk.DoubleVar(value=kwargs.pop("eccentricity", 0))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        result.altitude_km = ttk.DoubleVar(value=self.altitude_km.get())
        result.inclination_deg = ttk.DoubleVar(value=self.inclination_deg.get())
        result.eccentricity = ttk.DoubleVar(value=self.eccentricity.get())
        return result

    def to_config(self) -> OrbitConfig:
        return OrbitConfig(
            altitude_km=self.altitude_km.get(),
            inclination_deg=self.inclination_deg.get(),
            eccentricity=self.eccentricity.get()
        )


class HohmannModel:
    r"""
    Hold the settings data for a Hohmann Transfer.

    Assumes circular and coplanar start and end orbits, with apogee kick exactly at $\nu = 180^\circ$
    """

    def __init__(self, target_model: OrbitModel, chaser_model: OrbitModel, **kwargs):
        self.target_model = target_model
        self.chaser_model = chaser_model
        self.r_selection = ttk.StringVar(value=kwargs.pop("selection", "custom"))
        self.r_custom = ttk.DoubleVar(value=kwargs.pop("Manual", target_model.to_config().radius))
        self.t_selection = ttk.StringVar(value=kwargs.pop("selection", "custom"))
        self.t_custom = ttk.DoubleVar(value=kwargs.pop("Manual", 0.0))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        # If copied from the SettingsModel, we want to have new references to the existing target and chaser models
        if id(self.target_model) in memo:
            result.target_model = memo[id(self.target_model)]
        else:
            result.target_model = copy.deepcopy(self.target_model)
        if id(self.chaser_model) in memo:
            result.chaser_model = memo[id(self.chaser_model)]
        else:
            result.chaser_model = copy.deepcopy(self.chaser_model)

        result.r_selection = ttk.StringVar(value=self.r_selection.get())
        result.r_custom = ttk.DoubleVar(value=self.r_custom.get())
        result.t_selection = ttk.StringVar(value=self.t_selection.get())
        result.t_custom = ttk.DoubleVar(value=self.t_custom.get())

        return result

    @property
    def r_final(self) -> float:
        if self.r_selection.get().lower() == "custom":
            return self.r_custom.get()
        elif self.r_selection.get().lower() == "target":
            return self.target_model.to_config().radius
        else:
            raise ValueError(f"Unknown option for radius: {self.r_selection.get()}")

    @r_final.setter
    def r_final(self, r) -> None:
        matching_r_threshold = 0.001  # km = 1m
        if r - self.target_model.to_config().semimajor < matching_r_threshold and self.target_model.eccentricity == 0:
            self.r_selection.set("target".capitalize())
        else:
            self.r_selection.set("custom".capitalize())
            self.r_custom.set(r)

    @property
    def t_start(self) -> float:
        if self.t_selection.get().lower() == "custom":
            return self.t_custom.get()
        elif self.t_selection.get().lower() == "immediate":
            return 0
        elif self.t_selection.get().lower() == "rendezvous":
            # TODO: implement Vallado Algorithm 45: Circular Coplanar Phasing (Different Orbits) pg 367
            raise ValueError(f"{self.t_selection.get()} Not yet implemented")
        else:
            raise ValueError(f"Unknown option for time: {self.t_selection.get()}")

    @t_start.setter
    def t_start(self, t) -> None:
        if t == 0:
            self.t_selection.set("immediate".capitalize())
        else:
            self.t_selection.set("custom".capitalize())
            self.t_custom.set(t)

    @property
    def delta_t(self) -> float:
        return np.pi * np.sqrt((self.chaser_model.to_config().radius + self.r_final) ** 3 / (8 * earth.mu))

    @property
    def delta_v_1(self) -> float:
        r"""
        Gets the magnitude of the first impulsive burn. 
        The sign indicates if the burn is in the direction of velocity (positive) or opposite the direction of 
        velocity (negative).
        
        :param self: Description
        :return: Description
        :rtype: float
        """
        r1 = self.chaser_model.to_config().radius
        r2 = self.r_final
        return np.sqrt(earth.mu / r1) * (np.sqrt(2 * r2 / (r1 + r2)) - 1)

    @property
    def delta_v_2(self) -> float:
        r1 = self.chaser_model.to_config().radius
        r2 = self.r_final
        return np.sqrt(earth.mu / r2) * (1 - np.sqrt(2 * r1 / (r1 + r2)))

    @property
    def delta_v_total(self) -> float:
        return abs(self.delta_v_1) + abs(self.delta_v_2)

    def register_cb(self, cb) -> list[tuple]:
        """
        Register callback on variables that affect the generation of the final radius.
        
        :param cb: Callback
        :returns: (variable, trace_id) pairs. The caller can remove them on destruction.
        """
        watched = [
            # self.target_model, self.chaser_model, # TODO: need a trace add for OrbitModel
            self.r_selection, self.r_custom, self.t_selection, self.t_custom
        ]
        return [(v, v.trace_add("write", cb)) for v in watched]

    def to_config(self) -> list[ImpulseConfig]:
        return [
            ImpulseConfig(time=self.t_start, delta_v=self.delta_v_1),
            ImpulseConfig(time=self.t_start + self.delta_t, delta_v=self.delta_v_2)
        ]


class BiellipticModel:
    r"""
    Hold the settings data for a Bi-elliptic Transfer.

    Assumes circular and coplanar start and end orbits, with apogee kick exactly at $\nu = 180^\circ$

    Uses Vallado Algorith 37, pg 330.
    """

DEFAULT_INT_RATIO = 40
    r"""
    Ratio between intermediate orbit and initial orbit, ..math:`R^* = r_{int} / r_{initial}`.
    """    def __init__(self, target_model: OrbitModel, chaser_model: OrbitModel, **kwargs):
        self.target_model = target_model
        self.chaser_model = chaser_model
        self.ratio_int_selection = ttk.StringVar(value=kwargs.pop("selection", "custom"))
        self.ratio_int_custom = ttk.DoubleVar(value=kwargs.pop("Manual", self.DEFAULT_INT_RATIO))
        self.ratio_final_selection = ttk.StringVar(value=kwargs.pop("selection", "custom"))
        self.ratio_final_custom = ttk.DoubleVar(value=kwargs.pop("Manual", 1.0))
        self.t_selection = ttk.StringVar(value=kwargs.pop("selection", "custom"))
        self.t_custom = ttk.DoubleVar(value=kwargs.pop("Manual", 0.0))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        # If copied from the SettingsModel, we want to have new references to the existing target and chaser models
        if id(self.target_model) in memo:
            result.target_model = memo[id(self.target_model)]
        else:
            result.target_model = copy.deepcopy(self.target_model)
        if id(self.chaser_model) in memo:
            result.chaser_model = memo[id(self.chaser_model)]
        else:
            result.chaser_model = copy.deepcopy(self.chaser_model)

        result.ratio_final_selection = ttk.StringVar(value=self.ratio_final_selection.get())
        result.ratio_final_custom = ttk.DoubleVar(value=self.ratio_final_custom.get())
        result.t_selection = ttk.StringVar(value=self.t_selection.get())
        result.t_custom = ttk.DoubleVar(value=self.t_custom.get())

        return result

    @property
    def r_init(self) -> float:
        return self.chaser_model.to_config().radius

    @property
    def r_int(self) -> float:
        if self.ratio_final_selection.get().lower() == "custom":
            return self.ratio_final_custom.get()
        else:
            raise ValueError(f"Unknown option for radius: {self.ratio_final_selection.get()}")

    @r_int.setter
    def r_int(self, r) -> None:
        matching_r_threshold = 0.001 # km = 1m
        if r - self.target_model.to_config().semimajor < matching_r_threshold and self.target_model.eccentricity == 0:
            self.ratio_final_selection.set("target".capitalize())
        else:
            self.ratio_final_selection.set("custom".capitalize())
            self.ratio_final_custom.set(r)

    @property
    def r_final(self) -> float:
        if self.ratio_final_selection.get().lower() == "custom":
            return self.ratio_final_custom.get()
        elif self.ratio_final_selection.get().lower() == "target":
            return self.target_model.to_config().radius
        else:
            raise ValueError(f"Unknown option for radius: {self.ratio_final_selection.get()}")

    @r_final.setter
    def r_final(self, r) -> None:
        matching_r_threshold = 0.001 # km = 1m
        if r - self.target_model.to_config().semimajor < matching_r_threshold and self.target_model.eccentricity == 0:
            self.ratio_final_selection.set("target".capitalize())
        else:
            self.ratio_final_selection.set("custom".capitalize())
            self.ratio_final_custom.set(r)

    @property
    def t_start(self) -> float:
        if self.t_selection.get().lower() == "custom":
            return self.t_custom.get()
        elif self.t_selection.get().lower() == "immediate":
            return 0
        elif self.t_selection.get().lower() == "rendezvous":
            # TODO: implement Vallado Algorithm 45: Circular Coplanar Phasing (Different Orbits) pg 367
            raise ValueError(f"{self.t_selection.get()} Not yet implemented")
        else:
            raise ValueError(f"Unknown option for time: {self.t_selection.get()}")

    @t_start.setter
    def t_start(self, t) -> None:
        if t == 0:
            self.t_selection.set("immediate".capitalize())
        else:
            self.t_selection.set("custom".capitalize())
            self.t_custom.set(t)

    @property
    def delta_t(self) -> float:
        return np.pi * np.sqrt((self.chaser_model.to_config().radius + self.r_final)**3 / (8 * earth.mu))

    @property
    def delta_v_1(self) -> float:
        r"""
        Gets the magnitude of the first impulsive burn.
        The sign indicates if the burn is in the direction of velocity (positive) or opposite the direction of
        velocity (negative).

        :param self: Description
        :return: Description
        :rtype: float
        """
        r1 = self.chaser_model.to_config().radius
        r2 = self.r_final
        return np.sqrt(earth.mu / r1) * (np.sqrt(2 * r2 / (r1 + r2)) - 1)

    @property
    def delta_v_2(self) -> float:
        r1 = self.chaser_model.to_config().radius
        r2 = self.r_final
        return np.sqrt(earth.mu / r2) * (1 - np.sqrt(2 * r1 / (r1 + r2)))


    @property
    def delta_v_3(self) -> float:
        r1 = self.chaser_model.to_config().radius
        r2 = self.r_final
        return np.sqrt(earth.mu / r2) * (1 - np.sqrt(2 * r1 / (r1 + r2)))

    @property
    def delta_v_total(self) -> float:
        return abs(self.delta_v_1) + abs(self.delta_v_2) + abs(self.delta_v_3)


    def register_cb(self, cb) -> list[tuple]:
        """
        Register callback on variables that affect the generation of the final radius.

        :param cb: Callback
        :returns: (variable, trace_id) pairs. The caller can remove them on destruction.
        """
        watched = [
            self.ratio_int_selection, self.ratio_int_custom, self.ratio_final_selection, self.ratio_final_custom, self.t_selection, self.t_custom
        ]
        return [(v, v.trace_add("write", cb)) for v in watched]

    def to_config(self) -> list[ImpulseConfig]:
        return [
            ImpulseConfig(time=self.t_start, delta_v=self.delta_v_1),
            ImpulseConfig(time=self.t_start + self.delta_t, delta_v=self.delta_v_2),
            ImpulseConfig(time=self.t_start + self.delta_t, delta_v=self.delta_v_2)
        ]



class SettingsModel:
    """
    Model to represent the state of the settings UI.
    """

    def __init__(self):
        self.target_orbit = OrbitModel()
        self.chaser_orbit = OrbitModel()
        self.orbit_maneuvers = []

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        # Orbits must be copied before maneuvers
        result.target_orbit = copy.deepcopy(self.target_orbit, memo)
        result.chaser_orbit = copy.deepcopy(self.chaser_orbit, memo)
        result.orbit_maneuvers = copy.deepcopy(self.orbit_maneuvers, memo)
        return result

    def to_config(self) -> SimConfig:
        target = self.target_orbit.to_config()
        chaser = self.chaser_orbit.to_config()
        maneuvers: list[ImpulseConfig] = []
        for m in self.orbit_maneuvers:
            maneuvers.extend(m.to_config())
        return SimConfig(target_orbit=target, chaser_orbit=chaser, maneuvers=maneuvers)
