from collections import deque
import itertools
import numpy as np
import queue
from scipy.integrate import solve_ivp

from SatSim.algorithms.multiplicative_ekf import AttitudeObservationVec, MissionModeMekf
from SatSim.common.quaternion import Quaternion
from SatSim.common.attitude_matrix import quaternion_to_rpy
from SatSim.model.settings_model import SettingsModel
from SatSim.model.attitude_dynamics import AttitudeDynamics, MoiTensorCube
from SatSim.model.orbit_dynamics import OrbitDynamics
from SatSim.model.orbit_model import ImpulseModel, OrbitModel


class ImpulseResultsModel:
    def __init__(self, time: float, pos: np.ndarray, magnitude: float):
        self.time = time
        self.pos = pos
        self.magnitude = abs(magnitude)


class Simulate:

    def __init__(self, settings: SettingsModel):
        self.settings = settings
        self.impulse_results: list[ImpulseResultsModel] = []
        self.maneuvers: deque[ImpulseModel] = deque()
        self.orbits: list[OrbitDynamics] = []
        self.attitudes: list[AttitudeDynamics] = []
        self.orbit_events = []
        self.results = []
        self.estimate = []
        self.times = []

        self.update_q: queue.Queue | None = None
        self.t_final = 0.0
        self.pct_complete = 0.0

    @property
    def states(self) -> np.ndarray:
        return np.asarray(self.results)

    def _restart(self):
        self.times = []
        self.impulse_results = []
        self.maneuvers = deque()
        self.orbits = []
        self.orbit_events = []
        self.results = []
        self.estimate = []
        self.pct_complete = 0.0

    @staticmethod
    def _dynamics(t, y, self: 'Simulate') -> np.ndarray:
        self._update_progress(t)

        y_prime = np.zeros(y.shape)
        for orbit_idx, orbit in enumerate(self.orbits):
            start_state_idx = orbit_idx * OrbitDynamics.STATE_LEN
            end_state_idx = start_state_idx + OrbitDynamics.STATE_LEN
            y_prime[start_state_idx:end_state_idx] = OrbitDynamics.dynamics(t, y[start_state_idx:end_state_idx])

        for attitude_idx, attitude in enumerate(self.attitudes):
            moi = attitude.moi_tensor
            start_state_idx = attitude_idx * AttitudeDynamics.STATE_LENGTH + len(self.orbits) * OrbitDynamics.STATE_LEN
            end_state_idx = start_state_idx + AttitudeDynamics.STATE_LENGTH
            y_prime[start_state_idx:end_state_idx] = AttitudeDynamics.dynamics(t, y[start_state_idx:end_state_idx], moi)

        return y_prime

    @staticmethod
    def _impulse_event(t, y, self: 'Simulate') -> float:
        if len(self.maneuvers) > 0:
            return t - self.maneuvers[0].time
        else:
            return 1

    def _get_max_period(self, y0) -> float:
        return np.max([OrbitModel.from_pos_vel(y0[i * 6:i * 6 + 3], y0[i * 6 + 3:i * 6 + 6]).period for i in
                       range(0, len(self.orbits))])

    def _update_progress(self, t: np.floating):
        """
        Adds a payload to the queue with the percent complete. 
        
        Adding to the queue is a very slow operation so we only do it every few percent.
        
        :param t: Description
        """
        if t == 0.0 or self.update_q is None:
            return
        pct = 100 * t / self.t_final
        if pct - self.pct_complete > 3.0:
            self.pct_complete = pct
            self.update_q.put(("progress", pct))

    def _apply_maneuvers(self, t, y) -> np.ndarray:
        r"""
        Apply all maneuvers scheduled at the time of the first pending one.
        
        :param t: The maneuver time
        :param y: State vector
        :return: Update state vector with :math:`\Delta v` applied.
        """
        burn_time = self.maneuvers[0].time
        while self.maneuvers and self.maneuvers[0].time == burn_time:
            man = self.maneuvers.popleft()
            v = y[9:12]
            y[9:12] = v + v / np.linalg.norm(v) * man.delta_v
            self.impulse_results.append(ImpulseResultsModel(t, y[6:9].copy(), man.delta_v))
        return y

    def _advance_simulation(self, t_span: tuple[np.floating, np.floating], y: np.ndarray) -> np.ndarray:
        """
        Integrate the dynamics across t_span, restarting the solver if it is interrupted by a terminal event.
        
        Note that if :code:`solve_ivp`'s argument for relative tolerance, `rtol`, is not sufficiently small, this will not work.

        :param t_span: Time span, (start, end) tuple.
        :param y: The initial state at t_span[0]
        :return: The final state at t_span[1]
        """ 
        t = t_span[0]
        while t < t_span[1]:
            sol = solve_ivp(
                self._dynamics, (t, t_span[1]), y, args=(self,),
                rtol=1e-9, events=self._impulse_event,
            )
            t, y = sol.t[-1], sol.y[:, -1].copy()
            if sol.status == 1:  # terminated by an event
                y = self._apply_maneuvers(t, y)
        return y

    def run_simulation(self, update_q: queue.Queue):
        r"""

        :return:
        """
        self._restart()
        self.update_q = update_q
        config = self.settings.to_model()
        dt = config.estimator.get("dt", 5.0)
        self.orbits = [OrbitDynamics(config.target_orbit), OrbitDynamics(config.chaser_orbit)]
        self.attitudes = [AttitudeDynamics(Quaternion.eye(), np.array([[0, 0, 0.1]]).T,
                                           MoiTensorCube(1, 0.001))]  # TODO: make configurable
        self.maneuvers = deque(sorted(config.maneuvers, key=lambda x: x.time))
        self._impulse_event.terminal = True
        self._impulse_event.direction = 1

        t0 = 0.0
        y = np.concatenate([orbit.initial_state() for orbit in self.orbits])
        att0 = np.concatenate([attitude.initial_state() for attitude in self.attitudes])
        y = np.concatenate((y, att0))

        y = self._apply_maneuvers(t0, y) # Apply any maneuvers at t = 0

        self.t_final = config.sim_time
        n_steps = round(self.t_final / dt)
        self.times = np.arange(0, n_steps + 1) * dt
        self.results = np.empty((len(y), len(self.times)))
        self.results[:, 0] = y.T

        estimator = MissionModeMekf(**config.estimator["constructor"])
        estimator.initialize(**config.estimator["init"])

        for i in range(1, n_steps + 1):
            # Solve the orbital and attitude dynamics for the 6DOF simulation at the current timestep
            y = self._advance_simulation((self.times[i - 1], self.times[i]), y)
            self.results[:, i] = y

            # Construct measurements

            # Evaluate estimator

            # Evaluate controller



        update_q.put(("done", []))

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
        return np.array(self.times)[time_idxs], self.states[orbit_idx * 6:orbit_idx * 6 + 3, time_idxs]

    def get_full_positions(self, orbit_idx: int) -> tuple[np.ndarray, np.ndarray]:
        """

        :param orbit_idx:
        :return: The times (s) and positions in the geocentric reference frame in km.
        """
        if len(self.times) == 0:
            return np.array([]), np.array([])
        return np.array(self.times), self.states[orbit_idx * 6:orbit_idx * 6 + 3, :]

    def get_full_velocities(self, orbit_idx: int) -> tuple[np.ndarray, np.ndarray]:
        """

        :param orbit_idx:
        :return: The times (s) and velocities in the geocentric reference frame in km.
        """
        if len(self.times) == 0:
            return np.array([]), np.array([])
        return np.array(self.times), self.states[orbit_idx * 6 + 3:orbit_idx * 6 + 6, :]

    def get_pos_lvlh(self) -> tuple[np.ndarray, np.ndarray]:
        """
        """
        _, r_target = self.get_full_positions(0)
        _, v_target = self.get_full_velocities(0)
        t, r_chaser = self.get_full_positions(1)

        err_eci = r_target - r_chaser
        # Create unit vectors in radial, cross track, and in-track direction
        radial = r_target / np.linalg.norm(r_target, axis=0, keepdims=True)
        angular_momentum = np.cross(r_target, v_target, axis=0)
        cross_track = angular_momentum / np.linalg.norm(angular_momentum, axis=0, keepdims=True)
        # In track only aligns with velocity for circular orbits
        in_track = np.cross(cross_track, radial, axis=0)

        rotation = np.stack((radial, in_track, cross_track), axis=0)  # Should have (3,3,N) shape
        # Back to (3, N) shape
        err_lvlh = np.einsum('ijn,jn->in', rotation, err_eci)
        return t, err_lvlh

    def get_vel_lvlh(self) -> tuple[np.ndarray, np.ndarray]:
        """
        """
        _, r_target = self.get_full_positions(0)
        _, v_target = self.get_full_velocities(0)
        _, r_chaser = self.get_full_positions(1)
        t, v_chaser = self.get_full_velocities(1)

        r_diff_eci = r_target - r_chaser
        err_eci = v_chaser - v_target
        # Can this be done for 3 by N
        radial = r_target / np.linalg.norm(r_target, axis=0, keepdims=True)
        angular_momentum = np.cross(r_target, v_target, axis=0)
        cross_track = angular_momentum / np.linalg.norm(angular_momentum, axis=0, keepdims=True)
        # In track only aligns with velocity for circular orbits
        in_track = np.cross(cross_track, radial, axis=0)

        rotation = np.stack((radial, in_track, cross_track), axis=0)  # Should have (3,3,N) shape

        r_diff_lvlh = np.einsum('ijn,jn->in', rotation, r_diff_eci)
        # Compute angular velocity
        omega_eci = np.cross(r_target, v_target, axis=0) / np.sum(r_target ** 2, axis=0)
        omega_lvlh = np.einsum('ijn,jn->in', rotation, omega_eci)

        v_lvlh = np.einsum('ijn,jn->in', rotation, err_eci) - np.cross(omega_lvlh, r_diff_lvlh, axis=0)
        return t, v_lvlh

    def get_delta_v(self) -> tuple[np.ndarray, np.ndarray]:
        # Interpolate delta-v
        dv_t = list([0.0])
        dv_t.extend([impulse.time for impulse in self.impulse_results])
        dv_dv = list([0.0])
        dv_dv.extend(list(itertools.accumulate([abs(impulse.magnitude) for impulse in self.impulse_results])))
        dv_idx = np.searchsorted(dv_t, np.asarray(self.times), side="right") - 1
        dv_idx = np.clip(dv_idx, 0, None)
        dv = np.asarray(dv_dv)[dv_idx]
        return np.array(self.times), dv

    def get_attitude_rpy(self, attitude_idx: int = 0) -> tuple[np.ndarray, np.ndarray]:
        start_state_idx = attitude_idx * AttitudeDynamics.STATE_LENGTH + len(self.orbits) * OrbitDynamics.STATE_LEN
        end_state_idx = start_state_idx + 4
        rpy = np.zeros((3, len(self.times)))
        for idx in range(0, len(self.times)):
            rpy[:, idx] = quaternion_to_rpy(self.states[start_state_idx:end_state_idx, idx])

        return np.array(self.times), rpy
