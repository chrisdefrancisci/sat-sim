from dataclasses import dataclass
import numpy as np

from SatSim.constants import earth


@dataclass(frozen=True)
class ImpulseConfig:
    time: float
    r"""
    Time from previous impulse or maneuver.
    """

    delta_v: float
    r"""
    Impulsive maneuver with ..math:`\Delta v`. Positive means the burn is in the direction of velocity, 
    negative means the burn is opposite direction of velocity.
    """

@dataclass(frozen=True)
class OrbitConfig:
    altitude_km: float
    inclination_deg: float
    eccentricity: float

    @property
    def rot(self) -> np.ndarray:
        inc = np.radians(self.inclination_deg)
        rot = np.array([
            [1, 0, 0],
            [0, np.cos(inc), -np.sin(inc)],
            [0, np.sin(inc), np.cos(inc)],
        ])
        return rot

    @property
    def semimajor(self) -> float:
        r"""
        Calculates the semimajor axis of the ellipse / radius of the circle
        :return: Semimajor axis of the ellipse, ..math`a` (km)
        """
        r_p = earth.radius + self.altitude_km
        semimajor = r_p / (1.0 - self.eccentricity)
        return semimajor

    @property
    def radius(self) -> float:
        """
        Helper to ensure circular orbit.
        
        :return: Radius of the circular orbit, ..math`r` (km)
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

    
@dataclass(frozen=True)
class SimConfig:
    target_orbit: OrbitConfig
    chaser_orbit: OrbitConfig
    maneuvers: list[ImpulseConfig]