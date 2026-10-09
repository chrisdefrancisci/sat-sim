from dataclasses import dataclass
import numpy as np

from SatSim.common import earth
from SatSim.model.maneuver_model import OrbitConfig


class OrbitModel:
    r""" Orbit model

    .. math::
        \ddot{\mathbf{r}} = -\frac{\mu}{|\mathbf{r}|^3}\mathbf{r}

    """

    def __init__(self, orbit_config: OrbitConfig):
        """


        :param altitude_km: Orbit altitude in km (above the earth's surface).
        :param inclination_deg:
        :param eccentricity:
        """
        self.config = orbit_config

    @staticmethod
    def dynamics(t, state: np.ndarray) -> np.ndarray:
        r"""Simulates orbit dynamics.

        For the state :math:`\mathbf{x} = \begin{bmatrix} \mathbf{r} \\ \mathbf{v} \end{bmatrix}`,
        returns :math:`\dot{\mathbf{x}} = \begin{bmatrix} \mathbf{v} \\ \dot{\mathbf{v}} \end{bmatrix}` using the
        the two-body equation. [Vallado, Eq 1-14, pg 23]

        .. math::
            \ddot{\mathbf{r}} = -\frac{\mu}{|\mathbf{r}|^3}\mathbf{r}


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

        Calculates the semimajor axis, :math:`a`, and initializes position and velocity to be at perigee.

        Uses the definition of eccentricity to convert between :math:`r_p` and :math:`a`.

        .. math::
            \begin{aligned}
                e &= \frac{c}{a} \\
                r_p &= a - c \\
                r_p &= a (1 - e)
            \end{aligned}

        Uses the vis-viva equation for to determine velocity at perigee.

        .. math::
            v^2 = \mu (\frac{2}{|r|} - \frac{1}{a})

        :see also: Vallado, Eq 1-2, pg 14; Eq 1-22, pg 27; Eq 1-30, pg 32
        :return: State in :math:`km`, :math:`\frac{km}{s}`.
            Note that this is a row vector for ease of use with :code:`solve_ivp`.
        """

        r_p = earth.radius + self.config.altitude_km

        # Pos, vel at perigee, lying along the x-axis before inclination tilt.
        v_p = np.sqrt(earth.mu * (2.0 / r_p - 1.0 / self.config.semimajor))  # vis-viva equation
        pos = np.array([r_p, 0.0, 0.0])
        vel = np.array([0.0, v_p, 0.0])

        # Tilt the whole orbital plane by the inclination about the x-axis,
        # so the orbit is a great circle (or ellipse) crossing the equator.
        pos = self.config.rot @ pos
        vel = self.config.rot @ vel
        return np.concatenate([pos, vel])
