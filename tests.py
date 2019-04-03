import sys
from PyQt4 import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import seabreeze.spectrometers as sb
import time
from scipy.optimize import curve_fit
from scipy import exp, asarray
from math import cos, sin, radians, pi, sqrt


devices = sb.list_devices()
spec = sb.Spectrometer(devices[0])
spec.integration_time_micros(10000)

app = QtGui.QApplication(sys.argv)
win = pg.GraphicsWindow(title='First try')
win.resize(800, 800)
win.setWindowTitle('First try again')

btn = QtGui.QPushButton('start')

entry = QtGui.QLineEdit()
entry.setValidator(QtGui.QIntValidator())
entry.setMaxLength(4)
#entry.setAlignment(QtCore.AlignRight)
entry.setFont(QtGui.QFont("Arial",20))


pg.setConfigOptions(antialias=True)



layout = pg.LayoutWidget()
layout.addWidget(btn, 0, 1)
layout.addWidget(win, 0, 0)
layout.addWidget(entry, 1, 1)
layout.show()

xs = spec.wavelengths()
ys = spec.intensities()


fred = np.argmax(ys)
charles = xs[np.argmax(ys)]


print fred
print charles

p1 = win.addPlot(title='Spectrum')
curve = p1.plot(xs, ys, pen=0.75)

ptr = 0
num =1

def edit_done():
    global num
    print num
    num = int(entry.text())
    print num





def start_timer():
    print 'response'
    global stoppage
    global timer
    timer = QtCore.QTimer()
    if stoppage:
        stoppage = False
        timer.timeout.connect(update)
        timer.start(200)
    else:
        stoppage = True
        timer.stop()
    print'end'


def update():

    global curve, ptr, p1, num
    start = time.clock()
    ys = spec.intensities()
    for each in range (num - 1):
        ys += spec.intensities()
        print ys[0]
    ys = ys/num
    print ys[0]


    # ys = spec.intensities()

    curve.setData(xs, ys)
    if ptr == 0:
        p1.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    ptr += 1



    slope = (ys[-1] - ys[0]) / (xs[-1] - xs[0])
    intercept = ys[0] - slope * xs[0]
    max_index = np.argmax(ys)
    r1 = xs[max_index]
    r2 = r1 - 1.4
    r1_h = ys[max_index] - (slope * r1 + intercept)
    r2_h = r1_h / 2.0

    p0 = [r2_h, r2, 0.5, 1.0, r1_h, r1, 0.5, 1.0, slope, intercept]

    # popt, pcov = curve_fit(double_gauss, xs, ys, p0=[1000.0, 699.0, 1.0, 2000.0, 700.0, 1.0, -1.0, 3000.0])
    popt, pcov = curve_fit(double_pseudo, xs, ys, p0=p0)

    print popt[5]

    alpha = 1904
    beta = 9.5
    lambda0 = 694.300

    P = alpha * ((1 / beta) * (((popt[5] / lambda0) ** beta) - 1))
    print P
    end = time.clock()
    print end - start
    
def double_pseudo(x, a1, c1, eta1, w1, a2, c2, eta2, w2, m, bg):
    return a1 * (eta1 * (2 / pi) * (w1 / (4 * (x - c1) ** 2 + w1 ** 2)) +
                 (1 - eta1) * (sqrt(4 * np.log(2)) / (sqrt(pi) * w1)) * exp(
                -(4 * np.log(2) / w1 ** 2) * (x - c1) ** 2)) + \
           a2 * (eta2 * (2 / pi) * (w2 / (4 * (x - c2) ** 2 + w2 ** 2)) +
                 (1 - eta2) * (sqrt(4 * np.log(2)) / (sqrt(pi) * w2)) * exp(
                -(4 * np.log(2) / w2 ** 2) * (x - c2) ** 2)) + \
           m * x + bg

stoppage = True

btn.clicked.connect(start_timer)
entry.editingFinished.connect(edit_done)
# timer = QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(100)


app.exec_()

