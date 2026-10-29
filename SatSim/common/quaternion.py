"""
Implements quaternion operations using definitions from Crassidis and Markley.
"""
import numpy as np

def skew_symmetric(v: np.ndarray) -> np.ndarray:
    r"""
    Docstring for omega_matrix
    
    :param v: Description
    :return: Description
    """
    if np.shape(v) not in {(3,), (3,1)}:
        raise ValueError(f"Input vector must have first dimension 4, but has shape {np.shape(v)}")
    x, y, z = v.flatten()
    return np.array([
        [0, -z,  y],
        [z,  0, -x],
        [-y, x,  0]
    ])

def omega_matrix(v: np.ndarray) -> np.ndarray:
    r"""
    Docstring for omega_matrix
    
    :param v: Description
    :return: Description
    """
    if np.shape(v) not in {(3,), (3,1)}:
        raise ValueError(f"Input vector must have first dimension 4, but has shape {np.shape(v)}")
    omega = np.zeros((4, 4))
    omega[0:3, 0:3] = -skew_symmetric(v)
    omega[0:3, 3] = v.flatten()
    omega[3, 0:3] = -v.T
    return omega

def gamma_matrix(v: np.ndarray) -> np.ndarray:
    r"""
    Docstring for gamma_matrix
    
    :param v: Description
    :return: Description
    """
    if np.shape(v) not in {(3,), (3,1)}:
        raise ValueError(f"Input vector must have first dimension 4, but has shape {np.shape(v)}")
    gamma = np.zeros((4, 4))
    gamma[0:3, 0:3] = skew_symmetric(v)
    gamma[0:3, 3] = v.flatten()
    gamma[3, 0:3] = -v.T
    return gamma


class Quaternion:
    r"""
    A class for quaternion operations.

    The quaternion is defined as
    ..math::
        \mathbf{q} = 
            \begin{bmatrix}
                \mathbf{q}_{1:3} \\
                q_4
            \end{bmatrix}

    where :math:`\mathbf{q}_{1:3}` is the vector component of the quaternion and :math:`q_{4}` is the scalar. 
    """
    def __init__(self, q: np.ndarray):
        if np.shape(q) not in {(4,), (4,1), (3,), (3,1)}:
            raise ValueError(f"Input vector must have first dimension 4, but has shape {np.shape(q)}")

        self._q = np.zeros((4,1))
        self._q[:len(q)] = np.atleast_2d(q).reshape(-1, 1)

    def __getitem__(self, key) -> np.ndarray:
        return self._q[key]

    def __setitem__(self, key, value):
        self._q[key] = value

    def __str__(self) -> str:
        return f"{self._q}"

    def __repr__(self) -> str:
        return f"{self._q}"

    def __mul__(self, other: float|np.floating):
        return Quaternion(self._q * other)

    def __rmul__(self, other: float|np.floating):
        return self.__mul__(other)

    def __rmatmul__(self, other: np.ndarray):
        q_new = other @ self._q
        return Quaternion(q_new)

    def __truediv__(self, other: float|np.floating):
        self._q = self._q / other

    @property
    def vector(self) -> np.ndarray:
        return self._q[0:3,:]

    @vector.setter
    def vector(self, other):
        self._q[0:3, :] = other

    @property
    def scalar(self) -> np.ndarray:
        return np.atleast_2d(self._q[3,:])

    @scalar.setter
    def scalar(self, other):
        self._q[3, :] = other

    def angle(self) -> float:
        return 2 * np.arccos(np.abs(self.scalar.item()))

    def conj(self) -> 'Quaternion':
        return Quaternion(np.concatenate((-self.vector, self.scalar)))

    @property
    def psi_matrix(self) -> np.ndarray:
        q = self._q.flatten()
        return np.array([
            [q[3], q[2], -q[1]],
            [-q[2], q[3], q[0]],
            [q[1], -q[0], q[3]],
            [-q[0], -q[1], -q[2]],
            ])

    @property
    def xi_matrix(self) -> np.ndarray:
        q = self._q.flatten()
        return np.array([
            [q[3], -q[2], q[1]],
            [q[2], q[3], -q[0]],
            [-q[1], q[0], q[3]],
            [-q[0], -q[1], -q[2]],
            ])

    @property
    def cross_matrix(self) -> np.ndarray:
        return np.concatenate((self.psi_matrix, self._q), axis=1) 
    
    @property
    def dot_matrix(self) -> np.ndarray:
        return np.concatenate((self.xi_matrix, self._q), axis=1)

    @classmethod
    def cross(cls, first: 'Quaternion|np.ndarray', second:'Quaternion|np.ndarray') -> 'Quaternion':
        r"""
        :see also: Markley & Crassidis, Eqs. A.8a and A21.a, pg 347 and 349
        """
        if isinstance(first, Quaternion) and isinstance(second, Quaternion):
            # q x q
            return Quaternion(first.cross_matrix @ second._q)
        elif isinstance (first, np.ndarray) and isinstance(second, Quaternion):
            # vector x q
            return Quaternion(Quaternion(first).cross_matrix @ second._q)
        elif isinstance (first, Quaternion) and isinstance(second, np.ndarray):
            # q x vector
            return Quaternion(first.cross_matrix @ Quaternion(second)._q)
        else:
            raise ValueError("One of the arguments should be a Quaternion")

    @classmethod
    def dot(cls, first: 'Quaternion|np.ndarray', second:'Quaternion|np.ndarray') -> 'Quaternion':
        r"""
        :see also: Markley & Crassidis, Eqs. A.8b and A21.b, pgs 347 and 349
        """
        if isinstance(first, Quaternion) and isinstance(second, Quaternion):
            # q . q
            return Quaternion(first.dot_matrix @ second._q)
        elif isinstance (first, np.ndarray) and isinstance(second, Quaternion):
            # vector . q
            return Quaternion(Quaternion(first).dot_matrix @ second._q)
        elif isinstance (first, Quaternion) and isinstance(second, np.ndarray):
            # q . vector
            return Quaternion(first.dot_matrix @ Quaternion(second)._q)
        else:
            raise ValueError("One of the arguments should be a Quaternion")

    @classmethod
    def eye(cls) -> 'Quaternion':
        r"""
        Creates the identity quaternion.
        """
        return Quaternion(np.array([0,0,0,1]))