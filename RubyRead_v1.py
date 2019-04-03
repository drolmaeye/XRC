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



class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(100, 100, 1080, 720)
        self.setWindowTitle('RubyRead')
        self.setWindowIcon(QtGui.QIcon('ruby3.png'))

        # make the window portion of the Main Window using QWidget

        self.cw = QtGui.QWidget()
        self.setCentralWidget(self.cw)

        self.cw_layout = QtGui.QHBoxLayout(self.cw)
        self.cw.setLayout(self.cw_layout)


        self.pw = pg.PlotWidget(name='Plot1')

        self.cw_layout.addWidget(self.pw)









        self.show()













app = QtGui.QApplication(sys.argv)
gui = Window()
curve = gui.pw.plot()
ptr = 0
sys.exit(app.exec_())







# ###if __name__ == '__main__':
# ###    main()
# ###    curve = gui.pw.plot(xs, ys, pen=0.75)
# ###    ptr = 0