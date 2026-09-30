import numpy as np
from scipy.integrate import solve_ivp

from SatSim.model.orbit_model import OrbitModel


class Simulate:

    def __init__(self):
        self.orbits: list[OrbitModel] = []
        self.orbit_events = []
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

    def add_orbit(self, orbit: OrbitModel, events: tuple | list = tuple()) -> int:
        """

        :param orbit:
        :param events: Iterable of events to pass to the solver.
        :return: The index of the orbit in the orbits list.
        """
        self.orbits.append(orbit)
        self.orbit_events.append(events)
        return len(self.orbits) - 1

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
