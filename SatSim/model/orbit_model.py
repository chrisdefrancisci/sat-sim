import numpy as np

from SatSim.constants import earth


class OrbitModel:
    r""" Orbit model

    .. math::
        \ddot{\mathbf{r}} = -\frac{\mu}{|\mathbf{r}|^3}\mathbf{r}

    """

    def __init__(self, altitude_km=400.0, inclination_deg=51.6,
                 eccentricity=0.0):
        """


        :param altitude_km: Orbit altitude in km (above the earth's surface).
        :param inclination_deg:
        :param eccentricity:
        """
        self.altitude_km = altitude_km
        self.inclination_deg = inclination_deg
        self.eccentricity = eccentricity

        # Create rotation matrix
        inc = np.radians(self.inclination_deg)
        rot = np.array([
            [1, 0, 0],
            [0, np.cos(inc), -np.sin(inc)],
            [0, np.sin(inc), np.cos(inc)],
        ])
        self.rot = rot

    def get_params(self):
        return {'altitude_km': self.altitude_km, 'inclination_deg': self.inclination_deg,
                'eccentricity': self.eccentricity}

    def set_params(self, **kwargs):
        if 'altitude_km' in kwargs:
            self.altitude_km = kwargs['altitude_km']
        if 'inclination_deg' in kwargs:
            self.inclination_deg = kwargs['inclination_deg']
            inc = np.radians(self.inclination_deg)
            rot = np.array([
                [1, 0, 0],
                [0, np.cos(inc), -np.sin(inc)],
                [0, np.sin(inc), np.cos(inc)],
            ])
            self.rot = rot
        if 'eccentricity' in kwargs:
            self.eccentricity = kwargs['eccentricity']

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

        semimajor = earth.radius + self.altitude_km  # semimajor axis, a
        # Pos, vel at perigee, lying along the x-axis before inclination tilt.
        r_p = semimajor * (1.0 - self.eccentricity)
        v_p = np.sqrt(earth.mu * (2.0 / r_p - 1.0 / semimajor))  # vis-viva equation
        pos = np.array([r_p, 0.0, 0.0])
        vel = np.array([0.0, v_p, 0.0])

        # Tilt the whole orbital plane by the inclination about the x-axis,
        # so the orbit is a great circle (or ellipse) crossing the equator.
        pos = self.rot @ pos
        vel = self.rot @ vel
        return np.concatenate([pos, vel])

    def get_period(self) -> float:
        r"""
        Calculates the period of the orbit using Kepler's third law.

        .. math:: P = 2\pi \sqrt{\frac{a^3}{\mu}}

        :see also: Vallado, Eq 1-26, pg 30
        :return: Period, :math:`s`
        """
        semimajor = earth.radius + self.altitude_km  # semimajor axis, a
        return 2 * np.pi * np.sqrt(semimajor ** 3 / earth.mu)
