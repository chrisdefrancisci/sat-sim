import numpy as np

from SatSim.common.quaternion import skew_symmetric, Quaternion

def MoiTensorCube(mass, length) -> np.ndarray:
    r"""
    Returns the moment of inertia tensor for a cube with axis of rotation through the middle of the faces, parallel to the edges.

    :see also: https://en.wikipedia.org/wiki/List_of_moments_of_inertia#List_of_3D_inertia_tensors
    """
    return np.eye(3) * 1/6 * mass * length **2

class AttitudeDynamics:
    STATE_LENGTH = 7
    def __init__(self, q: Quaternion, ang_vel: np.ndarray, moi_tensor: np.ndarray):
        self.attitude = q
        self.ang_vel = ang_vel
        self.moi_tensor = moi_tensor

    @staticmethod
    def dynamics(t, state:np.ndarray, moi_tensor: np.ndarray, torque: np.ndarray = np.zeros((3,1))) -> np.ndarray:
        attitude = Quaternion(state[:4])
        ang_vel = np.reshape(state[4:], (3,1))
        d_attitude = 0.5 * Quaternion.cross(ang_vel, attitude)
        inv_moi = np.linalg.inv(moi_tensor)
        cross_ang_vel = skew_symmetric(ang_vel)
        d_ang_vel = inv_moi @ (torque - cross_ang_vel @ moi_tensor @ ang_vel)
        return np.concatenate((d_attitude._q.flatten(), d_ang_vel.flatten()))

    def initial_state(self) -> np.ndarray:
        return np.concatenate((self.attitude._q.flatten(), self.ang_vel.flatten()))