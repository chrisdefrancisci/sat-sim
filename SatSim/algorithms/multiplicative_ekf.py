from collections.abc import Callable
from dataclasses import dataclass
import numpy as np
from typing import Sequence

from SatSim.common.attitude_matrix import attitude_matrix
from SatSim.common.quaternion import cross_prod_matrix, Quaternion

@dataclass(frozen=True, slots=True)
class AttitudeObservationVec:
    """
    Holds the two vectors and variance used to form an attitude observation.
    """

    body: np.ndarray
    r"""Body frame vector, :math:`\vector{b}`"""
    
    reference: np.ndarray
    r"""Reference frame vector, :math:`\vector{r}`"""

    variance: np.floating
    r"""Measurment variance, :math:`\sigma^2`"""

    def __post_init__(self):
        # frozen=True means we must use object.__setattr__ to normalize
        object.__setattr__(self, "measurement", np.asarray(self.body, dtype=float).reshape((3,1)))
        object.__setattr__(self, "reference",   np.asarray(self.reference,   dtype=float).reshape((3,1)))
        if not self.variance > 0:
            raise ValueError(f"variance must be positive, got {self.variance}")

@dataclass(frozen=True, slots=True)
class AttitudeObservationQuat:
    """ TODO: See Markley & Crassidis Eq 6.21, 6.22 for how this changes the MEKF. """
    pass


class GyroCalibrationMekf:
    r"""
    :see also: Markley & Crassidis, page 250, Table 6.1
    """
    def __init__(self):
        pass

class MissionModeMekf:
    r"""
    The Multiplicative Extended Kalman Filter (MEKF) estimates attitude and gyro biases.

    :see also: Markley & Crassidis, page 257, Table 6.3
    :param dt: The evaluation period (s) of the filter, :math:`\Delta t`
    :param var_ang_vel: The variance / spectral density of of the angular momentum noise.

        The angular momentum is given by:

        .. math::
            \vector{\omega} = \vector{\omega}^{true} + \vector{\beta}^{true} + \vector{\eta}_v

        and the spectral density of :math:`\vector{\eta}_v` is :math:`\sigma_v^2 I_3`.
    :param var_bias_walk: The variance / spectral density of the change in bias over time.

        The bias is given by:

        .. math::
            \dot{\vector{\beta}}^{true} = \vector{\eta}_u

        and the spectral density of :math:`\vector{\eta}_u` is :math:`\sigma_u^2 I_3`.
    """

    def __init__(self, dt:np.floating, var_ang_vel: np.floating, var_bias_walk: np.floating):
        self.dt = dt
        r"""Filter evaluation period, :math:`\Delta t`"""

        self.process_noise = MissionModeMekf._process_noise_approx(dt, var_ang_vel, var_bias_walk)
        r"""Function to return process noise :math:`Q_k` given :math:`\Delta t`"""

        self.attitude_est = Quaternion.eye()
        """Global attitude estimation"""

        self.gyro_bias_est = np.zeros((3,1))
        """Global bias estimation"""

        self.covariance = np.eye(6)
        """EKF Covariance, :math:`P`"""

        self.state = np.zeros((6,1))
        r"""
        This is the actual state vector

        .. math::
            \Delta\vector{x} =
                \begin{bmatrix}
                    \delta \vartheta
                    \Delta \beta
                \end{bmatrix}
        """

    def _compute_sensitivity_matrix(self, reference: np.ndarray) -> np.ndarray:
        a_mat = attitude_matrix(self.attitude_est)
        r_cross = cross_prod_matrix(reference)
        return np.hstack((a_mat @ r_cross, np.zeros((3, 3))))

    def _compute_kalman_gain(self, reference: np.ndarray, var: np.floating) -> np.ndarray:
        P = self.covariance # prior
        H = self._compute_sensitivity_matrix(reference)
        sigma = var
        # Innovation/residual covariance
        S = H @ P @ H.T + sigma * np.eye(3)
        K = P @ H @ np.linalg.inv(S)
        return K

    def _update_single(self, measurement: AttitudeObservationVec):
        r"""
        Computes the standard Kalman Filter update step for a single measurement

        :see also: Markley & Crassidis, Fig 6.2, pg 261 describes this approach as "Murrell's Version"        
        :param measurement: Measurment in the body frame
        :param reference: Measurement in the reference (inertial) frame
        :param variance: Measurement variance
        """
        b = measurement.body
        r = measurement.reference
        sigma = measurement.variance
        
        K = self._compute_kalman_gain(r, sigma)
        H = self._compute_sensitivity_matrix(r)
        # Calculate new covariance matrix
        P = self.covariance # prior
        I = np.eye(3)
        self.covariance = (I - K @ H) @ P # post
        # Calculate new state
        eps = b - attitude_matrix(self.attitude_est) @ r # residual
        dx_prior = self.state
        dx_post = dx_prior + K @(eps - H @ dx_prior)
        self.state = dx_post     


    def _update(self, observations: Sequence[AttitudeObservationVec] | AttitudeObservationVec):
        """
        Entry point to the Kalman Filter's update step. Iterates over multiple observations.
        
        :param observations: Attitude Observation
        """
        if isinstance(observations, AttitudeObservationVec):
            observations = [observations]
        for obs in observations:
            self._update_single(obs)

    def _reset(self):
        r"""
        Executes the reset step of the MEKF.

        Sets the KF rotation state, :math:`\Delta \vartheta`, to 0. 
        """
        q_prior = self.attitude_est
        theta = Quaternion.eye()
        theta.vector = self.state[0:3, :] / 2 # attitude error
        theta.scalar = 1.0

        q_unnorm = Quaternion.cross(theta, q_prior)
        self.attitude_est = Quaternion.norm(q_unnorm) # q_post

        self.state[0:3, :] = 0

    def _propagate(self, ang_vel: np.ndarray):
        r"""

        
        .. math::
            \begin{aligned}
                \hat{\vector{x}}_{k+1}^- &= \Phi_k \hat{\vector{x}}_k^+ + \Gamma_k \vector{u}_k \\
            \end{aligned}

        Where :math:`\Phi` is given by the following equation:
                            
        .. math::
            \begin{aligned}
                \Phi &= \begin{bmatrix} 
                        \Phi_{11} & \Phi_{12} \\ 
                        \Phi_{21} & \Phi_{22} \\
                    \end{bmatrix} \\
                % No whitespace with sphinx 
                %
                \Phi_{11} &= I_3 - [\hat{\vector{\omega}} \times] 
                    \frac{sin(\| \hat{\vector{\omega}} \| \Delta t}{\| \hat{\vector{\omega}} \|}
                    + [\hat{\vector{\omega}} \times]^2 \frac{1 - cos(\| \hat{\vector{\omega}} \| \Delta t}{\| \hat{\vector{\omega}} \|^2} \\
                %
                \Phi_{11} &= [\hat{\vector{\omega}} \times] 
                    \frac{1 - cos(\| \hat{\vector{\omega}} \| \Delta t}{\| \hat{\vector{\omega}} \|^2}
                    - I_3 \Delta t
                    - [\hat{\vector{\omega}} \times]^2 \frac{\| \hat{\vector{\omega}} \| \Delta t - sin(\| \hat{\vector{\omega}} \| \Delta t)}{\| \hat{\vector{\omega}} \|^3} \\
                %
                \Phi_{21} &= 0_{3 \times 3} \\
                %
                \Phi_{22} &= I_3 \\
            \end{aligned}
        
        :see also: Markley & Cassidis, Eq 6.83, pg 258; Eq. E.128, pg 465
        :param ang_vel: Angular velocity measurement :math:`\omega`, assuming a highly accurate IMU.
        """
        est_ang_vel = ang_vel - self.gyro_bias_est
        om = est_ang_vel # hat omega
        om_norm = np.linalg.norm(om)
        om_cross = cross_prod_matrix(om)
        i3 = np.eye(3)

        dt = self.dt

        sin_ = np.sin(om_norm * dt)
        cos_ = np.cos(om_norm * dt)

        phi = np.zeros((6, 6))
        p11 = phi[0:3, 0:3]
        p12 = phi[0:3, 3:6]
        p21 = phi[3:6, 0:3]
        p22 = phi[3:6, 3:6]

        p11[:,:] = i3 - om_cross * sin_ / om_norm + om_cross @ om_cross * (1 - cos_) / om_norm **2
        p12[:,:] = om_cross * (1 - cos_) / om_norm ** 2 - i3 * dt - om_cross @ om_cross * (1 - sin_) / om_norm ** 3
        p21[:,:] = np.zeros((3, 3))
        p22[:,:] = np.eye(3)

        self.state = phi @ self.state
        self.covariance = phi @ self.covariance @ phi + self.process_noise

    @staticmethod
    def _process_noise_approx(dt: np.floating, var_ang_vel: np.floating, var_bias_walk: np.floating) -> np.ndarray:
        r"""
        Docstring for process_noise_approx
        
        :see also: Markley & Crassidis, Eq 6.93, pg 260
        :param dt: Description
        :param var_drift: Description
        :param var_bias: Description
        :return: Description
        """
        var_v = var_ang_vel
        var_u = var_bias_walk
        Q = np.zeros((6, 6))
        Q[0:3, 0:3] = (var_v * dt + var_u * dt ** 2 / 3) * np.eye(3)
        Q[0:3, 3:6] = -(var_u * dt ** 2 / 2) * np.eye(3)
        Q[3:6, 0:3] = -(var_u * dt ** 2 / 2) * np.eye(3)
        Q[3:6, 3:6] = (var_u * dt) * np.eye(3)
        return Q
    
    def initialize(self, attitude:Quaternion, gyro_bias:np.ndarray, covariance:np.ndarray) -> None:
        r"""
        Initialize the filter.

        .. math::
            \begin{aligned}
                \hat{\vector{q}}(t_0) &= \hat{\vector{q}}_0 \\
                \hat{\vector{\beta}}(t_0) &= \hat{\vector{\beta}}_0 \\
                P(t_0) &= P_0 \\
                \Delta \hat{\vector{x}}_k^- &= \vector{0}
            \end{aligned}

        :param attitude:
        :param gyro_bias:
        :param covariance:
        """
        self.attitude_est = attitude
        self.gyro_bias_est = gyro_bias
        self.covariance = covariance
        self.state = np.zeros((6,1))

    def run(self, ang_vel: np.ndarray, observations: Sequence[AttitudeObservationVec] | AttitudeObservationVec):
        r"""
        Entry point for evaluating the Kalman Filter.

        Propagates across :math:`\Delta t`, updates from all observations, and "resets" - moving information from the filter state to the global attitude state.
        
        :param ang_vel: The measured angular velocity, :math:`\vector{\omega}`. Used directly (with estimate of bias) in propagation step.
        :param observations: Attitude observations, used in the update step.
        """
        self._propagate(ang_vel)
        self._update(observations)
        self._reset()