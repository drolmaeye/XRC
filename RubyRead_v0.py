__author__ = 'j.smith'

'''
A GUI for measuring ruby pressure with Ocean Optics spectrometer
'''

# import necessary modules
import sys
from PyQt4 import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import seabreeze.spectrometers as sb
import time

# ###graph_data = open('visible_spectrum.txt', 'r').read()
# ###lines = graph_data.split('\n')
# ###xs = []
# ###ys = []
# ###
# ###for line in lines:
# ###    if len(line) > 1:
# ###        i, j = line.split(',')
# ###        xs.append(i)
# ###        ys.append(j)
# ###
# ###xra = np.asarray(xs).astype(float)
# ###yra = np.asarray(ys).astype(float)

devices = sb.list_devices()
spec = sb.Spectrometer(devices[0])
spec.integration_time_micros(20000)

xs = spec.wavelengths()
ys = spec.intensities()



class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(100, 100, 1080, 720)
        self.setWindowTitle('RubyRead')
        self.setWindowIcon(QtGui.QIcon('ruby3.png'))

        # make the window portion of the Main Window using QWidget

        self.cw = QtGui.QWidget()
        self.setCentralWidget(self.cw)

        grid = QtGui.QGridLayout(self.cw)
        self.cw.setLayout(grid)




        self.pw = pg.PlotWidget(name='Plot1')
        self.btn_2 = QtGui.QPushButton('Start')
        self.btn_2.clicked.connect(start_timer)
        self.btn_3 = QtGui.QPushButton('Three')
        self.btn_4 = QtGui.QPushButton('Four')

        grid.addWidget(self.pw, 1, 0, 3, 1)
        grid.addWidget(self.btn_2, 0, 1)
        grid.addWidget(self.btn_3, 1, 1)
        grid.addWidget(self.btn_4, 2, 1)

        #p1 = self.pw.plot(y=ys, x=xs)


        # self.cw = pg.GraphicsLayoutWidget(self)
        # self.setCentralWidget(self.cw)

        # self.vbox = QtGui.QVBoxLayout()
        # self.vbox.addWidget(self.pw)










        self.show()


def start_timer():
    print 'response'
    global stoppage
    global timer
    timer = QtCore.QTimer()
    if stoppage:
        stoppage = False
        timer.timeout.connect(update)
        timer.start(1000)
    else:
        stoppage = True
        timer.stop()
    print'end'


def update():
    global curve, ptr, p1
    ys = spec.intensities()
    curve.setData(xs, ys)
    if ptr == 0:
        gui.pw.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    ptr += 1

stoppage = True










app = QtGui.QApplication(sys.argv)
gui = Window()
curve = gui.pw.plot()
ptr = 0
sys.exit(app.exec_())







# ###if __name__ == '__main__':
# ###    main()
# ###    curve = gui.pw.plot(xs, ys, pen=0.75)
# ###    ptr = 0