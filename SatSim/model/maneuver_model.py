from dataclasses import dataclass
import numpy as np

from SatSim.common import earth
from SatSim.common.conversions import rotation_matrix


@dataclass(frozen=True)
class ImpulseConfig:
    time: float
    r"""
    Time from previous impulse or maneuver.
    """

    delta_v: float
    r"""
    Impulsive maneuver with :math:`\Delta v`. Positive means the burn is in the direction of velocity, 
    negative means the burn is opposite direction of velocity.
    """


@dataclass(frozen=True)
class OrbitConfig:
    r"""
    Keplerian orbit elements.

    :see also: Vallado, Algorithm 9 RV2COE and Algorithm 10 COE2RV, pages 115-121
    """
    semimajor: float
    r"""Semimajor axis of the orbit, :math:`a` (km)."""
    eccentricity: float
    r"""Eccentricity of the orbit, :math:`e`."""
    inclination: float
    r"""Inclination of the orbit, :math:`i` (deg)."""
    node: float
    r"""Right ascension of the ascending node orbit, :math:`\Omega` (deg)."""
    arg_perigee: float
    r"""Argument of perigee of the orbit, :math:`\omega` (deg)."""
    true_anomaly: float
    r"""True anomaly of the orbit, :math:`\nu` (deg)."""

    @property
    def radius(self) -> float:
        """
        Helper to ensure circular orbit.
        
        :return: Radius of the circular orbit, :math:`r` (km)
        """
        if self.eccentricity != 0.0:
            raise ValueError(f"Orbit has eccentricity: {self.eccentricity}")
        return self.semimajor

    @property
    def period(self) -> float:
        r"""
        Calculates the period of the orbit using Kepler's third law.

        .. math:: P = 2\pi \sqrt{\frac{a^3}{\mu}}

        :see also: Vallado, Eq 1-26, pg 30
        :return: Period, :math:`s`
        """
        return 2 * np.pi * np.sqrt(self.semimajor ** 3 / earth.mu)

    @staticmethod
    def from_circular_eq(radius: float, true_longitude: float) -> 'OrbitConfig':
        r"""
        Factory function to create orbital elements from a circular equatorial orbit.

        :param radius: Radius of the circular orbit, :math:`r` (km).
        :param true_longitude: True longitude of the circular orbit, :math:`\lambda_{true}` (deg).
        :return: Imprecise OrbitElements that can be used for numerical computations.
        """
        return OrbitConfig(
            semimajor=radius,
            eccentricity=0,
            inclination=0,
            node=0,
            arg_perigee=0,
            true_anomaly=true_longitude,
        )

    @staticmethod
    def from_circular_inc(radius: float, inclination: float, node: float, arg_latitude: float) -> 'OrbitConfig':
        r"""
        Factory function to create orbital elements from a circular inclined orbit.

        :param radius: Radius of the circular orbit, :math:`r` (km).
        :param inclination: Inclination of the orbit, :math:`i` (deg).
        :param node: Right ascension of the ascending node orbit, :math:`\Omega` (deg).
        :param arg_latitude: Argument of latitude of the circular orbit, :math:`u` (deg).
        :return: Imprecise OrbitElements that can be used for numerical computations.
        """
        return OrbitConfig(
            semimajor=radius,
            eccentricity=0,
            inclination=inclination,
            node=node,
            arg_perigee=0,
            true_anomaly=arg_latitude
        )

    @staticmethod
    def from_elliptical_eq(semimajor: float, eccentricity: float, long_periapsis: float,
                           true_anomaly: float) -> 'OrbitConfig':
        r"""
        Factory function to create orbital elements from a elliptical equatorial orbit.

        :param semimajor: Semimajor axis of the elliptical orbit, :math:`a` (km).
        :param eccentricity: Eccentricity of the elliptical orbit, :math:`e`.
        :param long_periapsis: Longitude of periapsis, :math:`\tilde{\omega}` (deg).
        :param true_anomaly: True anomaly of the orbit, :math:`\nu` (deg).

        :return: Imprecise OrbitElements that can be used for numerical computations.
        """
        return OrbitConfig(
            semimajor=semimajor,
            eccentricity=eccentricity,
            inclination=0,
            node=0,
            arg_perigee=long_periapsis,
            true_anomaly=true_anomaly
        )

    @staticmethod
    def from_pos_vel(pos_vec: np.ndarray, vel_vec:np.ndarray) -> 'OrbitConfig':
        r"""
        Factory function to create orbital elements from position and velocity vectors in ECI frame.

        :see also: Vallado, Algorithm 9, page 115
        :param pos_vec:
        :param vel_vec:
        :return: Orbital Elements
        """
        def float_eq(val1, val2) -> bool:
            TOLERANCE = 1e-9 # TODO determine if this is good or not
            return abs(val1 - val2) < TOLERANCE

        pos = np.linalg.norm(pos_vec)
        vel = np.linalg.norm(vel_vec)

        angular_momentum_vec = np.cross(pos_vec.flatten(), vel_vec.flatten()) # "h"
        angular_momentum = np.linalg.norm(angular_momentum_vec)
        k_hat = np.array([0, 0, 1]) # Unit vector in K direction
        eccentricity_vec = 1/earth.mu * ((vel ** 2 - earth.mu / pos) * pos_vec - (pos_vec @ vel_vec) * vel_vec)
        eccentricity = np.linalg.norm(eccentricity_vec)

        if float_eq(eccentricity, 1.0):
            raise ValueError("Parabolic orbits not yet suppported.")

        node_vec = np.cross(k_hat, angular_momentum_vec)
        node_norm = np.linalg.norm(node_vec)
        # cos(Omega) = n_I / |n|
        raan = np.rad2deg(np.arccos(node_vec[0]/np.linalg.norm(node_vec)))
        raan = 360 - raan if node_vec[1] < 0 else raan

        mech_energy = vel**2 / 2 - earth.mu / pos
        semimajor = -earth.mu / (2 * mech_energy)

        # cos(i) = h_K / |h|
        inclination = np.rad2deg(np.arccos(angular_momentum_vec[2] / angular_momentum))

        # cos(nu) = e / |e| dot r / |r|, may not apply
        true_anomaly = np.rad2deg(np.arccos(np.dot(eccentricity_vec, pos_vec) / (eccentricity * pos)))
        true_anomaly = 360 - true_anomaly if np.dot(pos_vec, vel_vec) < 0 else true_anomaly

        # Handle special cases first: circular equitorial, circular inclined, elliptic equitorial
        if float_eq(eccentricity, 0.0) and float_eq(inclination, 0.0):
            # cos(lambda) = r_I / |r|
            true_longitude = np.rad2deg(np.arccos(pos_vec[0] / pos))
            true_longitude = 360 - true_longitude if pos_vec[1] < 0 else true_longitude
            return OrbitConfig.from_circular_eq(
                radius = semimajor,
                true_longitude=true_longitude
            )
        elif float_eq(eccentricity, 0.0):
            # cos(u) = n / |n| dot r / |r|
            arg_latitude = np.rad2deg(np.arccos(np.dot(node_vec, pos_vec) / (node_norm * pos)))
            arg_latitude = 360 - arg_latitude if pos_vec[2] < 0 else arg_latitude
            return OrbitConfig.from_circular_inc(
                radius = semimajor,
                inclination=inclination,
                node=raan,
                arg_latitude=arg_latitude
            )
        elif float_eq(inclination, 0.0):
            # cos(omega) = e_I / |e|
            long_periapsis = np.rad2deg(np.arccos(eccentricity_vec[0] / eccentricity))
            long_periapsis = 360 - long_periapsis if eccentricity_vec[1] < 0 else long_periapsis
            return OrbitConfig.from_elliptical_eq(
                semimajor=semimajor,
                eccentricity=eccentricity,
                long_periapsis=long_periapsis,
                true_anomaly=true_anomaly
            )

        # cos(omega) = n / |n| dot e / |e|
        arg_perigee = np.rad2deg(np.arccos(np.dot(node_vec, eccentricity_vec) / (node_norm * eccentricity)))
        arg_perigee = 360 - arg_perigee if eccentricity_vec[2] < 0 else arg_perigee

        return OrbitConfig(
            semimajor=semimajor,
            eccentricity=eccentricity,
            inclination=inclination,
            node=raan,
            arg_perigee=arg_perigee,
            true_anomaly=true_anomaly
        )

    def to_position(self) -> np.ndarray:
        r"""

        :return: Position in earth-centered coordinates.
        """
        p = self.semimajor * (1 - self.eccentricity ** 2)  # Vallado, Eq. 1-10, pg 17
        nu = np.deg2rad(self.true_anomaly)
        e = self.eccentricity
        pos_perifocal = np.array([[p * np.cos(nu) / (1 + e * np.cos(nu))],
                                  [p * np.sin(nu) / (1 + e * np.cos(nu))],
                                  [0]])
        raan = np.deg2rad(self.node)  # right ascension of ascending node
        i = np.deg2rad(self.inclination)
        omega = np.deg2rad(self.arg_perigee)
        pos_earth_centered = rotation_matrix(2, -raan) @ rotation_matrix(0, -i) @ rotation_matrix(2,
                                                                                                  -omega) @ pos_perifocal
        return pos_earth_centered

    def to_velocity(self) -> np.ndarray:
        r"""

        :return: Velocity in earth-centered coordinates.
        """
        p = self.semimajor * (1 - self.eccentricity ** 2)  # Vallado, Eq. 1-10, pg 17
        nu = np.deg2rad(self.true_anomaly)
        e = self.eccentricity
        vel_perifocal = np.array([[-np.sqrt(earth.mu / p) * np.sin(nu)],
                                  [np.sqrt(earth.mu / p) * (e + np.cos(nu))],
                                  [0]])
        raan = np.deg2rad(self.node)  # right ascension of ascending node
        i = np.deg2rad(self.inclination)
        omega = np.deg2rad(self.arg_perigee)
        vel_earth_centered = rotation_matrix(2, -raan) @ rotation_matrix(0, -i) @ rotation_matrix(2,
                                                                                                  -omega) @ vel_perifocal
        return vel_earth_centered


@dataclass(frozen=True)
class SimConfig:
    target_orbit: OrbitConfig
    interceptor_orbit: OrbitConfig
    maneuvers: list[ImpulseConfig]
