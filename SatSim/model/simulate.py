import numpy as np
from scipy.integrate import solve_ivp

from SatSim.model.orbit_model import OrbitModel


class Simulate:

    def __init__(self):
        self.orbits: list[OrbitModel] = []
        self.orbit_events = []
        self.maneuvers = []
        self.times = np.array([])
        self.states = np.array([])

    @staticmethod
    def _dynamics(t, y, self: 'Simulate') -> np.ndarray:
        y_prime = np.zeros(y.shape)
        for start_idx, orbit in enumerate(self.orbits):
            y_prime[start_idx * 6:start_idx * 6 + 6] = orbit.dynamics(t, y[start_idx * 6:start_idx * 6 + 6])
        return y_prime

    def _get_max_period(self) -> float:
        return np.max([orbit.get_period() for orbit in self.orbits])

    def run_simulation(self):
        r"""

        Note that if :code:`solve_ivp`'s argument for relative tolerance, `rtol`, is not sufficiently small, this will not work.

        :return:
        """
        # For now let's default to running 2 periods after any change
        max_period = self._get_max_period() * 2
        dt = 60  # (s) = 1min
        t_eval = np.linspace(0, max_period, int(max_period / dt))
        y0 = np.concatenate([orbit.initial_state() for orbit in self.orbits])
        sol = solve_ivp(
            self._dynamics, [t_eval[0], t_eval[-1]], y0, t_eval=t_eval,
            args=(self,), rtol=1e-9
        )
        self.times = sol.t
        self.states = sol.y.T

    def get_settings(self) -> dict:
        """
        Assembles a dictionary of simulation settings.
        :return: Settings
        """

        def _get_default_orbit() -> dict:
            """
            Helper function for :code:`get_settings` to get a default orbit if none implemented.

            Note that this must be kept in sync with OrbitModel.

            :return: Orbit default settings dict.
            """
            return {"altitude_km": 600.0, "inclination_deg": 60, "eccentricity": 0.0}

        settings = {}
        orbits = {}
        # Orbits only meaningful right now if there is a target and a chaser
        if len(self.orbits) >= 2:
            orbits["chaser"] = self.orbits[0].get()
            orbits["target"] = self.orbits[1].get()
        else:
            orbits["chaser"] = _get_default_orbit()
            orbits["target"] = _get_default_orbit()

        settings["orbits"] = orbits
        settings["maneuvers"] = self.maneuvers

        return settings

    def load_settings(self, settings) -> None:
        """
        Takes a dictionary of simulation settings and stores it as the simulation parameters.
        :param settings: Simulation settings
        """
        self.orbits = []
        self.orbits.append(OrbitModel(**settings["orbits"]["chaser"]))
        self.orbits.append(OrbitModel(**settings["orbits"]["target"]))
        self.maneuvers = settings["maneuvers"]

    def get_total_duration(self) -> float:
        """

        :return: Time duration (s)
        """
        return self.times[-1] - self.times[0]

    def get_positions(self, orbit_idx: int, t_min: float, t_max: float) -> tuple[np.ndarray, np.ndarray]:
        """

        :param orbit_idx:
        :param t_min:
        :param t_max:
        :return: The times (s) and positions in the geocentric reference frame in km.
        """
        time_idxs = (self.times >= t_min) & (self.times <= t_max)
        return self.times[time_idxs], self.states[time_idxs, orbit_idx:orbit_idx + 3]

    def get_full_positions(self, orbit_idx: int) -> tuple[np.ndarray, np.ndarray]:
        """

        :param orbit_idx:
        :return: The times (s) and positions in the geocentric reference frame in km.
        """
        if self.times.size == 0:
            return np.array([]), np.array([])
        return self.times, self.states[:, orbit_idx * 6:orbit_idx * 6 + 3]
