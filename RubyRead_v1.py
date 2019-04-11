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
from scipy.optimize import curve_fit
from scipy import exp, asarray
from math import cos, sin, radians, pi, sqrt


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

        # make and add layout to Pressure Control QGroupBox
        self.press_control_layout = QtGui.QGridLayout()
        self.press_control_layout.setAlignment(QtCore.Qt.AlignTop)
        self.press_control.setLayout(self.press_control_layout)

        # ###make and add individual widgets to press control layout

        # create, configure, and add lambda naught label and input
        self.lambda_naught_label = QtGui.QLabel('R1 lambda naught (nm)')
        self.lambda_naught_input = QtGui.QLineEdit('694.290')
        self.lambda_naught_input.setValidator(QtGui.QDoubleValidator(694.200, 694.400, 3))
        self.press_control_layout.addWidget(self.lambda_naught_label, 0, 0)
        self.press_control_layout.addWidget(self.lambda_naught_input, 0, 1)

        # create, configure, add pointer widget
        self.pointer_position_label = QtGui.QLabel('Pointer position')
        self.pointer_position_input = QtGui.QLineEdit('694.290')
        self.pointer_position_input.setValidator(QtGui.QDoubleValidator(670.000, 770.000, 3))
        self.press_control_layout.addWidget(self.pointer_position_label, 1, 0)
        self.press_control_layout.addWidget(self.pointer_position_input, 1, 1)

        # create, configure, add calibration label
        self.press_calibration_label1 = QtGui.QLabel('Pressure Calibration')
        self.press_calibration_label2 = QtGui.QLabel('Mao et al 1986')
        self.press_control_layout.addWidget(self.press_calibration_label1, 2, 0)
        self.press_control_layout.addWidget(self.press_calibration_label2, 2, 1)

        # create, configure, add sample temperature widgets
        self.temperature_label = QtGui.QLabel('Temperature (K)')
        self.temperature_input = QtGui.QLineEdit('300')
        self.temperature_track_cbox = QtGui.QCheckBox('Track')
        self.press_control_layout.addWidget(self.temperature_label, 3, 0)
        self.press_control_layout.addWidget(self.temperature_input, 3, 1)
        self.press_control_layout.addWidget(self.temperature_track_cbox, 3, 2)

        # create, configure, add pressure calc widgets
        self.press_calc_label1 = QtGui.QLabel('P(calculated) (GPa)')
        self.press_calc_label2 = QtGui.QLabel('0.00')
        self.press_control_layout.addWidget(self.press_calc_label1, 4, 0)
        self.press_control_layout.addWidget(self.press_calc_label2, 4, 1)

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

        # pressure calculation parameters
        self.alpha = 1904
        self.beta = 9.5
        self.lambda0 = 694.290
        self.temperature = 300
        self.pressure = 0.00




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
    # get and plot spectra
    start = time.clock()
    core.ys = core.spec.intensities()
    if gui.average_spec_cbox.isChecked():
        num = int(gui.average_spec_input.text())
        for each in range(num - 1):
            core.ys += core.spec.intensities()
        core.ys = core.ys/num
    core.curve.setData(core.xs, core.ys)

    # start to pick values for fitting
    slope = (core.ys[-1] - core.ys[0]) / (core.xs[-1] - core.xs[0])
    intercept = core.ys[0] - slope * core.xs[0]
    max_index = np.argmax(core.ys)
    r1 = core.xs[max_index]
    r2 = r1 - 1.4
    r1_h = core.ys[max_index] - (slope * r1 + intercept)
    r2_h = r1_h / 2.0

    # define fitting parameters p0
    p0 = [r2_h, r2, 0.5, 1.0, r1_h, r1, 0.5, 1.0, slope, intercept]

    # fit!
    popt, pcov = curve_fit(double_pseudo, core.xs, core.ys, p0=p0)

    gui.pointer_position_input.setText('%.3f' % popt[5])

    # delta T first try
    current_temp = float(gui.temperature_input.text())
    print current_temp



    # calculate pressure (needs to be independent function)
    core.pressure = core.alpha * ((1 / core.beta) * (((popt[5] / core.lambda0) ** core.beta) - 1))
    gui.press_calc_label2.setText('%.2f' % core.pressure)
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


def update_count_time():
    count_time = int(gui.count_time_input.text())*1000
    core.spec.integration_time_micros(count_time)






app = QtGui.QApplication(sys.argv)
pg.setConfigOptions(antialias=True)
gui = Window()
core = CoreData()
sys.exit(app.exec_())
