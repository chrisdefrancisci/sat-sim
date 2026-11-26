"""
Implements quaternion operations using definitions from Crassidis and Markley.
"""
import math
import numpy as np


def cross_prod_matrix(v: np.ndarray) -> np.ndarray:
    r"""
    Generates the skew-symmetric cross product-matrix for a vector
    
    The skew-symmetric cross-product matrix is defined as
    
    .. math::
        [\vector{v} \times] \equiv
        \begin{bmatrix}
             0   & -v_3  &  v_2 \\
             v_3 &  0    & -v_1 \\
            -v_2 &  v_1  &  0 \\
        \end{bmatrix}
    
    :see also: Markley & Crassidis, Eq A.1, pg 345
    :param v: Input vector.
    :return: Cross-product matrix, :math:`[\vector{v} \times]`
    """
    if np.shape(v) not in {(3,), (3, 1)}:
        raise ValueError(f"Input vector must have first dimension 4, but has shape {np.shape(v)}")
    x, y, z = v.flatten()
    return np.array([
        [0, -z, y],
        [z, 0, -x],
        [-y, x, 0]
    ])


def omega_matrix(v: np.ndarray) -> np.ndarray:
    r"""
    Docstring for omega_matrix
    
    :param v: Description
    :return: Description
    """
    if np.shape(v) not in {(3,), (3, 1)}:
        raise ValueError(f"Input vector must have first dimension 4, but has shape {np.shape(v)}")
    omega = np.zeros((4, 4))
    omega[0:3, 0:3] = -cross_prod_matrix(v)
    omega[0:3, 3] = v.flatten()
    omega[3, 0:3] = -v.T
    return omega


def gamma_matrix(v: np.ndarray) -> np.ndarray:
    r"""
    Docstring for gamma_matrix
    
    :param v: Description
    :return: Description
    """
    if np.shape(v) not in {(3,), (3, 1)}:
        raise ValueError(f"Input vector must have first dimension 4, but has shape {np.shape(v)}")
    gamma = np.zeros((4, 4))
    gamma[0:3, 0:3] = cross_prod_matrix(v)
    gamma[0:3, 3] = v.flatten()
    gamma[3, 0:3] = -v.T
    return gamma


class Quaternion:
    r"""
    A class for quaternion operations.

    The quaternion is defined as
    
    .. math::
        \vector{q} = 
            \begin{bmatrix}
                \vector{q}_{1:3} \\
                q_4
            \end{bmatrix}

    where :math:`\vector{q}_{1:3}` is the vector component of the quaternion and :math:`q_{4}` is the scalar. 
    """

    def __init__(self, q: np.ndarray):
        if np.shape(q) not in {(4,), (4, 1), (3,), (3, 1)}:
            raise ValueError(f"Input vector must have first dimension 4, but has shape {np.shape(q)}")

        self._q = np.zeros((4, 1))
        self._q[:len(q)] = np.atleast_2d(q).reshape(-1, 1)

    def __getitem__(self, key) -> np.ndarray:
        return self._q[key]

    def __setitem__(self, key, value):
        self._q[key] = value

    def __str__(self) -> str:
        entries = [f"{x:.4f}" for x in self._q.flatten()]
        width = max(len(e) for e in entries)
        v = [e.rjust(width) for e in entries[:3]]
        s = entries[3].rjust(width)

        return f"Quaternion([{v[0]}, {v[1]}, {v[2]} | {s}])"

    def __repr__(self) -> str:
        entries = [f"{x:.4f}" for x in self._q.flatten()]
        width = max(len(e) for e in entries)
        v = [e.rjust(width) for e in entries[:3]]
        s = entries[3].rjust(width)

        return (
            f"Quaternion(\n"
            f"  vector: [[{v[0]}],\n"
            f"           [{v[1]}],\n"
            f"           [{v[2]}]]\n"
            f"  scalar: [[{s}]])"
        )

    def __add__(self, other: 'Quaternion'):
        return Quaternion(self._q + other._q)

    def __sub__(self, other: 'Quaternion'):
        return Quaternion(self._q - other._q)

    def __mul__(self, other: float | np.floating):
        return Quaternion(self._q * other)

    def __rmul__(self, other: float | np.floating):
        return self.__mul__(other)

    def __rmatmul__(self, other: np.ndarray):
        q_new = other @ self._q
        return Quaternion(q_new)

    def __truediv__(self, other: float | np.floating) -> 'Quaternion':
        return Quaternion(self._q / other)

    def __array__(self, dtype=None, copy=None):
        return np.asarray(self._q, dtype=dtype)

    @property
    def vector(self) -> np.ndarray:
        return self._q[0:3, :]

    @vector.setter
    def vector(self, other):
        self._q[0:3, :] = other

    @property
    def scalar(self) -> np.ndarray:
        return np.atleast_2d(self._q[3, :])

    @scalar.setter
    def scalar(self, other):
        self._q[3, :] = other

    def angle(self) -> float:
        return 2 * math.acos(np.abs(self.scalar.item()))

    def conj(self) -> 'Quaternion':
        r"""
        Constructs the conjugate of the quaternion, :math:`\vector{q}^*`.

        .. math::
            \vector{q}^* \equiv \begin{bmatrix}
                -\vector{q}_{1:3} \\
                q_4
            \end{bmatrix}

        :see also: Markley & Crassidis, Eq. 2.91, pg 39
        :return: Conjugate of the quaternion
        """
        return Quaternion(np.concatenate((-self.vector, self.scalar)))

    def inv(self) -> 'Quaternion':
        r"""
        Constructs the inverse of the quaternion, :math:`\vector{q}^{-1}`.

        .. math::
            \vector{q}^{-1} \equiv \frac{\vector{q}^*}{\| \vector{q} \|}

        :see also: Markley & Crassidis, Eq. 2.95, pg 39
        :return: Inverse of the quaternion
        """
        return self.normalized(self.conj())

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
    def cross(cls, first: 'Quaternion|np.ndarray', second: 'Quaternion|np.ndarray') -> 'Quaternion':
        r"""
        .. math::
            \otimes

        :see also: Markley & Crassidis, Eqs. A.8a and A21.a, pg 347 and 349
        """
        if isinstance(first, Quaternion) and isinstance(second, Quaternion):
            # q x q
            return Quaternion(first.cross_matrix @ second._q)
        elif isinstance(first, np.ndarray) and isinstance(second, Quaternion):
            # vector x q
            return Quaternion(Quaternion(first).cross_matrix @ second._q)
        elif isinstance(first, Quaternion) and isinstance(second, np.ndarray):
            # q x vector
            return Quaternion(first.cross_matrix @ Quaternion(second)._q)
        else:
            raise ValueError("One of the arguments should be a Quaternion")

    @classmethod
    def dot(cls, first: 'Quaternion|np.ndarray', second: 'Quaternion|np.ndarray') -> 'Quaternion':
        r"""
        .. math::
            \odot

        :see also: Markley & Crassidis, Eqs. A.8b and A21.b, pgs 347 and 349
        """
        if isinstance(first, Quaternion) and isinstance(second, Quaternion):
            # q . q
            return Quaternion(first.dot_matrix @ second._q)
        elif isinstance(first, np.ndarray) and isinstance(second, Quaternion):
            # vector . q
            return Quaternion(Quaternion(first).dot_matrix @ second._q)
        elif isinstance(first, Quaternion) and isinstance(second, np.ndarray):
            # q . vector
            return Quaternion(first.dot_matrix @ Quaternion(second)._q)
        else:
            raise ValueError("One of the arguments should be a Quaternion")

    @classmethod
    def eye(cls) -> 'Quaternion':
        r"""
        Creates the identity quaternion.
        """
        return Quaternion(np.array([0, 0, 0, 1]))

    @classmethod
    def normalized(cls, obj: 'Quaternion') -> 'Quaternion':
        r"""
        Returns the quaternion, normalized.
        """
        return obj / np.linalg.norm(obj._q) ** 2

    @classmethod
    def error(cls, q1: 'Quaternion', q2: 'Quaternion') -> 'Quaternion':
        r"""
        Computes the error quaternion.

        The error quaternion is defined as:
        .. math::
            \delta \vector{q} \equiv \vector{q}_1 \otimes \vector{q}_2^{-1}

        :param q1: Calculated quaternion
        :param q2: Reference quaternion
        :return: Error quaternion
        """
        return Quaternion.cross(q1, q2.inv())
