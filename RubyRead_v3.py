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
        self.spec_control_layout.addWidget(self.count_time_input, 1, 0)

        # crate count time shortcut buttons
        self.count_less_button = QtGui.QPushButton('')
        self.count_less_button.setIcon(QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_ArrowLeft))
        self.count_more_button = QtGui.QPushButton('')
        self.count_more_button.setIcon(QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_ArrowRight))

        # connect shortcut buttons to count time function
        self.count_less_button.clicked.connect(lambda: self.count_time_shortcut('down'))
        self.count_more_button.clicked.connect(lambda: self.count_time_shortcut('up'))

        # add shortcut buttons to layout
        self.spec_control_layout.addWidget(self.count_less_button, 1, 1)
        self.spec_control_layout.addWidget(self.count_more_button, 1, 2)


        # create and add checkbox widget
        self.average_spec_cbox = QtGui.QCheckBox('Average n spectra')
        self.spec_control_layout.addWidget(self.average_spec_cbox, 3, 0, 1, 2)

        # create and add number to average
        self.average_spec_input = QtGui.QLineEdit('1')
        self.average_spec_input.setValidator(QtGui.QIntValidator())
        self.average_spec_input.setMaxLength(1)
        self.spec_control_layout.addWidget(self.average_spec_input, 3, 2)

        ###
        # Plot control window
        ###

        # make central right widget for plot control
        self.plot_control = QtGui.QGroupBox()
        self.plot_control.setTitle('Plot Control')
        self.cw_layout.addWidget(self.plot_control)

        # make and add layout for Plot Control QGroupBox
        self.plot_control_layout = QtGui.QGridLayout()
        self.plot_control_layout.setAlignment(QtCore.Qt.AlignTop)
        self.plot_control.setLayout(self.plot_control_layout)

        # ### make and add individual widgets to plot control
        self.plot_control_top_label = QtGui.QLabel('Select items to show')
        self.show_fit_cbox = QtGui.QCheckBox('Fit')
        self.show_r1r2_cbox = QtGui.QCheckBox('R1, R2')
        self.show_bg_cbox = QtGui.QCheckBox('Background')
        self.show_reference_p_cbox = QtGui.QCheckBox('P(ref)')
        self.show_target_p_cbox = QtGui.QCheckBox('P(target)')
        self.zoom_full_btn = QtGui.QPushButton('Full spectrum')
        self.zoom_roi_btn = QtGui.QPushButton('Zoom ROI')
        self.autoscale_cbox = QtGui.QCheckBox('Autoscale')

        self.plot_control_layout.addWidget(self.plot_control_top_label, 0, 0)
        self.plot_control_layout.addWidget(self.show_fit_cbox, 1, 0)
        self.plot_control_layout.addWidget(self.show_r1r2_cbox, 2, 0)
        self.plot_control_layout.addWidget(self.show_bg_cbox, 3, 0)
        self.plot_control_layout.addWidget(self.show_reference_p_cbox, 4, 0)
        self.plot_control_layout.addWidget(self.show_target_p_cbox, 5, 0)
        self.plot_control_layout.addWidget(self.zoom_full_btn, 6, 0)
        self.plot_control_layout.addWidget(self.zoom_roi_btn, 6, 1)
        self.plot_control_layout.addWidget(self.autoscale_cbox, 6, 2)

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

        # create, configure, and add lambda naught (295) label and input
        self.lambda_naught_295_label = QtGui.QLabel(u'\u03BB' + '<sub>0</sub>' + '(295)' + ' (nm)')
        self.lambda_naught_295_input = QtGui.QLineEdit()
        self.lambda_naught_295_input.setValidator(QtGui.QDoubleValidator(694.200, 694.400, 3))
        self.press_control_layout.addWidget(self.lambda_naught_295_label, 0, 0)
        self.press_control_layout.addWidget(self.lambda_naught_295_input, 0, 1)

        # create, configure, and add lambda naught (T) label and input
        self.lambda_naught_t_label = QtGui.QLabel(u'\u03BB' + '<sub>0</sub>' + '(T)' + ' (nm)')
        self.lambda_naught_t_input = QtGui.QLineEdit()
        self.lambda_naught_t_input.setValidator(QtGui.QDoubleValidator(690.000, 699.000, 3))
        self.press_control_layout.addWidget(self.lambda_naught_t_label, 1, 0)
        self.press_control_layout.addWidget(self.lambda_naught_t_input, 1, 1)

        # create, configure, add pointer widget
        self.pointer_position_label = QtGui.QLabel(u'\u03BB' + '<sub>R1</sub>' + ' (nm)')
        self.pointer_position_input = QtGui.QLineEdit()
        self.pointer_position_input.setValidator(QtGui.QDoubleValidator(670.000, 770.000, 3))
        self.press_control_layout.addWidget(self.pointer_position_label, 2, 0)
        self.press_control_layout.addWidget(self.pointer_position_input, 2, 1)

        # create, configure, add calibration label
        self.press_calibration_label1 = QtGui.QLabel('Pressure Calibration')
        self.press_calibration_label2 = QtGui.QLabel('Mao et al 1986')
        self.press_control_layout.addWidget(self.press_calibration_label1, 3, 0)
        self.press_control_layout.addWidget(self.press_calibration_label2, 3, 1)

        # create, configure, add sample temperature widgets
        self.temperature_label = QtGui.QLabel('Temperature (K)')
        self.temperature_input = QtGui.QLineEdit()
        self.temperature_input.returnPressed.connect(calculate_lambda_0_t)
        self.temperature_track_cbox = QtGui.QCheckBox('Track')
        self.press_control_layout.addWidget(self.temperature_label, 4, 0)
        self.press_control_layout.addWidget(self.temperature_input, 4, 1)
        self.press_control_layout.addWidget(self.temperature_track_cbox, 4, 2)

        # create, configure, add fitting threshold widgets
        self.fit_threshold_label = QtGui.QLabel('Fit threshold')
        self.fit_threshold_input = QtGui.QLineEdit('200')
        self.fit_threshold_input.setValidator(QtGui.QIntValidator())
        self.press_control_layout.addWidget(self.fit_threshold_label, 5, 0)
        self.press_control_layout.addWidget(self.fit_threshold_input, 5, 1)

        # create, configure, add pressure calc widgets
        self.press_calc_label1 = QtGui.QLabel('Pressure<sub>calc</sub> (GPa)')
        self.press_calc_label2 = QtGui.QLabel('0.00')
        self.press_fit_cbox = QtGui.QCheckBox('Fit')
        self.press_control_layout.addWidget(self.press_calc_label1, 6, 0)
        self.press_control_layout.addWidget(self.press_calc_label2, 6, 1)
        self.press_control_layout.addWidget(self.press_fit_cbox, 6, 2)


        self.show()

    def count_time_shortcut(self, direction):
        # quickly increase count time over common range
        old_time = int(self.count_time_input.text())
        preset_times = ['20', '50', '100', '200', '500', '1000']
        if direction == 'down':
            for each in reversed(preset_times):
                if int(each) < old_time:
                    self.count_time_input.setText(each)
                    core.spec.integration_time_micros(int(each)*1000)
                    break
        if direction == 'up':
            for each in preset_times:
                if int(each) > old_time:
                    self.count_time_input.setText(each)
                    core.spec.integration_time_micros(int(each)*1000)
                    break

    def initialize_inputs(self):
        self.lambda_naught_295_input.setText('%.3f' % core.lambda_0_ref)
        self.lambda_naught_t_input.setText('%.3f' % core.lambda_0_t_user)
        self.pointer_position_input.setText('%.3f' % core.lambda_0_ref)
        self.temperature_input.setText('%.0f' % core.temperature)


class CoreData:
    def __init__(self):
        # super(CoreData, self).__init__()
        self.curve = gui.pw.plot()
        self.vline = pg.InfiniteLine(pos=694.260, angle=90.0, movable=True)
        gui.pw.addItem(self.vline)

        self.stopped = True
        self.ptrn = 0

        self.devices = sb.list_devices()
        self.spec = sb.Spectrometer(self.devices[0])
        self.spec.integration_time_micros(10000)

        self.xs = self.spec.wavelengths()
        self.ys = self.spec.intensities()

        self.timer = QtCore.QTimer()

        # pressure calculation parameters
        # lambda zero (ref) is 694.260 based on Ragan et al JAP 72, 5539 (1992) at 295K
        self.alpha = 1904
        self.beta = 9.5
        self.lambda_0_ref = 694.260
        self.lambda_0_user = 694.260
        self.lambda_0_t_user = 694.260
        self.lambda_r1 = 694.260
        self.temperature = 295
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

    if gui.press_fit_cbox.isChecked():
        print 'fitting'
    else:
        return

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
    calculate_pressure(popt[5])
    gui.press_calc_label2.setText('%.2f' % core.pressure)
    core.vline.setPos(popt[5])
    end = time.clock()
    print end - start


def calculate_lambda_0_t():
    offset = core.lambda_0_user - core.lambda_0_ref
    t = float(gui.temperature_input.text())
    lambda_0_t = 10000000 / (14423.0 + 0.0446*t - 0.000481*t*t + 0.000000371*t*t*t)
    core.lambda_0_t_user = lambda_0_t + offset
    print offset, lambda_0_t
    gui.lambda_naught_t_input.setText('%.3f' % core.lambda_0_t_user)
    calculate_pressure(core.lambda_r1)


def calculate_pressure(lambda_r1):
    print core.lambda_0_t_user
    core.pressure = core.alpha * ((1 / core.beta) * (((lambda_r1 / core.lambda_0_t_user) ** core.beta) - 1))
    gui.press_calc_label2.setText('%.2f' % core.pressure)

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
gui.initialize_inputs()
update()
sys.exit(app.exec_())
