from scipy import exp, asarray
from math import cos, sin, radians, pi, sqrt

v0 = 10000000/694.290

v = v0 - 76.6*(1/(exp(482.0/300.0)-1))

l = 10000000/v

print l

print l - 694.290