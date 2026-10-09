import numpy as np
from scipy.integrate import solve_ivp

from SatSim.model.settings_model import SettingsModel
from SatSim.model.orbit_model import OrbitModel
from SatSim.model.maneuver_model import ImpulseConfig

class Simulate:

    def __init__(self, settings:SettingsModel):
        self.settings = settings
        self.orbits:list[OrbitModel] = []
        self.orbit_events = []
        self.maneuvers:list[ImpulseConfig] = []
        self.apply_impulse:ImpulseConfig|None = None
        self.times = []
        self.states = []

    @staticmethod
    def _dynamics(t, y, self: 'Simulate') -> np.ndarray:
        y_prime = np.zeros(y.shape)
        for start_idx, orbit in enumerate(self.orbits):
            y_prime[start_idx * 6:start_idx * 6 + 6] = orbit.dynamics(t, y[start_idx * 6:start_idx * 6 + 6])
        return y_prime

    @staticmethod
    def _impulse_event(t, y, self:'Simulate') -> float:
        if len(self.maneuvers) > 0:
            return t - self.maneuvers[0].time
        else:
            return 1


    def _get_max_period(self) -> float:
        # TODO: get max period needs to look at current pos, vel vectors, not config.
        return np.max([orbit.config.period for orbit in self.orbits])

    def run_simulation(self):
        r"""

        Note that if :code:`solve_ivp`'s argument for relative tolerance, `rtol`, is not sufficiently small, this will not work.

        :return:
        """
        config = self.settings.to_config()
        dt = 5  # (s) TODO: make configurable
        self.orbits = [OrbitModel(config.target_orbit), OrbitModel(config.chaser_orbit)]
        self.maneuvers = config.maneuvers
        self.maneuvers.sort(key=lambda x: x.time)
        self._impulse_event.terminal = True
        self._impulse_event.direction = 1

        t0 = 0.0
        y0 = np.concatenate([orbit.initial_state() for orbit in self.orbits])

        if len(self.maneuvers) > 0 and (self.maneuvers[0].time <= dt):
            man = self.maneuvers.pop(0) # remove maneuver from list
            # Apply impulsive delta v in the direction of the current velocity vector
            v_norm = y0[9:12] / np.linalg.norm(y0[9:12])
            y0[9:12] += v_norm * man.delta_v

        self.times = [t0]
        self.states = [y0]

        # For now let's default to running 2 periods after any change
        t_final = self._get_max_period() * 2

        while self.times[-1] < t_final:
            # Drop the first linspace point
            t_eval = np.linspace(t0, t_final, int((t_final - t0) / dt) + 1)[1:]

            sol = solve_ivp(
                self._dynamics, [t_eval[0], t_eval[-1]], y0, t_eval=t_eval,
                args=(self,), rtol=1e-9, events=self._impulse_event
            )
            self.times.extend(sol.t)
            self.states.extend(sol.y.T)

            # Index 0 corresponds to _impulse_events
            if len(sol.t_events[0]) > 0:
                man = self.maneuvers.pop(0) # remove maneuver from list
                y0 = sol.y[:, -1]
                # Apply impulsive delta v in the direction of the current velocity vector
                v_norm = y0[9:12] / np.linalg.norm(y0[9:12])
                y0[9:12] += v_norm * man.delta_v
                # Extend simulation length
                t0 = sol.t[-1]
                t_final = self._get_max_period() * 2 + sol.t[-1]


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
        time_idxs = (np.asarray(self.times) >= t_min) & (np.asarray(self.times) <= t_max)
        return np.array(self.times)[time_idxs], np.array(self.states)[time_idxs, orbit_idx:orbit_idx + 3]

    def get_full_positions(self, orbit_idx: int) -> tuple[np.ndarray, np.ndarray]:
        """

        :param orbit_idx:
        :return: The times (s) and positions in the geocentric reference frame in km.
        """
        if len(self.times) == 0:
            return np.array([]), np.array([])
        return np.array(self.times), np.array(self.states)[:, orbit_idx * 6:orbit_idx * 6 + 3]
