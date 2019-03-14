import sys
from PyQt4 import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import seabreeze.spectrometers as sb
import time

devices = sb.list_devices()
spec = sb.Spectrometer(devices[0])
spec.integration_time_micros(20000)

app = QtGui.QApplication(sys.argv)
win = pg.GraphicsWindow(title='First try')
win.resize(800, 800)
win.setWindowTitle('First try again')

btn = QtGui.QPushButton('start')

pg.setConfigOptions(antialias=True)

layout = pg.LayoutWidget()
layout.addWidget(btn)
layout.addWidget(win, row=1)
layout.show()

xs = spec.wavelengths()
ys = spec.intensities()

start = time.clock()
fred = np.argmax(ys)
charles = xs[np.argmax(ys)]
end = time.clock()
print end - start, 'wow!'
print fred
print charles

p1 = win.addPlot(title='Spectrum')
curve = p1.plot(xs, ys, pen='b')

ptr = 0





def start_timer():
    print 'response'
    global stoppage
    global timer
    timer = QtCore.QTimer()
    if stoppage:
        stoppage = False
        timer.timeout.connect(update)
        timer.start(50)
    else:
        stoppage = True
        timer.stop()
    print'end'


def update():
    global curve, ptr, p1
    ys = spec.intensities()
    curve.setData(xs, ys)
    if ptr == 0:
        p1.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    ptr += 1

stoppage = True

btn.clicked.connect(start_timer)
# timer = QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(100)


app.exec_()

