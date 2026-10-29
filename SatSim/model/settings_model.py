import copy
import ttkbootstrap as ttk
from math import isclose
import numpy as np

from SatSim.common import earth
from SatSim.model.orbit_model import ImpulseModel, SimModel, OrbitModel


class OrbitSettingsModel:
    r"""
    Hold the settings data for orbit parameters.
    """

    def __init__(self, **kwargs):
        self.altitude_km = ttk.DoubleVar(value=kwargs.pop("altitude_km", 450))
        self.inclination_deg = ttk.DoubleVar(value=kwargs.pop("inclination_deg", 30))
        self.eccentricity = ttk.DoubleVar(value=kwargs.pop("eccentricity", 0))
        self.node = ttk.DoubleVar(value=kwargs.pop("node", 0))
        self.arg_perigee = ttk.DoubleVar(value=kwargs.pop("arg_perigee", 0))
        self.true_anomaly = ttk.DoubleVar(value=kwargs.pop("true_anomaly", 0))

        # Special cases
        self.true_longitude = ttk.DoubleVar(value=kwargs.pop("true_longitude", 0))
        self.arg_latitude = ttk.DoubleVar(value=kwargs.pop("arg_latitude", 0))
        self.long_periapsis = ttk.DoubleVar(value=kwargs.pop("long_periapsis", 0))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        result.altitude_km = ttk.DoubleVar(value=self.altitude_km.get())
        result.inclination_deg = ttk.DoubleVar(value=self.inclination_deg.get())
        result.eccentricity = ttk.DoubleVar(value=self.eccentricity.get())
        result.node = ttk.DoubleVar(value=self.node.get())
        result.arg_perigee = ttk.DoubleVar(value=self.arg_perigee.get())
        result.true_anomaly = ttk.DoubleVar(value=self.true_anomaly.get())
        result.true_longitude = ttk.DoubleVar(value=self.true_longitude.get())
        result.arg_latitude = ttk.DoubleVar(value=self.arg_latitude.get())
        result.long_periapsis = ttk.DoubleVar(value=self.long_periapsis.get())
        return result

    @staticmethod
    def from_config(config: OrbitModel) -> 'OrbitSettingsModel':
        if config.eccentricity == 0.0 and config.inclination == 0.0:
            return OrbitSettingsModel(
                altitude_km=config.semimajor - earth.radius,
                true_longitude=config.true_anomaly,
                inclination_deg=0.0
            )
        elif config.eccentricity == 0.0:
            return OrbitSettingsModel(
                altitude_km=config.semimajor - earth.radius,
                inclination_deg=config.inclination,
                node=config.node,
                arg_latitude=config.true_anomaly
            )
        elif config.inclination == 0.0:
            return OrbitSettingsModel(
                altitude_km=config.semimajor * (1 - config.eccentricity) - earth.radius,
                eccentricity=config.eccentricity,
                inclination_deg=0.0,
                long_periapsis=config.arg_perigee,
                true_anomaly=config.true_anomaly
            )
        else:
            return OrbitSettingsModel(
                altitude_km=config.semimajor * (1 - config.eccentricity) - earth.radius,
                eccentricity=config.eccentricity,
                inclination_deg=config.inclination,
                node=config.node,
                arg_perigee=config.arg_perigee,
                true_anomaly=config.true_anomaly
            )

    def copy_from(self, other: 'OrbitSettingsModel') -> None:
        """Copy values from `other` in place, writing only variables that changed so downstream traces stay quiet."""
        FIELDS = ("altitude_km", "inclination_deg", "eccentricity", "node", "arg_perigee",
                  "true_anomaly", "true_longitude", "arg_latitude", "long_periapsis")
        for name in FIELDS:
            new = getattr(other, name).get()
            var = getattr(self, name)
            if var.get() != new:
                var.set(new)

    def register_cb(self, cb) -> list[tuple]:
        """
        Register callback on all variables.
        
        :param cb: Callback
        :returns: (variable, trace_id) pairs. The caller can remove them on destruction.
        """
        watched = [
            self.altitude_km, self.inclination_deg, self.eccentricity, self.node, self.arg_perigee,
            self.true_anomaly, self.true_longitude, self.arg_latitude, self.long_periapsis
        ]
        return [(v, v.trace_add("write", cb)) for v in watched]

    def to_orbit(self) -> OrbitModel:
        if self.eccentricity.get() == 0.0 and self.inclination_deg.get() == 0.0:
            return OrbitModel.from_circular_eq(
                radius=self.altitude_km.get() + earth.radius,
                true_longitude=self.true_longitude.get()
            )
        elif self.eccentricity.get() == 0.0:
            return OrbitModel.from_circular_inc(
                radius=self.altitude_km.get() + earth.radius,
                inclination=self.inclination_deg.get(),
                node=self.node.get(),
                arg_latitude=self.arg_latitude.get()
            )
        elif self.inclination_deg.get() == 0.0:
            return OrbitModel.from_elliptical_eq(
                semimajor=(self.altitude_km.get() + earth.radius) / (1 - self.eccentricity.get()),
                eccentricity=self.eccentricity.get(),
                long_periapsis=self.long_periapsis.get(),
                true_anomaly=self.true_anomaly.get()
            )
        else:
            return OrbitModel(
                semimajor=(self.altitude_km.get() + earth.radius) / (1 - self.eccentricity.get()),
                eccentricity=self.eccentricity.get(),
                inclination=self.inclination_deg.get(),
                node=self.node.get(),
                arg_perigee=self.arg_perigee.get(),
                true_anomaly=self.true_anomaly.get()
            )


class HohmannSettingsModel:
    r"""
    Hold the settings data for a Hohmann Transfer.

    Assumes circular and coplanar start and end orbits, with apogee kick exactly at $\nu = 180^\circ$
    """

    def __init__(self, target_orbit: OrbitSettingsModel, chaser_orbit: OrbitSettingsModel, **kwargs):
        self.target_init_orbit = target_orbit
        self.chaser_init_orbit = chaser_orbit
        self.r_selection = ttk.StringVar(value=kwargs.pop("selection", "target"))
        self.r_custom = ttk.DoubleVar(value=kwargs.pop("Manual", target_orbit.to_orbit().radius))
        self.t_selection = ttk.StringVar(value=kwargs.pop("selection", "immediate"))
        self.t_custom = ttk.DoubleVar(value=kwargs.pop("Manual", 60.0))

        self.t_offset = 0.0  # Used to calculate where target is in its orbit
        self.traces = []  # Traces from registered callbacks

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        # If copied from the SettingsModel, we want to have new references to the existing target and chaser models
        if id(self.target_init_orbit) in memo:
            result.target_init_orbit = memo[id(self.target_init_orbit)]
        else:
            result.target_init_orbit = copy.deepcopy(self.target_init_orbit)
        if id(self.chaser_init_orbit) in memo:
            result.chaser_init_orbit = memo[id(self.chaser_init_orbit)]
        else:
            result.chaser_init_orbit = copy.deepcopy(self.chaser_init_orbit)

        result.r_selection = ttk.StringVar(value=self.r_selection.get())
        result.r_custom = ttk.DoubleVar(value=self.r_custom.get())
        result.t_selection = ttk.StringVar(value=self.t_selection.get())
        result.t_custom = ttk.DoubleVar(value=self.t_custom.get())

        result.t_offset = self.t_offset
        result.traces = []
        return result

    @property
    def r_final(self) -> float:
        if self.r_selection.get().lower() == "custom":
            return self.r_custom.get()
        elif self.r_selection.get().lower() == "target":
            return self.target_init_orbit.to_orbit().radius
        else:
            raise ValueError(f"Unknown option for radius: {self.r_selection.get()}")

    @r_final.setter
    def r_final(self, r) -> None:
        matching_r_threshold = 0.001  # km = 1m
        if r - self.target_init_orbit.to_orbit().semimajor < matching_r_threshold and self.target_init_orbit.eccentricity == 0:
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
            return self.min_wait_time
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
        return np.pi * np.sqrt((self.chaser_init_orbit.to_orbit().radius + self.r_final) ** 3 / (8 * earth.mu))

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
        r1 = self.chaser_init_orbit.to_orbit().radius
        r2 = self.r_final
        return np.sqrt(earth.mu / r1) * (np.sqrt(2 * r2 / (r1 + r2)) - 1)

    @property
    def delta_v_2(self) -> float:
        r1 = self.chaser_init_orbit.to_orbit().radius
        r2 = self.r_final
        return np.sqrt(earth.mu / r2) * (1 - np.sqrt(2 * r1 / (r1 + r2)))

    @property
    def delta_v_total(self) -> float:
        return abs(self.delta_v_1) + abs(self.delta_v_2)

    @property
    def delta_phase(self) -> float:
        """Phase change (deg)"""
        a_chaser = self.chaser_init_orbit.to_orbit().radius
        ang_vel_chaser = np.sqrt(earth.mu / a_chaser ** 3)
        return np.rad2deg(ang_vel_chaser) * self.t_start + 180

    @property
    def min_wait_time(self) -> float:
        r"""
        Minimum wait time (number of extra revolutions = 0) to rendezvous with Hohmann transfer.

        :see also: Vallado, Algorithm 45, page 367
        :return: Time (s)
        """
        a_tgt = self.target_init_orbit.to_orbit().radius
        a_int = self.chaser_init_orbit.to_orbit().radius
        ang_vel_tgt = np.sqrt(earth.mu / a_tgt ** 3)
        ang_vel_int = np.sqrt(earth.mu / a_int ** 3)
        lead_angle = ang_vel_tgt * self.delta_t

        # Pre-burn phase angle
        phase_angle_init = self.t_offset * ang_vel_tgt + np.deg2rad(
            self.target_init_orbit.to_orbit().true_anomaly - self.chaser_init_orbit.to_orbit().true_anomaly)
        # Desired phase angle for rendezvous
        phase_angle_begin = np.pi - lead_angle
        delta_phase = phase_angle_begin - phase_angle_init
        delta_ang_vel = ang_vel_tgt - ang_vel_int
        if delta_phase > 0 and delta_ang_vel < 0:
            # Need to make delta_phase negative
            delta_phase -= np.pi * 2
        elif delta_phase < 0 and delta_ang_vel > 0:
            # Need to make delta_phase negative
            delta_phase += np.pi * 2

        return delta_phase / delta_ang_vel

    @property
    def result_orbit(self) -> OrbitModel:
        """Resulting orbit parameters from this maneuver"""
        return OrbitModel(
            semimajor=self.r_final,
            eccentricity=0.0,
            inclination=self.chaser_init_orbit.inclination_deg.get(),
            node=self.chaser_init_orbit.node.get(),
            arg_perigee=self.chaser_init_orbit.arg_perigee.get(),
            true_anomaly=self.chaser_init_orbit.to_orbit().true_anomaly + self.delta_phase
        )

    @property
    def target_orbit(self) -> OrbitModel:
        return self.target_init_orbit.to_orbit().propagate(self.delta_t + self.t_start)

    @property
    def chaser_model(self) -> OrbitSettingsModel:
        return OrbitSettingsModel.from_config(self.result_orbit)

    @property
    def target_model(self) -> OrbitSettingsModel:
        return OrbitSettingsModel.from_config(self.target_orbit)

    def _on_destroy(self, event) -> None:
        # <Destroy> event also fires for child widgets; only react to this frame.
        if event.widget is not self:
            return
        for var, trace_id in self.traces:
            var.trace_remove("write", trace_id)

    def register_cb(self, cb) -> list[tuple]:
        """
        Register callback on variables that affect the generation of the dependent parameters.
        
        :param cb: Callback
        :returns: (variable, trace_id) pairs. The caller can remove them on destruction.
        """
        watched = [
            self.r_selection, self.r_custom, self.t_selection, self.t_custom
        ]
        return [(v, v.trace_add("write", cb)) for v in watched]

    def to_impulse(self, t_offset=0.0) -> list[ImpulseModel]:
        self.t_offset = t_offset
        return [
            ImpulseModel(time=t_offset + self.t_start, delta_v=self.delta_v_1),
            ImpulseModel(time=t_offset + self.t_start + self.delta_t, delta_v=self.delta_v_2)
        ]


class BiellipticSettingsModel:
    r"""
    Hold the settings data for a Bi-elliptic Transfer.

    Assumes circular and coplanar start and end orbits, with apogee kick exactly at $\nu = 180^\circ$

    Uses Vallado Algorith 37, pg 330.
    """

    DEFAULT_INT_RATIO = 40
    r"""
    Ratio between intermediate orbit and initial orbit, ..math:`R^* = r_{int} / r_{initial}`.
    """

    def __init__(self, target_orbit: OrbitSettingsModel, chaser_orbit: OrbitSettingsModel, **kwargs):
        self.target_init_orbit = target_orbit
        self.chaser_init_orbit = chaser_orbit
        self.ratio_int_selection = ttk.StringVar(value=kwargs.pop("selection", "custom"))
        self.ratio_int_custom = ttk.DoubleVar(value=kwargs.pop("Manual", self.DEFAULT_INT_RATIO))
        self.ratio_final_selection = ttk.StringVar(value=kwargs.pop("selection", "target"))
        self.ratio_final_custom = ttk.DoubleVar(value=kwargs.pop("Manual", 1.0))
        self.t_selection = ttk.StringVar(value=kwargs.pop("selection", "immediate"))
        self.t_custom = ttk.DoubleVar(value=kwargs.pop("Manual", 60.0))

        self.t_offset = 0.0  # Used to calculate where target is in its orbit
        self.traces = []  # Traces from registered callbacks

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        # If copied from the SettingsModel, we want to have new references to the existing target and chaser models
        if id(self.target_init_orbit) in memo:
            result.target_init_orbit = memo[id(self.target_init_orbit)]
        else:
            result.target_init_orbit = copy.deepcopy(self.target_init_orbit)
        if id(self.chaser_init_orbit) in memo:
            result.chaser_init_orbit = memo[id(self.chaser_init_orbit)]
        else:
            result.chaser_init_orbit = copy.deepcopy(self.chaser_init_orbit)

        result.ratio_int_selection = ttk.StringVar(value=self.ratio_int_selection.get())
        result.ratio_int_custom = ttk.DoubleVar(value=self.ratio_int_custom.get())
        result.ratio_final_selection = ttk.StringVar(value=self.ratio_final_selection.get())
        result.ratio_final_custom = ttk.DoubleVar(value=self.ratio_final_custom.get())
        result.t_selection = ttk.StringVar(value=self.t_selection.get())
        result.t_custom = ttk.DoubleVar(value=self.t_custom.get())

        result.t_offset = self.t_offset
        result.traces = []
        return result

    @property
    def r_init(self) -> float:
        return self.chaser_init_orbit.to_orbit().radius

    @property
    def r_int(self) -> float:
        if self.ratio_int_selection.get().lower() == "custom":
            return self.ratio_int_custom.get() * self.chaser_init_orbit.to_orbit().radius
        else:
            raise ValueError(f"Unknown option for radius: {self.ratio_int_selection.get()}")

    @r_int.setter
    def r_int(self, r) -> None:
        matching_r_threshold = 0.001  # km = 1m
        if r - self.target_init_orbit.to_orbit().semimajor < matching_r_threshold and self.target_init_orbit.eccentricity == 0:
            self.ratio_final_selection.set(
                "target".capitalize())  # TODO: remove, should be no options for intermediate orbit, other than min delta v maybe?
        else:
            self.ratio_final_selection.set("custom".capitalize())
            self.ratio_final_custom.set(r)

    @property
    def r_final(self) -> float:
        if self.ratio_final_selection.get().lower() == "custom":
            return self.ratio_final_custom.get() * self.chaser_init_orbit.to_orbit().radius
        elif self.ratio_final_selection.get().lower() == "target":
            return self.target_init_orbit.to_orbit().radius
        else:
            raise ValueError(f"Unknown option for radius: {self.ratio_final_selection.get()}")

    @r_final.setter
    def r_final(self, r) -> None:
        matching_r_threshold = 0.001  # km = 1m
        if r - self.target_init_orbit.to_orbit().semimajor < matching_r_threshold and self.target_init_orbit.eccentricity == 0:
            self.ratio_final_selection.set("target".capitalize())
            self.ratio_final_custom.set(
                self.target_init_orbit.to_orbit().semimajor / self.chaser_init_orbit.to_orbit().semimajor)
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
            raise ValueError(f"{self.t_selection.get()} Not yet implemented for Bielliptic Model")
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
    def semimajor_1(self) -> float:
        """Semimajor axis of the first transfer orbit. (km)"""
        return (self.r_init + self.r_int) / 2.0

    @property
    def semimajor_2(self) -> float:
        """Semimajor axis of the second transfer orbit. (km)"""
        return (self.r_int + self.r_final) / 2.0

    @property
    def delta_t_1(self) -> float:
        """Time between first and second burns. (s)"""
        return np.pi / np.sqrt(earth.mu) * self.semimajor_1 ** (3 / 2)

    @property
    def delta_t_2(self) -> float:
        """Time between second and third burns. (s)"""
        return np.pi / np.sqrt(earth.mu) * self.semimajor_2 ** (3 / 2)

    @property
    def delta_t(self) -> float:
        """Total transfer time to new orbit. (s)"""
        return self.delta_t_1 + self.delta_t_2

    @property
    def delta_v_1(self) -> float:
        r"""
        Gets the magnitude of the first of three impulsive burns.
        The sign indicates if the burn is in the direction of velocity (positive) or opposite the direction of
        velocity (negative).

        :return: Value of :math:`\Delta v_1`, first burn. (km/s)
        """
        r1 = self.r_init
        a_trans1 = self.semimajor_1
        v_init = np.sqrt(earth.mu / r1)
        v_trans1a = np.sqrt(2 * earth.mu / r1 - earth.mu / a_trans1)
        return v_trans1a - v_init

    @property
    def delta_v_2(self) -> float:
        r"""
        Gets the magnitude of the second of three impulsive burn.
        The sign indicates if the burn is in the direction of velocity (positive) or opposite the direction of
        velocity (negative).

        :return: Value of :math:`\Delta v_2`, second burns. (km/s)
        """
        r2 = self.r_int
        a_trans1 = self.semimajor_1
        a_trans2 = self.semimajor_2
        v_trans1b = np.sqrt(2 * earth.mu / r2 - earth.mu / a_trans1)
        v_trans2b = np.sqrt(2 * earth.mu / r2 - earth.mu / a_trans2)
        return v_trans2b - v_trans1b

    @property
    def delta_v_3(self) -> float:
        r"""
        Gets the magnitude of the third of three impulsive burn.
        The sign indicates if the burn is in the direction of velocity (positive) or opposite the direction of
        velocity (negative).

        :return: Value of :math:`\Delta v_3`, third burns. (km/s)
        """
        r3 = self.r_final
        a_trans2 = self.semimajor_2
        v_trans2c = np.sqrt(2 * earth.mu / r3 - earth.mu / a_trans2)
        v_final = np.sqrt(earth.mu / r3)
        return v_final - v_trans2c

    @property
    def delta_phase(self) -> float:
        """Phase change (deg)"""
        a_chaser = self.chaser_init_orbit.to_orbit().radius
        ang_vel_chaser = np.sqrt(earth.mu / a_chaser ** 3)
        return np.rad2deg(ang_vel_chaser) * self.t_start + 360

    @property
    def delta_v_total(self) -> float:
        return abs(self.delta_v_1) + abs(self.delta_v_2) + abs(self.delta_v_3)

    @property
    def result_orbit(self) -> OrbitModel:
        """Resulting orbit parameters from this maneuver"""
        return OrbitModel(
            semimajor=self.r_final,
            eccentricity=0.0,
            inclination=self.chaser_init_orbit.inclination_deg.get(),
            node=self.chaser_init_orbit.node.get(),
            arg_perigee=self.chaser_init_orbit.arg_perigee.get(),
            true_anomaly=self.chaser_init_orbit.to_orbit().true_anomaly + self.delta_phase
        )

    @property
    def target_orbit(self) -> OrbitModel:
        return self.target_init_orbit.to_orbit().propagate(self.delta_t + self.t_start)

    @property
    def chaser_model(self) -> OrbitSettingsModel:
        return OrbitSettingsModel.from_config(self.result_orbit)

    @property
    def target_model(self) -> OrbitSettingsModel:
        return OrbitSettingsModel.from_config(self.target_orbit)

    def _on_destroy(self, event):
        # <Destroy> event also fires for child widgets; only react to this frame.
        if event.widget is not self:
            return
        for var, trace_id in self.traces:
            var.trace_remove("write", trace_id)

    def register_cb(self, cb) -> list[tuple]:
        """
        Register callback on variables that affect the generation of the final radius.

        :param cb: Callback
        :returns: (variable, trace_id) pairs. The caller can remove them on destruction.
        """
        watched = [
            self.ratio_int_selection, self.ratio_int_custom, self.ratio_final_selection, self.ratio_final_custom,
            self.t_selection, self.t_custom
        ]
        return [(v, v.trace_add("write", cb)) for v in watched]

    def to_impulse(self, t_offset=0.0) -> list[ImpulseModel]:
        return [
            ImpulseModel(time=t_offset + self.t_start, delta_v=self.delta_v_1),
            ImpulseModel(time=t_offset + self.t_start + self.delta_t_1, delta_v=self.delta_v_2),
            ImpulseModel(time=t_offset + self.t_start + self.delta_t_1 + self.delta_t_2, delta_v=self.delta_v_3)
        ]


class PhasingSettingsModel:
    r"""
    Hold the settings data for a Phasing Orbit Transfer.

    :see also: Vallado, Algorithm 44, pg 366
    """

    def __init__(self, target_orbit: OrbitSettingsModel, chaser_orbit: OrbitSettingsModel, **kwargs):
        self.target_init_orbit = target_orbit
        self.chaser_init_orbit = chaser_orbit
        self.orbit_count = ttk.IntVar(value=kwargs.pop("Count", 1))
        self.t_selection = ttk.StringVar(value=kwargs.pop("selection", "immediate"))
        self.t_custom = ttk.DoubleVar(value=kwargs.pop("Manual", 60.0))

        self.t_offset = 0.0  # Used to calculate where target is in its orbit
        self.traces = []  # Traces from registered callbacks

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        # If copied from the SettingsModel, we want to have new references to the existing target and chaser models
        if id(self.target_init_orbit) in memo:
            result.target_init_orbit = memo[id(self.target_init_orbit)]
        else:
            result.target_init_orbit = copy.deepcopy(self.target_init_orbit)
        if id(self.chaser_init_orbit) in memo:
            result.chaser_init_orbit = memo[id(self.chaser_init_orbit)]
        else:
            result.chaser_init_orbit = copy.deepcopy(self.chaser_init_orbit)

        result.orbit_count = ttk.IntVar(value=self.orbit_count.get())
        result.t_selection = ttk.StringVar(value=self.t_selection.get())
        result.t_custom = ttk.DoubleVar(value=self.t_custom.get())

        result.t_offset = self.t_offset
        result.traces = []
        return result

    def _assert_same_orbit(self) -> None:
        ECCENTRICITY_TOL = 0.01
        ARG_PERIGEE_TOL = 0.01  # Deg
        INCLINATION_TOL = 0.01  # Deg
        NODE_TOL = 0.01  # Deg
        SEMIMAJOR_TOL = 1  # km
        target = self.target_init_orbit.to_orbit()
        chaser = self.chaser_init_orbit.to_orbit()
        if not isclose(target.eccentricity, chaser.eccentricity, rel_tol=ECCENTRICITY_TOL):
            raise ValueError(
                f"Target and chaser eccentricity must agree, differ by {abs(target.eccentricity - chaser.eccentricity)}.")
        if not isclose(target.arg_perigee, chaser.arg_perigee, rel_tol=ARG_PERIGEE_TOL):
            raise ValueError(
                f"Target and chaser argument of perigee must agree, differ by {abs(target.arg_perigee - chaser.arg_perigee)} degrees.")
        if not isclose(target.inclination, chaser.inclination, rel_tol=INCLINATION_TOL):
            raise ValueError(
                f"Target and chaser inclination must agree, differ by {abs(target.inclination - chaser.inclination)} degrees.")
        if not isclose(target.node, chaser.node, rel_tol=NODE_TOL):
            raise ValueError(
                f"Target and chaser right ascension of ascending node must agree, differ by {abs(target.node - chaser.node)} degrees.")
        if not isclose(target.semimajor, chaser.semimajor, rel_tol=SEMIMAJOR_TOL):
            raise ValueError(
                f"Target and chaser argument of perigee must agree, differ by {abs(target.semimajor - chaser.semimajor)} degrees.")

    @property
    def t_start(self) -> float:
        if self.t_selection.get().lower() == "custom":
            return self.t_custom.get()
        elif self.t_selection.get().lower() == "immediate":
            return 0
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
        r"""
        Computes the required time of the phasing orbit.


        """
        self._assert_same_orbit()
        chaser = self.chaser_init_orbit.to_orbit()
        target = self.target_init_orbit.to_orbit()
        ecc = chaser.eccentricity
        delta_true_anomaly = np.deg2rad(chaser.true_anomaly - target.true_anomaly)
        ang_vel = np.sqrt(earth.mu / chaser.semimajor ** 3)

        add_time = chaser.period if delta_true_anomaly < 0 else 0

        return (np.pi * 2 * self.orbit_count.get() + delta_true_anomaly) / ang_vel + add_time

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
        semimajor_phasing = (np.sqrt(earth.mu) * self.delta_t / (2 * np.pi * self.orbit_count.get())) ** (2 / 3)

        # assuming circular for now
        radius = self.target_init_orbit.to_orbit().radius
        vel_phasing = np.sqrt(2 * earth.mu * (1 / radius - 1 / (2 * semimajor_phasing)))
        vel_init = np.sqrt(earth.mu / radius)
        return vel_phasing - vel_init

    @property
    def delta_v_2(self) -> float:
        return -self.delta_v_1

    @property
    def delta_v_total(self) -> float:
        return abs(self.delta_v_1) + abs(self.delta_v_2)

    @property
    def delta_phase(self) -> float:
        """Phase change (deg)"""
        self._assert_same_orbit()
        chaser = self.chaser_init_orbit.to_orbit()
        target = self.target_init_orbit.to_orbit()
        return chaser.true_anomaly - target.true_anomaly

    @property
    def result_orbit(self) -> OrbitModel:
        """Resulting orbit parameters from this maneuver"""
        return OrbitModel(
            semimajor=self.chaser_init_orbit.to_orbit().semimajor,
            eccentricity=0.0,
            inclination=self.chaser_init_orbit.inclination_deg.get(),
            node=self.chaser_init_orbit.node.get(),
            arg_perigee=self.chaser_init_orbit.arg_perigee.get(),
            true_anomaly=self.chaser_init_orbit.to_orbit().true_anomaly + self.delta_phase
        )

    @property
    def target_orbit(self) -> OrbitModel:
        return self.target_init_orbit.to_orbit().propagate(self.delta_t + self.t_start)

    @property
    def chaser_model(self) -> OrbitSettingsModel:
        return OrbitSettingsModel.from_config(self.result_orbit)

    @property
    def target_model(self) -> OrbitSettingsModel:
        return OrbitSettingsModel.from_config(self.target_orbit)

    def _on_destroy(self, event) -> None:
        # <Destroy> event also fires for child widgets; only react to this frame.
        if event.widget is not self:
            return
        for var, trace_id in self.traces:
            var.trace_remove("write", trace_id)

    def register_cb(self, cb) -> list[tuple]:
        """
        Register callback on variables that affect the generation of the dependent parameters.
        
        :param cb: Callback
        :returns: (variable, trace_id) pairs. The caller can remove them on destruction.
        """
        watched = [
            self.t_selection, self.t_custom, self.orbit_count
        ]
        return [(v, v.trace_add("write", cb)) for v in watched]

    def to_impulse(self, t_offset=0.0) -> list[ImpulseModel]:
        self.t_offset = t_offset
        return [
            ImpulseModel(time=t_offset + self.t_start, delta_v=self.delta_v_1),
            ImpulseModel(time=t_offset + self.t_start + self.delta_t, delta_v=self.delta_v_2)
        ]


class SettingsModel:
    """
    Model to represent the state of the settings UI.
    """

    def __init__(self):
        self.target_orbit = OrbitSettingsModel()
        self.chaser_orbit = OrbitSettingsModel()
        self.orbit_maneuvers: list[HohmannSettingsModel | BiellipticSettingsModel | PhasingSettingsModel | None] = []

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        # Orbits must be copied before maneuvers
        result.target_orbit = copy.deepcopy(self.target_orbit, memo)
        result.chaser_orbit = copy.deepcopy(self.chaser_orbit, memo)
        result.orbit_maneuvers = copy.deepcopy(self.orbit_maneuvers, memo)
        return result

    def to_model(self) -> SimModel:
        target = self.target_orbit.to_orbit()
        chaser = self.chaser_orbit.to_orbit()
        maneuvers: list[ImpulseModel] = []
        t0 = 0.0  # Ensure maneuvers are timed to not overlap
        for m in self.orbit_maneuvers:
            if m is not None:
                maneuvers.extend(m.to_impulse(t0))
                t0 += maneuvers[-1].time
        return SimModel(target_orbit=target, chaser_orbit=chaser, maneuvers=maneuvers)
