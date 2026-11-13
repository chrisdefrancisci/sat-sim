import numpy as np

from SatSim.common.quaternion import Quaternion
from SatSim.common.attitude_matrix import attitude_matrix
from SatSim.algorithms.multiplicative_ekf import AttitudeObservationVec

class StarTracker:
    """
    Simple simulation of a star tracker.

    :param range: The min (inclusive), max (exclusive) number of potential visible stars.
    :param variance: The noise applied to the measurement (arcsec^2).
    :param field_of_view: The available field of view of the star tracker.
    :param orientation: The orientation (in the body frame) of the star tracker
    """
    def __init__(self, range:tuple[int, int], variance: float|np.floating, field_of_view:np.floating = np.float64(10), orientation:np.ndarray = np.array([1, 0, 0])):
        self.range = range
        self.variance = variance * (np.pi / (180 * 3600)) ** 2 # convert arcsec to radian
        
        
        self.stddev = np.sqrt(self.variance)
        self.fov = np.deg2rad(field_of_view)
        self.orientation = orientation / np.linalg.norm(orientation)
        self.rng = np.random.default_rng()
        
    def _creat_meas(self, a_matrix_inv: np.ndarray) -> AttitudeObservationVec:
        """
        Generates a random unit vector in the inertial frame and produces a body frame measurement from it.
        
        The nth measurement from the star tracker can be defined as:

        ..math::
            \vector{y}_k^{(n)} = A(\vector{q}^{true}) \vector{r}_n + \nu_n

        The measurement is within the field of view of the orientation vector.

        :see also: Markley & Crassidis, Eq. 6.48a, pg 249
        :param attitude_matrx: Attitude matrix, :math:`A(\vector{q}^{true})`
        :return: Measurement, :math:`\vector{y}_k^{(n)}`.
        """
        orientation = self.orientation
        rng = self.rng

        # Pick a random unit vector orthogonal to the orientation
        # This vector and the orientation vector define the plane around the orientation vector that the measurement vector will be in
        v = rng.standard_normal(len(orientation))
        v_ortho = v - np.dot(v, orientation) * orientation
        v_ortho /= np.linalg.norm(v_ortho)
        # Sample uniform cos(theta) for uniform solid angle in 3D
        # This sets the angle to the orientation, within the above plane
        cos_theta = rng.uniform(np.cos(self.fov), 1.0)
        sin_theta = np.sqrt(1.0 - cos_theta**2)
        # Combine components
        meas_body_true = cos_theta * orientation + sin_theta * v_ortho
        meas_body_true /= np.linalg.norm(meas_body_true)

        meas_ref = a_matrix_inv @ meas_body_true
        meas_ref /= np.linalg.norm(meas_ref)

        # Project the noise onto the plane perpendicular to the measurement 
        # (Noise only has 2 degrees of freedom here, since the vector must be normalized)
        noise = rng.standard_normal(3) * self.stddev
        noise -= np.dot(noise, meas_body_true) * meas_body_true
        meas_body = meas_body_true + noise
        meas_body /= np.linalg.norm(meas_body)

        return AttitudeObservationVec(meas_body, meas_ref, self.variance)

    def run(self, attitude_true: Quaternion) -> list[AttitudeObservationVec]:
        """
        Docstring for run
        
        :param true: Attitude body orientation
        :return: List containing a random number of observations.
        """
        rng = np.random.default_rng()
        n_meas = rng.integers(*self.range)

        meas = []
        att_inv = attitude_matrix(attitude_true).T # Inverse of Direction Cosine Matrix is its transpose
        for _ in range(n_meas):
            meas.append(self._creat_meas(att_inv))
        return meas
