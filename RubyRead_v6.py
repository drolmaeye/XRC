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
import os


class Window(QtGui.QMainWindow):

    def __init__(self):
        # use QMainWindow in this early version to benefit from menu, tool bar, etc.
        super(Window, self).__init__()
        self.setGeometry(100, 100, 1080, 720)
        self.setWindowTitle('RubyRead')
        self.setWindowIcon(QtGui.QIcon('ruby4.png'))
        # self.setStyleSheet('font-size: 10pt')

        # create the main window widget and make it central
        self.mw = QtGui.QWidget()
        self.setCentralWidget(self.mw)
        # now make and set layout for the mw (main window)
        self.mw_layout = QtGui.QVBoxLayout()
        self.mw.setLayout(self.mw_layout)

        '''
        Custom Toolbar
        '''

        # make custom toolbar for top of main window
        self.tb = QtGui.QWidget()
        self.tb_layout = QtGui.QHBoxLayout()
        self.tb_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.tb.setLayout(self.tb_layout)

        # make custom toolbar widgets
        self.take_spec_label = QtGui.QLabel('Collect')
        self.take_one_spec_btn = QtGui.QPushButton('1')
        self.take_n_spec_btn = QtGui.QPushButton('n')
        self.take_n_spec_btn.setCheckable(True)

        self.fit_spec_label = QtGui.QLabel('Fit')
        self.fit_one_spec_btn = QtGui.QPushButton('1')
        self.fit_n_spec_btn = QtGui.QPushButton('n')
        self.fit_n_spec_btn.setCheckable(True)

        # connect custom toolbar signals
        self.take_one_spec_btn.clicked.connect(lambda: start_timer(1))
        self.take_n_spec_btn.clicked.connect(lambda: start_timer(0))

        # add custom toolbar widgets to toolbar layout
        self.tb_layout.addWidget(self.take_spec_label)
        self.tb_layout.addWidget(self.take_one_spec_btn)
        self.tb_layout.addWidget(self.take_n_spec_btn)
        self.tb_layout.addSpacing(20)
        self.tb_layout.addWidget(self.fit_spec_label)
        self.tb_layout.addWidget(self.fit_one_spec_btn)
        self.tb_layout.addWidget(self.fit_n_spec_btn)

        # add custom toolbar to main window
        self.mw_layout.addWidget(self.tb)

        '''
        Plot Window
        '''

        # make the plot window for the left side of bottom layout
        self.pw = pg.PlotWidget(name='Plot1')

        # create plot items (need to be added when necessary)
        self.raw_data = pg.PlotDataItem()
        self.fit_data = pg.PlotDataItem()
        self.r1_data = pg.PlotDataItem()
        self.r2_data = pg.PlotDataItem()
        self.bg_data = pg.PlotDataItem()
        self.ref_data = pg.PlotDataItem()
        self.target_data = pg.PlotDataItem()

        self.vline_press = pg.InfiniteLine(pos=694.260, angle=90.0, movable=False)
        self.vline_ref = pg.InfiniteLine(pos=694.260, angle=90.0, movable=False)
        self.vline_target = pg.InfiniteLine(pos=694.260, angle=90.0, movable=True)

        # raw data is always visible, add rest when or as needed
        self.pw.addItem(self.raw_data)

        # create signal for target pressure line
        self.vline_target.sigPositionChanged.connect(self.target_line_moved)

        # make layout for plot window and control window and add to main window
        self.bottom_layout = QtGui.QHBoxLayout()
        self.mw_layout.addLayout(self.bottom_layout)

        # add plot widget to bottom layout
        self.bottom_layout.addWidget(self.pw)

        # make the control window for the right side and add it to main window layout
        self.cw = QtGui.QWidget()
        self.cw.setMaximumWidth(300)
        self.bottom_layout.addWidget(self.cw)

        # make the layout for the control widget
        self.cw_layout = QtGui.QVBoxLayout()
        # self.cw_layout.setAlignment(QtCore.Qt.AlignTop)
        self.cw.setLayout(self.cw_layout)

        '''
        Spectrum control window
        '''

        # make top right widget for spectrometer control
        self.spec_control = QtGui.QGroupBox()
        self.spec_control.setTitle('Spectrum Control')
        self.cw_layout.addWidget(self.spec_control)

        # make and set layout to Spectrum Control QGroupBox
        self.spec_control_layout = QtGui.QVBoxLayout()
        self.spec_control_layout.setAlignment(QtCore.Qt.AlignTop)
        # ###self.spec_control_layout.setSpacing(10)
        self.spec_control.setLayout(self.spec_control_layout)

        # ###make individual widgets to spec control grid layout

        # create count time label
        self.count_time_label = QtGui.QLabel('Integration time (ms)')
        # create, configure count time input
        self.count_time_input = QtGui.QLineEdit('100')
        self.count_time_input.setValidator(QtGui.QIntValidator())
        self.count_time_input.setMaxLength(4)
        # crate count time shortcut buttons
        self.count_less_button = QtGui.QPushButton('')
        self.count_less_button.setIcon(QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_ArrowLeft))
        self.count_less_button.setMinimumWidth(70)
        self.count_more_button = QtGui.QPushButton('')
        self.count_more_button.setIcon(QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_ArrowRight))
        self.count_more_button.setMinimumWidth(70)
        # create checkbox widget, create and configure spinbox widget
        self.average_spec_cbox = QtGui.QCheckBox('Average n spectra')
        self.average_spec_sbox = QtGui.QSpinBox()
        self.average_spec_sbox.setMaximumWidth(50)
        self.average_spec_sbox.setValue(1)
        self.average_spec_sbox.setMinimum(1)
        self.average_spec_sbox.setMaximum(10)

        # connect signals
        self.count_time_input.editingFinished.connect(self.update_count_time)
        self.count_less_button.clicked.connect(lambda: self.count_time_shortcut('down'))
        self.count_more_button.clicked.connect(lambda: self.count_time_shortcut('up'))

        # add widgets to layout
        self.spec_control_layout.addWidget(self.count_time_label)

        self.count_time_layout = QtGui.QHBoxLayout()
        self.count_time_layout.addWidget(self.count_less_button)
        self.count_time_layout.addWidget(self.count_time_input)
        self.count_time_layout.addWidget(self.count_more_button)
        self.spec_control_layout.addLayout(self.count_time_layout)

        self.average_spec_layout = QtGui.QHBoxLayout()
        self.average_spec_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.average_spec_layout.addWidget(self.average_spec_cbox)
        self.average_spec_layout.addWidget(self.average_spec_sbox)
        self.spec_control_layout.addLayout(self.average_spec_layout)

        '''
        Plot control window v2
        '''

        # make middle-right widget for plot control
        self.plot_control = QtGui.QGroupBox()
        self.plot_control.setTitle('Plot Control')
        self.cw_layout.addWidget(self.plot_control)

        # make and set primary layout for Plot Control QGroupBox
        self.plot_control_layout = QtGui.QVBoxLayout()
        self.plot_control_layout.setAlignment(QtCore.Qt.AlignTop)
        self.plot_control.setLayout(self.plot_control_layout)

        # ### make and add individual widgets to plot control

        # create show curves label and checkboxes
        self.show_fits_label = QtGui.QLabel('Select fitted data to show')
        self.show_fit_cbox = QtGui.QCheckBox('Fit')
        self.show_r1r2_cbox = QtGui.QCheckBox('R1, R2')
        self.show_bg_cbox = QtGui.QCheckBox('Background')
        #  create show reference lines labels, cboxes, data displays, data inputs
        self.show_refs_label = QtGui.QLabel('Select reference lines to show')
        self.show_fitted_p_cbox = QtGui.QCheckBox('P(fit)')
        self.show_reference_p_cbox = QtGui.QCheckBox('P(ref)')
        self.show_ref_p_lambda = QtGui.QLabel('694.260')
        self.show_ref_p_pressure = QtGui.QLabel('0.00')
        self.show_ref_p_delta = QtGui.QLabel('0.00')
        self.show_target_p_cbox = QtGui.QCheckBox('P(target)')
        self.show_target_p_lambda = QtGui.QLineEdit('694.260')
        self.show_target_p_pressure = QtGui.QLineEdit('0.00')
        self.show_target_p_delta = QtGui.QLineEdit('0.00')
        # create zoom buttons
        self.zoom_full_btn = QtGui.QPushButton('Full spectrum')
        self.zoom_roi_btn = QtGui.QPushButton('Zoom ROI')
        self.autoscale_cbox = QtGui.QCheckBox('Autoscale')

        # connect plot control signals
        self.show_fit_cbox.stateChanged.connect(self.show_fit_cbox_changed)
        self.show_r1r2_cbox.stateChanged.connect(self.show_r1r2_cbox_changed)
        self.show_bg_cbox.stateChanged.connect(self.show_bg_cbox_changed)
        self.show_reference_p_cbox.stateChanged.connect(self.show_reference_p_cbox_changed)
        self.show_target_p_cbox.stateChanged.connect(self.show_target_p_cbox_changed)
        self.show_target_p_lambda.editingFinished.connect(self.show_target_p_lambda_changed)
        self.show_target_p_pressure.editingFinished.connect(self.show_target_p_pressure_changed)
        self.show_target_p_delta.editingFinished.connect(self.show_target_p_delta_changed)
        self.zoom_full_btn.clicked.connect(self.zoom_full)
        self.zoom_roi_btn.clicked.connect(self.zoom_roi)

        # add widgets to layout
        self.plot_control_layout.addWidget(self.show_fits_label)

        self.reference_curves_layout = QtGui.QHBoxLayout()
        self.reference_curves_layout.addWidget(self.show_fit_cbox)
        self.reference_curves_layout.addWidget(self.show_r1r2_cbox)
        self.reference_curves_layout.addWidget(self.show_bg_cbox)
        self.plot_control_layout.addLayout(self.reference_curves_layout)

        self.plot_control_layout.addWidget(self.show_refs_label)

        self.reference_lines_layout = QtGui.QGridLayout()
        self.reference_lines_layout.addWidget(self.show_fitted_p_cbox, 0, 0)
        self.reference_lines_layout.addWidget(self.show_reference_p_cbox, 1, 0)
        self.reference_lines_layout.addWidget(self.show_ref_p_lambda, 1, 1)
        self.reference_lines_layout.addWidget(self.show_ref_p_pressure, 1, 2)
        self.reference_lines_layout.addWidget(self.show_ref_p_delta, 1, 3)
        self.reference_lines_layout.addWidget(self.show_target_p_cbox, 2, 0)
        self.reference_lines_layout.addWidget(self.show_target_p_lambda, 2, 1)
        self.reference_lines_layout.addWidget(self.show_target_p_pressure, 2, 2)
        self.reference_lines_layout.addWidget(self.show_target_p_delta, 2, 3)
        self.plot_control_layout.addLayout(self.reference_lines_layout)

        self.zoom_buttons_layout = QtGui.QHBoxLayout()
        self.zoom_buttons_layout.addWidget(self.zoom_full_btn)
        self.zoom_buttons_layout.addWidget(self.zoom_roi_btn)
        self.zoom_buttons_layout.addWidget(self.autoscale_cbox)
        self.plot_control_layout.addLayout(self.zoom_buttons_layout)

        '''
        Pressure Control Window
        '''

        # make bottom right widget for Pressure control
        self.press_control = QtGui.QGroupBox()
        self.press_control.setTitle('Pressure Control')
        self.cw_layout.addWidget(self.press_control)

        # make and add primary layout to Pressure Control QGroupBox
        self.press_control_layout = QtGui.QGridLayout()
        self.press_control_layout.setAlignment(QtCore.Qt.AlignTop)
        self.press_control.setLayout(self.press_control_layout)

        # ###make and add individual widgets to press control layout

        # create pressure control widgets
        self.press_calibration_label = QtGui.QLabel('Pressure Calibration')
        self.press_calibration_display = QtGui.QLabel('Dorogokupets')
        self.lambda_naught_295_label = QtGui.QLabel(u'\u03BB' + '<sub>0</sub>' + '(295)' + ' (nm)')
        self.lambda_naught_295_display = QtGui.QLabel('694.260')
        self.lambda_naught_t_label = QtGui.QLabel(u'\u03BB' + '<sub>0</sub>' + '(T)' + ' (nm)')
        self.lambda_naught_t_display = QtGui.QLabel('694.260')
        self.lambda_r1_label = QtGui.QLabel(u'\u03BB' + '<sub>R1</sub>' + ' (nm)')
        self.lambda_r1_display = QtGui.QLabel('694.260')
        self.temperature_label = QtGui.QLabel('Temperature (K)')
        self.temperature_input = QtGui.QSpinBox()
        self.temperature_input.setRange(4, 600)
        self.temperature_input.setValue(295)
        self.temperature_track_cbox = QtGui.QCheckBox('Track')
        self.threshold_label = QtGui.QLabel('Fit thresholds')
        self.threshold_min_input = QtGui.QLineEdit('200')
        self.threshold_min_input.setValidator(QtGui.QIntValidator())
        self.threshold_warning_label = QtGui.QLabel('')
        self.pressure_fit_label = QtGui.QLabel('Pressure(fit) (GPa)')
        self.pressure_fit_display = QtGui.QLabel('0.00')
        self.press_fit_cbox = QtGui.QCheckBox('Fit')

        # connect pressure control signals
        self.temperature_input.valueChanged.connect(self.calculate_lambda_0_t)

        # add pressure control widgets to pressure control layout
        self.press_control_layout.addWidget(self.press_calibration_label, 0, 0)
        self.press_control_layout.addWidget(self.press_calibration_display, 0, 1)
        self.press_control_layout.addWidget(self.lambda_naught_295_label, 1, 0)
        self.press_control_layout.addWidget(self.lambda_naught_295_display, 1, 1)
        self.press_control_layout.addWidget(self.lambda_naught_t_label, 2, 0)
        self.press_control_layout.addWidget(self.lambda_naught_t_display, 2, 1)
        self.press_control_layout.addWidget(self.lambda_r1_label, 3, 0)
        self.press_control_layout.addWidget(self.lambda_r1_display, 3, 1)
        self.press_control_layout.addWidget(self.temperature_label, 4, 0)
        self.press_control_layout.addWidget(self.temperature_input, 4, 1)
        self.press_control_layout.addWidget(self.temperature_track_cbox, 4, 2)
        self.press_control_layout.addWidget(self.threshold_label, 5, 0)
        self.press_control_layout.addWidget(self.threshold_min_input, 5, 1)
        self.press_control_layout.addWidget(self.threshold_warning_label, 5, 2)
        self.press_control_layout.addWidget(self.pressure_fit_label, 6, 0)
        self.press_control_layout.addWidget(self.pressure_fit_display, 6, 1)
        self.press_control_layout.addWidget(self.press_fit_cbox, 6, 2)

        # experimenting with stylesheets

        # from Clemens' Dioptas
        # file = open(os.path.join("stylesheet.qss"))
        # stylesheet = file.read()
        # self.setStyleSheet(stylesheet)
        # file.close()

        # ###file = open(os.path.join("DarkStyle.qss"))
        # ###stylesheet = file.read()
        # ###self.setStyleSheet(stylesheet)
        # ###file.close()

        # huzzah
        self.show()

    '''
    Class methods
    '''

    # class methods for spectrum control
    def update_count_time(self):
        count_time = int(self.count_time_input.text()) * 1000
        core.spec.integration_time_micros(count_time)

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

    # class methods for plot control
    def show_fit_cbox_changed(self):
        if self.show_fit_cbox.isChecked():
            self.pw.addItem(self.fit_data)
            self.pw.addItem(self.vline_press)
        else:
            self.pw.removeItem(self.fit_data)
            self.pw.removeItem(self.vline_press)

    def show_r1r2_cbox_changed(self):
        if self.show_r1r2_cbox.isChecked():
            self.pw.addItem(self.r1_data)
            self.pw.addItem(self.r2_data)
        else:
            self.pw.removeItem(self.r1_data)
            self.pw.removeItem(self.r2_data)

    def show_bg_cbox_changed(self):
        if self.show_bg_cbox.isChecked():
            self.pw.addItem(self.bg_data)
        else:
            self.pw.removeItem(self.bg_data)

    def show_reference_p_cbox_changed(self):
        if self.show_reference_p_cbox.isChecked():
            self.pw.addItem(self.vline_ref)
        else:
            self.pw.removeItem(self.vline_ref)

    def show_target_p_cbox_changed(self):
        if self.show_target_p_cbox.isChecked():
            self.pw.addItem(self.vline_target)
        else:
            self.pw.removeItem(self.vline_target)

    def show_target_p_lambda_changed(self):
        target_lambda = float(self.show_target_p_lambda.text())
        self.vline_target.setX(target_lambda)
        self.calculate_target_pressure(target_lambda)

    def show_target_p_pressure_changed(self):
        target_pressure = float(self.show_target_p_pressure.text())
        target_lambda = core.lambda_0_t_user * ((target_pressure * core.beta / core.alpha + 1) ** (1 / core.beta))
        self.vline_target.setX(target_lambda)
        self.show_target_p_lambda.setText('%.3f' % target_lambda)
        self.calculate_deltas()

    def show_target_p_delta_changed(self):
        delta_p = float(self.show_target_p_delta.text())
        fit_p = float(self.pressure_fit_display.text())
        target_p = fit_p + delta_p
        self.show_target_p_pressure.setText('%.2f' % target_p)
        self.show_target_p_pressure_changed()

    def target_line_moved(self):
        target_lambda = self.vline_target.getXPos()
        self.show_target_p_lambda.setText('%.3f' % target_lambda)
        self.calculate_target_pressure(target_lambda)
        self.calculate_deltas()

    def calculate_target_p_lambda(self):
        target_pressure = float(self.show_target_p_pressure.text())
        target_lambda = core.lambda_0_t_user * ((target_pressure * core.beta / core.alpha + 1) ** (1 / core.beta))
        self.show_target_p_lambda.setText('%.3f' % target_lambda)
        self.show_target_p_lambda_changed()

    def calculate_target_pressure(self, lambda_r1):
        target_pressure = core.alpha * ((1 / core.beta) * (((lambda_r1 / core.lambda_0_t_user) ** core.beta) - 1))
        self.show_target_p_pressure.setText('%.2f' % target_pressure)
        self.calculate_deltas()

    def calculate_deltas(self):
        fit_p = float(self.pressure_fit_display.text())
        ref_p = float(self.show_ref_p_pressure.text())
        target_p = float(self.show_target_p_pressure.text())
        self.show_ref_p_delta.setText('%.2f' % (ref_p - fit_p))
        self.show_target_p_delta.setText('%.2f' % (target_p - fit_p))

    def zoom_full(self):
        self.pw.setXRange(core.xs[0], core.xs[-1])

    def zoom_roi(self):
        self.pw.setXRange(core.xs_roi[0], core.xs_roi[-1])

    # class methods for pressure control
    def calculate_lambda_0_t(self):
        offset = core.lambda_0_user - core.lambda_0_ref
        t = self.temperature_input.value()
        lambda_0_t = 10000000 / (14423.0 + 0.0446*t - 0.000481*t*t + 0.000000371*t*t*t)
        core.lambda_0_t_user = lambda_0_t + offset
        self.lambda_naught_t_display.setText('%.3f' % core.lambda_0_t_user)
        calculate_pressure(core.lambda_r1)
        self.calculate_target_p_lambda()


class CoreData:
    def __init__(self):
        self.stopped = True
        self.ptrn = 0

        self.devices = sb.list_devices()
        self.spec = sb.Spectrometer(self.devices[0])
        self.spec.integration_time_micros(100000)

        self.xs = self.spec.wavelengths()
        self.ys = self.spec.intensities()
        self.xs_roi = np.zeros(300)
        self.ys_roi = np.zeros(300)

        self.timer = QtCore.QTimer()

        # pressure calculation parameters
        # lambda zero (ref) is 694.260 based on Ragan et al JAP 72, 5539 (1992) at 295K
        self.alpha = 1885
        self.beta = 11.0
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
        num = gui.average_spec_sbox.value()
        for each in range(num - 1):
            core.ys += core.spec.intensities()
        core.ys = core.ys/num
    gui.raw_data.setData(core.xs, core.ys)

    if gui.press_fit_cbox.isChecked():
        fit_spectrum()


def fit_spectrum():
    # start by defining ROI arrays and get max_index for ROI
    full_max_index = np.argmax(core.ys)
    core.xs_roi = core.xs[full_max_index - 150:full_max_index + 150]
    core.ys_roi = core.ys[full_max_index - 150:full_max_index + 150]
    roi_max_index = np.argmax(core.ys_roi)

    # start with approximate linear background (using full spectrum)
    slope = (core.ys[-1] - core.ys[0]) / (core.xs[-1] - core.xs[0])
    intercept = core.ys[0] - slope * core.xs[0]

    # obtain initial guesses for fitting parameters using ROI array
    r1_pos = core.xs_roi[roi_max_index]
    r2_pos = r1_pos - 1.4
    r1_height = core.ys_roi[roi_max_index] - (slope * r1_pos + intercept)
    r2_height = r1_height / 2.0

    # check r1_height is greater than fitting threshold and not saturated
    threshold = int(gui.threshold_min_input.text())
    if r1_height < threshold:
        gui.threshold_warning_label.setText('Too weak')
        return
    elif core.ys_roi[roi_max_index] > 16000:
        gui.threshold_warning_label.setText('Saturated')
        return
    else:
        gui.threshold_warning_label.setText('')

    # define fitting parameters p0 (area approximated by height)
    p0 = [r2_height, r2_pos, 0.5, 1.0, r1_height, r1_pos, 0.5, 1.0, slope, intercept]
    # fit
    popt, pcov = curve_fit(double_pseudo, core.xs, core.ys, p0=p0)

    gui.lambda_r1_display.setText('%.3f' % popt[5])

    gui.fit_data.setData(core.xs_roi, double_pseudo(core.xs_roi, *popt), pen=(255, 0, 0))
    gui.r1_data.setData(core.xs_roi, pseudo(core.xs_roi, popt[4], popt[5], popt[6], popt[7], popt[8], popt[9]))
    gui.r2_data.setData(core.xs_roi, pseudo(core.xs_roi, popt[0], popt[1], popt[2], popt[3], popt[8], popt[9]))
    gui.bg_data.setData(core.xs_roi, (popt[8] * core.xs_roi + popt[9]))

    # calculate pressure
    core.lambda_r1 = popt[5]
    calculate_pressure(core.lambda_r1)
    gui.vline_press.setPos(popt[5])


def calculate_pressure(lambda_r1):
    core.pressure = core.alpha * ((1 / core.beta) * (((lambda_r1 / core.lambda_0_t_user) ** core.beta) - 1))
    gui.pressure_fit_display.setText('%.2f' % core.pressure)
    gui.calculate_deltas()


def calculate_target_pressure(lambda_r1):
    target_pressure = core.alpha * ((1 / core.beta) * (((lambda_r1 / core.lambda_0_t_user) ** core.beta) - 1))
    gui.show_target_p_pressure.setText('%.2f' % target_pressure)


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


app = QtGui.QApplication(sys.argv)
core = CoreData()
gui = Window()
pg.setConfigOptions(antialias=True)
update()
sys.exit(app.exec_())
