import enum
from turtle import st
import numpy as np


class Bezier():
    APPROX_LEVEL = 4

    def __init__(self, curve_points):
        # estimate the length of the curve
        diffs = np.subtract(curve_points[1:], curve_points[:-1])
        approx_len = np.sum(np.sqrt(np.einsum('...i,...i', diffs, diffs)))

        # subdivide the curve
        subdivisions = int(approx_len / Bezier.APPROX_LEVEL) + 2
        self.curve_points = Bezier.__point_at(curve_points, np.linspace(0, 1, subdivisions))

        # Calculate actual length note that we gave actual points
        diffs = np.subtract(self.curve_points[1:], self.curve_points[:-1])
        self.len = np.sum(np.sqrt(np.einsum('...i,...i', diffs, diffs)))


    def length(self):
        return self.len


    def point_at(self, p):
        return self.curve_points[int(p*len(self.curve_points))]


    @staticmethod
    def __point_at(curve_points, t):
        n = len(curve_points) - 1
        return sum(
            np.expand_dims(Bezier.__bernstein(i, n, t), -1) * p
            for i, p in enumerate(curve_points)
        )

    @staticmethod
    def __bernstein(i, n, t):
        return Bezier.__binomialCoefficient(n, i) * (t**i) * ((1 - t)**(n - i))


    @staticmethod
    def __binomialCoefficient(n, k):
        if k < 0 or k > n:   return 0
        if k == 0 or k == n: return 1

        k = min(k, n - k)  # Take advantage of geometry

        k_range = np.arange(k)
        c = np.prod((n - k_range) / (k_range + 1))

        return c


class Slider():
    def __init__(self, control_points):
        IDX_T = 0  # time
        IDX_X = 1  # xpos
        IDX_Y = 2  # ypos
        IDX_C = 3  # split slider?

        self.beziers = []

        curve = []
        for c in control_points:
            curve.append([ c[IDX_X], c[IDX_Y] ])

            if c[IDX_C] == 1:
                self.beziers.append(Bezier(curve))
                curve = [ [ c[IDX_X], c[IDX_Y] ] ]

        self.beziers.append(Bezier(curve))
        self.len = sum([ b.length() for b in self.beziers ])
        
        self.curve = []
        for bezier in self.beziers:
            self.curve.extend(bezier.curve_points)


    def point_at(self, p):
        return self.curve[int(p*len(self.curve))]



    def length(self):
        return self.len
