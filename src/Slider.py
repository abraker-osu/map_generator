import typing

import numpy as np


class Bezier():
    APPROX_LEVEL = 4

    def __init__(self, curve_points):
        # estimate the length of the curve
        diffs = np.subtract(curve_points[1:], curve_points[:-1])
        approx_len = np.sum(np.sqrt(np.einsum('...i,...i', diffs, diffs)))

        # subdivide the curve
        subdivisions = int(approx_len / Bezier.APPROX_LEVEL) + 2

        self.__curve_points: typing.Final = Bezier.__point_at(curve_points, np.linspace(0, 1, subdivisions))
        assert isinstance(self.__curve_points, np.ndarray)

        # Calculate actual length note that we gave actual points
        diffs = np.subtract(self.__curve_points[1:], self.__curve_points[:-1])
        self.__len = np.sum(np.sqrt(np.einsum('...i,...i', diffs, diffs)))


    @property
    def curve_points(self) -> np.ndarray:
        if isinstance(self.__curve_points, ( int, float )):
            return np.array([ self.__curve_points ])

        return self.__curve_points


    def length(self) -> float:
        return float(self.__len)


    def point_at(self, p: float) -> np.ndarray:
        assert isinstance(self.__curve_points, np.ndarray)
        return self.__curve_points[int(p*len(self.__curve_points))]


    @staticmethod
    def __point_at(curve_points: np.ndarray, t: float | np.ndarray) -> float | np.ndarray:
        n = len(curve_points) - 1
        return sum(
            np.expand_dims(Bezier.__bernstein(i, n, t), -1) * p
            for i, p in enumerate(curve_points)
        )


    @staticmethod
    def __bernstein(i: int, n: int, t: float | np.ndarray) -> float | np.ndarray:
        return Bezier.__binomialCoefficient(n, i) * (t**i) * ((1 - t)**(n - i))


    @staticmethod
    def __binomialCoefficient(n: float, k: float) -> float:
        if k < 0 or k > n:   return 0
        if k == 0 or k == n: return 1

        k = min(k, n - k)  # Take advantage of geometry

        k_range = np.arange(k)
        c = np.prod((n - k_range) / (k_range + 1))

        return float(c)


class Slider():

    def __init__(self, control_points: list[list[int]]):
        IDX_T = 0  # time
        IDX_X = 1  # xpos
        IDX_Y = 2  # ypos
        IDX_C = 3  # whether to split slider

        self.__beziers: list[Bezier] = []

        curve = []
        for c in control_points:
            curve.append([ c[IDX_X], c[IDX_Y] ])

            if c[IDX_C] == 1:
                self.__beziers.append(Bezier(curve))
                curve = [ [ c[IDX_X], c[IDX_Y] ] ]

        self.__beziers.append(Bezier(curve))
        self.__len = sum([ b.length() for b in self.__beziers ])

        self.__curve = []
        for bezier in self.__beziers:
            self.__curve.extend(bezier.curve_points)


    def point_at(self, p: float) -> np.ndarray:
        return self.__curve[int(p*len(self.__curve))]


    def length(self) -> float:
        return self.__len
