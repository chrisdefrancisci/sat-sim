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
    chaser_orbit: OrbitConfig
    maneuvers: list[ImpulseConfig]
