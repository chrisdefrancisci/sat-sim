import numpy as np


def rotation_matrix(axis: int, angle: float) -> np.ndarray:
    r"""
    Class for matrix rotations. Note that it is 0 indexed.

    .. math::
        \text{ROT0}(\alpha) =
        \begin{bmatrix}
            1 & 0 & 0 \\
            0 & cos(\alpha) & sin(\alpha) \\
            0 & -sin(\alpha) & cos(\alpha) \\
        \end{bmatrix}

    .. math::
        \text{ROT1}(\alpha) =
        \begin{bmatrix}
            cos(\alpha) & 0 & -sin(\alpha) \\
            0 & 1 & 0 \\
            sin(\alpha) & 0 & cos(\alpha) \\
        \end{bmatrix}

    .. math::
        \text{ROT2}(\alpha) =
        \begin{bmatrix}
            cos(\alpha) & sin(\alpha) & 0\\
            -sin(\alpha) & cos(\alpha) & 0 \\
            0 & 0 & 1
        \end{bmatrix}

    :see also: Vallado, Eq 3-15, pg 164
    :param axis: Principle axis of rotation.
    :param angle: Angle of rotation, in radians.
    :return: Rotation matrix.

    """

    if axis == 0:
        return np.array([[1, 0, 0],
                         [0, np.cos(angle), np.sin(angle)],
                         [0, -np.sin(angle), np.cos(angle)]])
    elif axis == 1:
        return np.array([[np.cos(angle), 0, -np.sin(angle)],
                         [0, 1, 0],
                         [np.sin(angle), 0, np.cos(angle)]])
    elif axis == 2:
        return np.array([[np.cos(angle), np.sin(angle), 0],
                         [-np.sin(angle), np.cos(angle), 0],
                         [0, 0, 1]])
    else:
        raise ValueError('Axis of rotation must be 0, 1, or 2.')
