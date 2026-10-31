import numpy as np

from SatSim.common.quaternion import skew_symmetric, Quaternion

def _validate(q: np.ndarray | Quaternion) -> Quaternion:
    if isinstance(q, np.ndarray):
        if np.shape(q) not in {(4,), (4,1)}:
            raise ValueError(f"Input vector must have first dimension 4, but has shape {np.shape(q)}")
        return Quaternion(q)
    return q

def attitude_matrix(q: np.ndarray | Quaternion) -> np.ndarray:
    r"""
    Constructs the attitude matrix from a quaternion

    :see also: Markley & Cassidis, Eq. 2.124, pg 45
    :param q: Description
    :returns: Attitude Matrix, :math:`A`
    """    
    q = _validate(q)
    vector = q.vector
    scalar = q.scalar.item()
    return ((scalar ** 2 - vector.T @ vector) * np.eye(3) 
            - 2 * scalar * skew_symmetric(vector)
            + 2 * vector @ vector.T)

def quaternion_to_rpy(q: np.ndarray | Quaternion) -> np.ndarray:
    r"""
    Converts a quaternion to roll-pitch-yaw.

    For attitude matrix :math:`A_{321}`, the roll is index 1, pitch is index 2, and yaw is index 3.
    
    :see also: Markley & Cassidis, Eqs 2.171-2.174, pgs 57-58
    :param q: Description
    :return: Roll (:math:`\psi`), pitch (:math:`\theta`), yaw (:math:`\phi`)
    """
    att = attitude_matrix(q)
    pitch = np.asin(-att[0, 2]) # pitch = theta

    sign = np.sign(np.cos(pitch))
    if (sign != 0):
        yaw = np.atan2(sign * att[0, 1], sign * att[0, 0]) # yaw = phi
        roll = np.atan2(sign * att[1, 2], sign * att[2, 2]) # roll = psi
        return np.array([roll, pitch, yaw])
    # gimal lock case
    # can compute eiether yaw or roll as above
    roll = np.atan2(att[1, 2], att[2, 2]) # roll = psi
    if att[0, 2] >= 0:
        yaw = -roll + np.atan2(
            -att[2,1]-att[1,0], att[1,1] - att[2,0]
        )
    else:
        yaw = roll + np.atan2(
            att[2,1]-att[1,0], att[1,1] + att[2,0]
        )
    return np.array([roll, pitch, yaw])
