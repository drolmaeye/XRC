from scipy import exp, asarray
from math import cos, sin, radians, pi, sqrt

T = 200

r_one_295_reference = 694.260

r_one_295_user = 694.200

r_one_295_offset = r_one_295_user - r_one_295_reference

r_one_t_cm = 14423.0 + 0.0446*T - 0.000481*T*T + 0.000000371*T*T*T

r_one_t_nm = 10000000 / r_one_t_cm

print r_one_t_nm

r_one_t_corrected = r_one_t_nm + r_one_295_offset

print r_one_t_corrected

r_one_measured = 694.200


alpha = 1904
beta = 7.665

pressure = alpha * ((1 / beta) * (((r_one_measured / r_one_t_corrected) ** beta) - 1))
print pressure

