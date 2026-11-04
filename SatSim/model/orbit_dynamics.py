import numpy as np

from SatSim.common import earth
from SatSim.model.orbit_model import OrbitModel


class OrbitDynamics:
    r""" Orbit model

    .. math::
        \ddot{\vector{r}} = -\frac{\mu}{|\vector{r}|^3}\vector{r}

    """

    STATE_LEN = 6

    def __init__(self, orbit_config: OrbitModel):
        """


        :param altitude_km: Orbit altitude in km (above the earth's surface).
        :param inclination_deg:
        :param eccentricity:
        """
        self.config = orbit_config

    @staticmethod
    def dynamics(t, state: np.ndarray) -> np.ndarray:
        r"""Simulates orbit dynamics.

        For the state :math:`\vector{x} = \begin{bmatrix} \vector{r} \\ \vector{v} \end{bmatrix}`,
        returns :math:`\dot{\vector{x}} = \begin{bmatrix} \vector{v} \\ \dot{\vector{v}} \end{bmatrix}` using the
        the two-body equation. [Vallado, Eq 1-14, pg 23]

        .. math::
            \ddot{\vector{r}} = -\frac{\mu}{|\vector{r}|^3}\vector{r}


        :see also: Vallado, Eq 1-14, pg 23
        :param t:
        :param state:
        :return: Derivative of state in :math:`\frac{km}{s}`, :math:`\frac{km}{s^2}`.
            Note that this is a row vector for ease of use with :code:`solve_ivp`.

        """
        pos = state[:3]
        vel = state[3:]
        pos_norm = np.linalg.norm(pos)
        accel = -earth.mu * pos / pos_norm ** 3
        return np.concatenate([vel, accel])

    def initial_state(self) -> np.ndarray:
        r"""
        Initial state of the orbit.

        :return: State in :math:`km`, :math:`\frac{km}{s}`.
            Note that this is a row vector for ease of use with :code:`solve_ivp`.
        """

        r = self.config.to_position()
        v = self.config.to_velocity()
        return np.concatenate((r, v)).flatten()
