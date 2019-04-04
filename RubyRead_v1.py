__author__ = 'j.smith'

'''
A GUI for measuring ruby pressure with Ocean Optics spectrometer
'''

# import necessary modules
import sys
from PyQt4 import QtGui, QtCore, Qt
import numpy as np
import pyqtgraph as pg
import seabreeze.spectrometers as sb
import time



class Window(QtGui.QMainWindow):

    def __init__(self):
        # use QMainWindow in this early version to benefit from menu, tool bar, etc.
        super(Window, self).__init__()
        self.setGeometry(100, 100, 1080, 720)
        self.setWindowTitle('RubyRead')
        self.setWindowIcon(QtGui.QIcon('ruby3.png'))

        # create the main widget self.mw for the 'window' portion and make it central
        self.mw = QtGui.QWidget()
        self.setCentralWidget(self.mw)

        # now make and set layout for the mw (main window)
        self.mw_layout = QtGui.QHBoxLayout()
        self.mw.setLayout(self.mw_layout)

        # ###make toolbar
        self.tool_bar = self.addToolBar('Main Controls')

        self.take_one_spec = QtGui.QAction('1', self.tool_bar)
        self.take_one_spec.triggered.connect(lambda: start_timer(1))
        self.tool_bar.addAction(self.take_one_spec)

        self.take_n_spec = QtGui.QAction('n', self.tool_bar)
        self.take_n_spec.triggered.connect(lambda: start_timer(0))
        self.tool_bar.addAction(self.take_n_spec)



        # make the plot window for the left side and add it to main window layout
        self.pw = pg.PlotWidget(name='Plot1')
        self.mw_layout.addWidget(self.pw)

        # make the control window for the right side and add it to main window layout
        self.cw = QtGui.QWidget()
        self.cw.setMaximumWidth(300)
        self.mw_layout.addWidget(self.cw)

        # make the layout for the control widget
        self.cw_layout = QtGui.QVBoxLayout()
        self.cw.setLayout(self.cw_layout)

        ###
        # Spectrum Control Window
        ###

        # make top right widget for spectrometer control
        self.spec_control = QtGui.QGroupBox()
        self.spec_control.setTitle('Spectrum Control')
        self.cw_layout.addWidget(self.spec_control)

        # make and add layout to Spectrum Control QGroupBox
        self.spec_control_layout = QtGui.QGridLayout()
        self.spec_control_layout.setAlignment(QtCore.Qt.AlignTop)
        self.spec_control.setLayout(self.spec_control_layout)

        # ###make and add individual widgets to spec control grid layout

        # create and add count time label
        self.count_time_label = QtGui.QLabel('Integration time (ms)')
        self.spec_control_layout.addWidget(self.count_time_label, 0, 0, 1, 2)

        # create, configure, add count time input field
        self.count_time_input = QtGui.QLineEdit('100')
        self.count_time_input.setValidator(QtGui.QIntValidator())
        self.count_time_input.setMaxLength(4)
        self.count_time_input.editingFinished.connect(update_count_time)
        self.spec_control_layout.addWidget(self.count_time_input, 1, 0, 2, 1)

        # create count time shortcut buttons
        self.btn_20 = QtGui.QPushButton('20')
        self.btn_50 = QtGui.QPushButton('50')
        self.btn_100 = QtGui.QPushButton('100')
        self.btn_200 = QtGui.QPushButton('200')
        self.btn_500 = QtGui.QPushButton('500')
        self.btn_1000 = QtGui.QPushButton('1000')

        # make buttons small
        self.btn_20.setMaximumWidth(50)
        self.btn_50.setMaximumWidth(50)
        self.btn_100.setMaximumWidth(50)
        self.btn_200.setMaximumWidth(50)
        self.btn_500.setMaximumWidth(50)
        self.btn_1000.setMaximumWidth(50) 

        # connect buttons to function
        self.btn_20.clicked.connect(lambda: self.count_time_shortcut('20'))
        self.btn_50.clicked.connect(lambda: self.count_time_shortcut('50'))
        self.btn_100.clicked.connect(lambda: self.count_time_shortcut('100'))
        self.btn_200.clicked.connect(lambda: self.count_time_shortcut('200'))
        self.btn_500.clicked.connect(lambda: self.count_time_shortcut('500'))
        self.btn_1000.clicked.connect(lambda: self.count_time_shortcut('1000'))

        # add shortcut buttons to layout
        self.spec_control_layout.addWidget(self.btn_20, 1, 1)
        self.spec_control_layout.addWidget(self.btn_50, 1, 2)
        self.spec_control_layout.addWidget(self.btn_100, 1, 3)
        self.spec_control_layout.addWidget(self.btn_200, 2, 1)
        self.spec_control_layout.addWidget(self.btn_500, 2, 2)
        self.spec_control_layout.addWidget(self.btn_1000, 2, 3)

        # create and add checkbox widget
        self.average_spec_cbox = QtGui.QCheckBox('Average n spectra')
        self.spec_control_layout.addWidget(self.average_spec_cbox, 3, 0, 1, 2)

        # create and add number to average
        self.average_spec_input = QtGui.QLineEdit('1')
        self.average_spec_input.setValidator(QtGui.QIntValidator())
        self.average_spec_input.setMaxLength(1)
        self.spec_control_layout.addWidget(self.average_spec_input, 3, 2)

        ###
        # Pressure Control Window
        ###

        # make bottom right widget for Pressure control
        self.press_control = QtGui.QGroupBox()
        self.press_control.setTitle('Pressure Control')
        self.cw_layout.addWidget(self.press_control)

        self.show()

    def count_time_shortcut(self, count):
        self.count_time_input.setText(count)
        core.spec.integration_time_micros(int(count)*1000)


class CoreData:
    def __init__(self):
        # super(CoreData, self).__init__()
        self.curve = gui.pw.plot()
        self.stopped = True
        self.ptrn = 0

        self.devices = sb.list_devices()
        self.spec = sb.Spectrometer(self.devices[0])
        self.spec.integration_time_micros(10000)

        self.xs = self.spec.wavelengths()
        self.ys = self.spec.intensities()

        self.timer = QtCore.QTimer()


def start_timer(count):
    if count:
        update()
    else:
        if core.stopped:
            core.stopped = False
            core.timer.timeout.connect(update)
            core.timer.start(20)
        else:
            core.stopped = True
            core.timer.stop()




def update():
    start = time.clock()
    core.ys = core.spec.intensities()
    if gui.average_spec_cbox.isChecked():
        num = int(gui.average_spec_input.text())
        for each in range(num - 1):
            core.ys += core.spec.intensities()
            print core.ys[0]
        core.ys = core.ys/num
        print core.ys[0]
    core.curve.setData(core.xs, core.ys)
    print time.clock() - start


def update_count_time():
    count_time = int(gui.count_time_input.text())*1000
    core.spec.integration_time_micros(count_time)






app = QtGui.QApplication(sys.argv)
pg.setConfigOptions(antialias=True)
gui = Window()
core = CoreData()
sys.exit(app.exec_())
