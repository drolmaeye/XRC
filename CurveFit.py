import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import seabreeze.spectrometers as sb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
import numpy as np
from scipy.optimize import curve_fit
from scipy import exp, asarray
from math import cos, sin, radians, pi, sqrt

style.use('dark_background')

fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)

graph_data = open('visible_spectrum.txt', 'r').read()
lines = graph_data.split('\n')
xs = []
ys = []

for line in lines:
    if len(line) > 1:
        i, j = line.split(',')
        xs.append(i)
        ys.append(j)

xra = asarray(xs).astype(float)
yra = asarray(ys).astype(float)


def double_gauss(x, a1, mu1, sigma1, a2, mu2, sigma2, m, bg):
    return a1 * exp(-(x - mu1) ** 2.0 / (2.0 * sigma1 ** 2.0)) + a2 * exp(
        -(x - mu2) ** 2.0 / (2.0 * sigma2 ** 2.0)) + m * x + bg


def double_pseudo(x, a1, c1, eta1, w1, a2, c2, eta2, w2, m, bg):
    return a1 * (eta1 * (2 / pi) * (w1 / (4 * (x - c1) ** 2 + w1 ** 2)) +
                 (1 - eta1) * (sqrt(4 * np.log(2)) / (sqrt(pi) * w1)) * exp(
                -(4 * np.log(2) / w1 ** 2) * (x - c1) ** 2)) + \
           a2 * (eta2 * (2 / pi) * (w2 / (4 * (x - c2) ** 2 + w2 ** 2)) +
                 (1 - eta2) * (sqrt(4 * np.log(2)) / (sqrt(pi) * w2)) * exp(
                -(4 * np.log(2) / w2 ** 2) * (x - c2) ** 2)) + \
           m * x + bg

def pseudo(x, a, c, eta, w, m, bg):
    return a * (eta * (2 / pi) * (w / (4 * (x - c) ** 2 + w ** 2)) +
                 (1 - eta) * (sqrt(4 * np.log(2)) / (sqrt(pi) * w)) * exp(
                -(4 * np.log(2) / w ** 2) * (x - c) ** 2)) + m * x + bg



# popt, pcov = curve_fit(double_gauss, xra, yra, p0=[1000.0, 699.0, 1.0, 2000.0, 700.0, 1.0, -1.0, 3000.0])
popt, pcov = curve_fit(double_pseudo, xra, yra, p0=[1000.0, 699.0, 0.5, 1.0, 2000.0, 700.0, 0.5, 1.0, -1.0, 3000.0])

print popt
# ax1.plot(xra, double_gauss(xra, *popt), 'ro')



ax1.plot(xra, yra)
ax1.plot(xra, double_pseudo(xra, *popt))
ax1.plot(xra, pseudo(xra, popt[0], popt[1], popt[2], popt[3], popt[8], popt[9]))
ax1.plot(xra, pseudo(xra, popt[4], popt[5], popt[6], popt[7], popt[8], popt[9]))
ax1.plot(xra, (popt[8]*xra + popt[9]))

plt.show()
