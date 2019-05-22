__author__ = 'j.smith'

'''
A GUI for measuring ruby pressure with Ocean Optics spectrometer

build command for pyinstaller: pyinstaller -F --add-binary "ca.dll'." RubyRead_vXX.py
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
from epics import PV
from pyqtgraph.GraphicsScene import exportDialog
import os


class Window(QtGui.QMainWindow):

    def __init__(self):
        # use QMainWindow in this early version to benefit from menu, tool bar, etc.
        super(Window, self).__init__()
        self.setGeometry(100, 100, 1080, 720)
        self.setWindowTitle('RubyRead beta')
        self.setWindowIcon(QtGui.QIcon('ruby4.png'))
        # self.setStyleSheet('font-size: 10pt')

        # create the main window widget and make it central
        self.mw = QtGui.QWidget()
        self.setCentralWidget(self.mw)
        # now make and set layout for the mw (main window)
        self.mw_layout = QtGui.QVBoxLayout()
        self.mw.setLayout(self.mw_layout)

        '''
        Menu bar
        '''

        # actions
        self.load_data_action = QtGui.QAction('Load', self)
        self.load_data_action.setShortcut('Ctrl+L')
        self.load_data_action.triggered.connect(self.load_data)

        self.save_data_action = QtGui.QAction('Save', self)
        self.save_data_action.setShortcut('Ctrl+S')
        self.save_data_action.triggered.connect(self.save_data)

        self.close_rubyread_action = QtGui.QAction('Exit', self)
        self.close_rubyread_action.setShortcut('Ctrl+Q')
        self.close_rubyread_action.triggered.connect(self.closeEvent)

        self.options_window_action = QtGui.QAction('Options', self)
        self.options_window_action.setShortcut('Ctrl+O')
        self.options_window_action.triggered.connect(lambda: self.ow.show())

        self.about_window_action = QtGui.QAction('About', self)
        self.about_window_action.setShortcut('Ctrl+A')
        self.about_window_action.triggered.connect(lambda: self.aw.show())

        # make menu, add headings, put actions under headings
        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu('File')
        self.file_menu.addAction(self.load_data_action)
        self.file_menu.addAction(self.save_data_action)
        self.file_menu.addAction(self.close_rubyread_action)
        self.options_menu = self.main_menu.addMenu('Options')
        self.options_menu.addAction(self.options_window_action)
        self.about_menu = self.main_menu.addMenu('About')
        self.about_menu.addAction(self.about_window_action)

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
        self.take_one_spec_btn.setShortcut(QtCore.Qt.Key_F1)
        self.take_one_spec_btn.setToolTip('Collect one spectrum (F1)')
        self.take_n_spec_btn = QtGui.QPushButton('n')
        self.take_n_spec_btn.setShortcut(QtCore.Qt.Key_F2)
        self.take_n_spec_btn.setToolTip('Continuously collect spectra (F2)')
        self.take_n_spec_btn.setCheckable(True)

        self.remaining_time_display = QtGui.QLabel('Idle')
        self.remaining_time_display.setFrameShape(QtGui.QFrame.Panel)
        self.remaining_time_display.setFrameShadow(QtGui.QFrame.Sunken)
        self.remaining_time_display.setMinimumWidth(80)
        self.remaining_time_display.setAlignment(QtCore.Qt.AlignCenter)
        self.remaining_time_display.setToolTip('Remaining collection time (s)')

        self.fit_spec_label = QtGui.QLabel('Fit')
        self.fit_one_spec_btn = QtGui.QPushButton('1')
        self.fit_one_spec_btn.setShortcut(QtCore.Qt.Key_F3)
        self.fit_one_spec_btn.setToolTip('Fit one spectrum (F3)')
        self.fit_n_spec_btn = QtGui.QPushButton('n')
        self.fit_n_spec_btn.setShortcut(QtCore.Qt.Key_F4)
        self.fit_n_spec_btn.setToolTip('Continuously fit spectra (F4)')
        self.fit_n_spec_btn.setCheckable(True)

        self.fit_warning_display = QtGui.QLabel('')
        self.fit_warning_display.setFrameShape(QtGui.QFrame.Panel)
        self.fit_warning_display.setFrameShadow(QtGui.QFrame.Sunken)
        self.fit_warning_display.setMinimumWidth(80)
        self.fit_warning_display.setAlignment(QtCore.Qt.AlignCenter)
        self.fit_warning_display.setToolTip('Fit warning')

        self.threshold_label = QtGui.QLabel('Fit threshold')
        self.threshold_min_input = QtGui.QSpinBox()
        self.threshold_min_input.setRange(0, 16000)
        self.threshold_min_input.setValue(1000)
        self.threshold_min_input.setSingleStep(100)
        self.threshold_min_input.setMinimumWidth(70)

        self.test_9000_btn = QtGui.QPushButton('Test 9000')
        self.test_9999_btn = QtGui.QPushButton('Test 9999')

        # connect custom toolbar signals
        self.take_one_spec_btn.clicked.connect(self.take_one_spectrum)
        self.take_n_spec_btn.clicked.connect(self.take_n_spectra)
        self.fit_one_spec_btn.clicked.connect(self.fit_one_spectrum)
        self.fit_n_spec_btn.clicked.connect(self.fit_n_spectra)
        self.threshold_min_input.valueChanged.connect(self.set_threshold)
        self.test_9000_btn.clicked.connect(self.test_9000)
        self.test_9999_btn.clicked.connect(self.test_9999)

        # add custom toolbar widgets to toolbar layout
        self.tb_layout.addWidget(self.take_spec_label)
        self.tb_layout.addWidget(self.take_one_spec_btn)
        self.tb_layout.addWidget(self.take_n_spec_btn)
        self.tb_layout.addWidget(self.remaining_time_display)
        self.tb_layout.addSpacing(20)

        self.tb_layout.addWidget(self.fit_spec_label)
        self.tb_layout.addWidget(self.fit_one_spec_btn)
        self.tb_layout.addWidget(self.fit_n_spec_btn)
        self.tb_layout.addWidget(self.fit_warning_display)
        self.tb_layout.addSpacing(20)

        self.tb_layout.addWidget(self.threshold_label)
        self.tb_layout.addWidget(self.threshold_min_input)
        self.tb_layout.addSpacing(20)

        # self.tb_layout.addWidget(self.test_9000_btn)
        # self.tb_layout.addWidget(self.test_9999_btn)

        # add custom toolbar to main window
        self.mw_layout.addWidget(self.tb)

        '''
        Plot Window
        '''

        # make the plot window for the left side of bottom layout
        # custom viewbox, vb, allows for custom button event handling
        self.pw = pg.PlotWidget(viewBox=vb, name='Plot1')

        # ###EXPERIMENT WITH STYLE###
        # self.pw.setTitle('Spectrum', size='12pt')
        # label_style = {'color': '#808080', 'font-size': '11px'}
        label_style = {'color': '#808080', 'font': ' bold 16px'}
        self.pw.plotItem.getAxis('left').enableAutoSIPrefix(False)
        self.pw.setLabel('left', 'Intensity', units='counts', **label_style)
        self.pw.setLabel('bottom', 'Wavelength', units='nm', **label_style)

        # create plot items (need to be added when necessary)
        self.raw_data = pg.PlotDataItem(name='raw')
        self.fit_data = pg.PlotDataItem(name='fit')
        self.r1_data = pg.PlotDataItem(name='r1')
        self.r2_data = pg.PlotDataItem(name='r2')
        self.bg_data = pg.PlotDataItem(name='bg')

        # stylize plot items
        self.fit_data.setPen(color='r', width=2)
        self.r1_data.setPen(color='g')
        self.r2_data.setPen(color='g')
        self.bg_data.setPen(color='c')

        line_dict = {'angle': 90, 'fill': 'k'}
        self.vline_press = pg.InfiniteLine(pos=694.260, angle=90.0, movable=False,
                                           pen='g', label='Fit', labelOpts=line_dict)
        self.vline_ref = pg.InfiniteLine(pos=694.260, angle=90.0, movable=False,
                                         pen='m', label='Reference', labelOpts=line_dict)
        self.vline_target = pg.InfiniteLine(pos=694.260, angle=90.0, movable=True,
                                            pen='y', label='Target', labelOpts=line_dict)

        # raw data is always visible, add rest when or as needed
        self.pw.addItem(self.raw_data)

        # create signal for target pressure line
        self.vline_target.sigPositionChanged.connect(self.target_line_moved)

        # ###LAYOUT MANAGEMENT###
        # make layout for plot window and control window and add to main window
        self.bottom_layout = QtGui.QHBoxLayout()
        self.mw_layout.addLayout(self.bottom_layout)

        # add plot widget to bottom layout
        self.bottom_layout.addWidget(self.pw)

        '''
        Control Window
        '''

        # make the control window for the right side and add it to main window layout
        self.cw = QtGui.QWidget()
        self.cw.setMaximumWidth(300)
        self.bottom_layout.addWidget(self.cw)

        # make the layout for the control widget
        self.cw_layout = QtGui.QVBoxLayout()
        self.cw_layout.setAlignment(QtCore.Qt.AlignTop)
        self.cw.setLayout(self.cw_layout)

        '''
        Spectrum control window
        '''

        # make top right widget for spectrometer control
        self.spec_control = QtGui.QGroupBox()
        self.spec_control.setTitle('Spectrum Control')
        self.cw_layout.addWidget(self.spec_control)
        self.cw_layout.addSpacing(10)

        # make and set layout to Spectrum Control QGroupBox
        self.spec_control_layout = QtGui.QVBoxLayout()
        self.spec_control_layout.setAlignment(QtCore.Qt.AlignTop)
        self.spec_control.setLayout(self.spec_control_layout)

        # ###make individual widgets to spec control grid layout

        # create count time label
        self.count_time_label = QtGui.QLabel('Integration time (ms)')
        # create, configure count time input
        self.count_time_input = QtGui.QLineEdit('100')
        self.count_time_input.setStyleSheet('font: bold 18px')
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
        self.average_spec_cbox.stateChanged.connect(self.toggle_average)
        self.average_spec_sbox.valueChanged.connect(self.set_num_average)

        # add widgets to layout
        self.spec_control_layout.addWidget(self.count_time_label)

        self.count_time_layout = QtGui.QHBoxLayout()
        self.count_time_layout.addWidget(self.count_less_button)
        self.count_time_layout.addWidget(self.count_time_input)
        self.count_time_layout.addWidget(self.count_more_button)
        self.spec_control_layout.addLayout(self.count_time_layout)

        self.spec_control_layout.addSpacing(10)

        self.average_spec_layout = QtGui.QHBoxLayout()
        self.average_spec_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.average_spec_layout.addWidget(self.average_spec_cbox)
        self.average_spec_layout.addWidget(self.average_spec_sbox)
        self.spec_control_layout.addLayout(self.average_spec_layout)

        '''
        Plot control window
        '''

        # make middle-right widget for plot control
        self.plot_control = QtGui.QGroupBox()
        self.plot_control.setTitle('Plot Control')
        self.cw_layout.addWidget(self.plot_control)
        self.cw_layout.addSpacing(10)

        # make and set primary layout for Plot Control QGroupBox
        self.plot_control_layout = QtGui.QVBoxLayout()
        self.plot_control_layout.setAlignment(QtCore.Qt.AlignTop)
        self.plot_control.setLayout(self.plot_control_layout)

        # ### make and add individual widgets to plot control

        # custom checked styles for checkbuttons
        showcurve_style = 'QPushButton::checked {border:4px solid red}'
        showr1r2_style = 'QPushButton::checked {border:4px solid green}'
        showbg_style = 'QPushButton::checked {border:4px solid cyan}'
        showfit_style = 'QPushButton::checked {border:4px solid green}'
        showref_style = 'QPushButton::checked {border:4px solid magenta}'
        showtarget_style = 'QPushButton::checked {border:4px solid yellow}'

        # create and style all show checkbuttons
        self.show_fits_label = QtGui.QLabel('Show fitted data')
        self.show_curve_cbtn = QtGui.QPushButton('Curve')
        self.show_curve_cbtn.setCheckable(True)
        self.show_curve_cbtn.setStyleSheet(showcurve_style)
        self.show_r1r2_cbtn = QtGui.QPushButton('R1, R2')
        self.show_r1r2_cbtn.setCheckable(True)
        self.show_r1r2_cbtn.setStyleSheet(showr1r2_style)
        self.show_bg_cbtn = QtGui.QPushButton('Background')
        self.show_bg_cbtn.setCheckable(True)
        self.show_bg_cbtn.setStyleSheet(showbg_style)
        self.show_fit_p_cbtn = QtGui.QPushButton('P(fit)')
        self.show_fit_p_cbtn.setCheckable(True)
        self.show_fit_p_cbtn.setStyleSheet(showfit_style)
        self.show_ref_p_cbtn = QtGui.QPushButton('P(ref)')
        self.show_ref_p_cbtn.setCheckable(True)
        self.show_ref_p_cbtn.setStyleSheet(showref_style)
        self.show_target_p_cbtn = QtGui.QPushButton('P(target)')
        self.show_target_p_cbtn.setCheckable(True)
        self.show_target_p_cbtn.setStyleSheet(showtarget_style)

        # create labels, headings, displays, and inputs for marker locations
        self.show_refs_label = QtGui.QLabel('Show pressure markers')
        self.markers_lambda_heading = QtGui.QLabel(u'\u03BB' + ' (nm)')
        self.markers_pressure_heading = QtGui.QLabel('P (GPa)')
        self.markers_delta_p_heading = QtGui.QLabel(u'\u0394' + 'P (GPa)')
        self.show_ref_p_lambda = QtGui.QLabel('694.260')
        self.show_ref_p_pressure = QtGui.QLabel('0.00')
        self.show_ref_p_delta = QtGui.QLabel('0.00')
        self.show_target_p_lambda = QtGui.QLineEdit('694.260')
        self.show_target_p_lambda.setValidator(QtGui.QDoubleValidator(669.000, 767.000, 3))
        self.show_target_p_pressure = QtGui.QLineEdit('0.00')
        self.show_target_p_pressure.setValidator(QtGui.QDoubleValidator(-57.00, 335.00, 2))
        self.show_target_p_delta = QtGui.QLineEdit('0.00')
        self.show_target_p_delta.setValidator(QtGui.QDoubleValidator(-57.00, 335.00, 2))
        # create buttons to define reference
        self.set_ref_p_label = QtGui.QLabel('Set P(ref) position')
        self.set_ref_from_zero_btn = QtGui.QPushButton('from Zero')
        self.set_ref_from_fit_btn = QtGui.QPushButton('from Fit')
        self.set_ref_from_target_btn = QtGui.QPushButton('from Target')
        # create buttons for y-scale control
        self.set_y_scaling_label = QtGui.QLabel('Intensity scaling')
        self.auto_y_btn = QtGui.QPushButton('Auto')
        self.grow_y_btn = QtGui.QPushButton('Grow')
        self.fix_y_btn = QtGui.QPushButton('Fix')
        self.auto_y_btn.setCheckable(True)
        self.grow_y_btn.setCheckable(True)
        self.fix_y_btn.setCheckable(True)
        self.auto_y_btn.setChecked(True)
        self.scale_y_btn_grp = QtGui.QButtonGroup()
        self.scale_y_btn_grp.addButton(self.auto_y_btn, 0)
        self.scale_y_btn_grp.addButton(self.grow_y_btn, 1)
        self.scale_y_btn_grp.addButton(self.fix_y_btn, 2)

        # connect plot control signals
        self.show_curve_cbtn.clicked.connect(self.show_curve_cbtn_clicked)
        self.show_r1r2_cbtn.clicked.connect(self.show_r1r2_cbtn_clicked)
        self.show_bg_cbtn.clicked.connect(self.show_bg_cbtn_clicked)
        self.show_fit_p_cbtn.clicked.connect(self.show_fit_p_cbtn_clicked)
        self.show_ref_p_cbtn.clicked.connect(self.show_ref_p_cbtn_clicked)
        self.show_target_p_cbtn.clicked.connect(self.show_target_p_cbtn_clicked)
        self.show_target_p_lambda.editingFinished.connect(self.show_target_p_lambda_changed)
        self.show_target_p_pressure.editingFinished.connect(self.show_target_p_pressure_changed)
        self.show_target_p_delta.editingFinished.connect(self.show_target_p_delta_changed)
        self.set_ref_from_zero_btn.clicked.connect(self.set_ref_from_zero)
        self.set_ref_from_fit_btn.clicked.connect(self.set_ref_from_fit)
        self.set_ref_from_target_btn.clicked.connect(self.set_ref_from_target)
        self.auto_y_btn.clicked.connect(lambda: vb.enableAutoRange(axis=vb.YAxis))
        self.grow_y_btn.clicked.connect(lambda: vb.disableAutoRange())
        self.fix_y_btn.clicked.connect(lambda: vb.disableAutoRange())

        # add widgets to layout
        self.plot_control_layout.addWidget(self.show_fits_label)

        self.reference_curves_layout = QtGui.QHBoxLayout()
        self.reference_curves_layout.addWidget(self.show_curve_cbtn)
        self.reference_curves_layout.addWidget(self.show_r1r2_cbtn)
        self.reference_curves_layout.addWidget(self.show_bg_cbtn)
        self.plot_control_layout.addLayout(self.reference_curves_layout)

        self.plot_control_layout.addSpacing(10)

        self.plot_control_layout.addWidget(self.show_refs_label)

        self.reference_lines_layout = QtGui.QGridLayout()
        self.reference_lines_layout.addWidget(self.show_fit_p_cbtn, 1, 0)
        self.reference_lines_layout.addWidget(self.markers_lambda_heading, 1, 1)
        self.reference_lines_layout.addWidget(self.markers_pressure_heading, 1, 2)
        self.reference_lines_layout.addWidget(self.markers_delta_p_heading, 1, 3)
        self.reference_lines_layout.addWidget(self.show_ref_p_cbtn, 2, 0)
        self.reference_lines_layout.addWidget(self.show_ref_p_lambda, 2, 1)
        self.reference_lines_layout.addWidget(self.show_ref_p_pressure, 2, 2)
        self.reference_lines_layout.addWidget(self.show_ref_p_delta, 2, 3)
        self.reference_lines_layout.addWidget(self.show_target_p_cbtn, 3, 0)
        self.reference_lines_layout.addWidget(self.show_target_p_lambda, 3, 1)
        self.reference_lines_layout.addWidget(self.show_target_p_pressure, 3, 2)
        self.reference_lines_layout.addWidget(self.show_target_p_delta, 3, 3)
        self.plot_control_layout.addLayout(self.reference_lines_layout)

        self.plot_control_layout.addSpacing(10)

        self.plot_control_layout.addWidget(self.set_ref_p_label)

        self.set_reference_layout = QtGui.QHBoxLayout()
        self.set_reference_layout.addWidget(self.set_ref_from_zero_btn)
        self.set_reference_layout.addWidget(self.set_ref_from_fit_btn)
        self.set_reference_layout.addWidget(self.set_ref_from_target_btn)
        self.plot_control_layout.addLayout(self.set_reference_layout)

        self.plot_control_layout.addSpacing(10)

        self.plot_control_layout.addWidget(self.set_y_scaling_label)

        self.zoom_buttons_layout = QtGui.QHBoxLayout()
        self.zoom_buttons_layout.addWidget(self.auto_y_btn)
        self.zoom_buttons_layout.addWidget(self.grow_y_btn)
        self.zoom_buttons_layout.addWidget(self.fix_y_btn)
        self.plot_control_layout.addLayout(self.zoom_buttons_layout)

        '''
        Pressure Control window
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
        self.press_calibration_label = QtGui.QLabel('Calibration')
        self.press_calibration_display = QtGui.QLabel('Dorogokupets and Oganov (2007)')
        self.lambda_naught_295_label = QtGui.QLabel(u'\u03BB' + '<sub>0</sub>' + '(295)' + ' (nm)')
        self.lambda_naught_295_display = QtGui.QLabel('694.260')
        self.lambda_naught_t_label = QtGui.QLabel(u'\u03BB' + '<sub>0</sub>' + '(T)' + ' (nm)')
        self.lambda_naught_t_display = QtGui.QLabel('694.260')
        self.lambda_r1_label = QtGui.QLabel(u'\u03BB' + '<sub>R1</sub>' + ' (nm)')
        self.lambda_r1_display = QtGui.QLabel('694.260')
        self.temperature_label = QtGui.QLabel('T(K)')
        self.temperature_label.setStyleSheet('QLabel {font: bold 18px}')
        self.temperature_input = QtGui.QSpinBox()
        self.temperature_input.setStyleSheet('QSpinBox {font: bold 24px}')
        self.temperature_input.setRange(4, 600)
        self.temperature_input.setValue(295)
        self.temperature_track_cbox = QtGui.QCheckBox('Track')
        self.temperature_track_cbox.setEnabled(False)
        self.pressure_fit_label = QtGui.QLabel('P(GPa)')
        self.pressure_fit_label.setStyleSheet('QLabel {font: bold 18px}')
        self.pressure_fit_display = QtGui.QLabel('0.00')
        self.pressure_fit_display.setMinimumWidth(100)
        self.pressure_fit_display.setStyleSheet('QLabel {font: bold 36px}')


        # connect pressure control signals
        self.temperature_input.valueChanged.connect(self.calculate_lambda_0_t)

        # add pressure control widgets to pressure control layout
        self.press_control_layout.addWidget(self.press_calibration_label, 0, 0)
        self.press_control_layout.addWidget(self.press_calibration_display, 0, 1, 1, 2)
        self.press_control_layout.addWidget(self.lambda_naught_295_label, 1, 0)
        self.press_control_layout.addWidget(self.lambda_naught_295_display, 1, 1)
        self.press_control_layout.addWidget(self.lambda_naught_t_label, 2, 0)
        self.press_control_layout.addWidget(self.lambda_naught_t_display, 2, 1)
        self.press_control_layout.addWidget(self.lambda_r1_label, 3, 0)
        self.press_control_layout.addWidget(self.lambda_r1_display, 3, 1)
        self.press_control_layout.addWidget(self.temperature_label, 4, 0)
        self.press_control_layout.addWidget(self.temperature_input, 4, 1)
        self.press_control_layout.addWidget(self.temperature_track_cbox, 4, 2)
        self.press_control_layout.addWidget(self.pressure_fit_label, 5, 0)
        self.press_control_layout.addWidget(self.pressure_fit_display, 5, 1)

        '''
        Options window
        '''

        self.ow = QtGui.QTabWidget()
        self.ow.setWindowTitle('Options')

        # ###PRESSURE CALIBRATION###
        # make pressure calibration tab
        self.p_calibration_tab = QtGui.QWidget()
        self.p_calibration_tab_layout = QtGui.QVBoxLayout()
        self.p_calibration_tab.setLayout(self.p_calibration_tab_layout)

        # make Group Box for lambda naught
        self.set_lambda_naught_gb = QtGui.QGroupBox()
        self.set_lambda_naught_gb.setTitle('Reference wavelength')
        self.p_calibration_tab_layout.addWidget(self.set_lambda_naught_gb)
        self.set_lambda_naught_gb_layout = QtGui.QVBoxLayout()
        self.set_lambda_naught_gb.setLayout(self.set_lambda_naught_gb_layout)

        # make widgets for lambda naught
        self.manual_lambda_naught_label = QtGui.QLabel('Enter user-defined ' + u'\u03BB' + '<sub>0</sub>' + '(295)')
        self.manual_lambda_naught_input = QtGui.QLineEdit('694.260')
        self.manual_lambda_naught_input.setValidator(QtGui.QDoubleValidator(692.000, 696.000, 3))
        self.auto_lambda_naught_btn = QtGui.QPushButton('Get ' + u'\u03BB' + '(295) from fit')

        # connect signals
        self.manual_lambda_naught_input.returnPressed.connect(lambda: self.set_lambda_naught('manual'))
        self.auto_lambda_naught_btn.clicked.connect(lambda: self.set_lambda_naught('auto'))

        # add lambda naught widgets to set lambda naught gb layout
        self.manual_lambda_naught_layout = QtGui.QHBoxLayout()
        self.manual_lambda_naught_layout.addWidget(self.manual_lambda_naught_label)
        self.manual_lambda_naught_layout.addWidget(self.manual_lambda_naught_input)
        self.set_lambda_naught_gb_layout.addLayout(self.manual_lambda_naught_layout)

        self.set_lambda_naught_gb_layout.addWidget(self.auto_lambda_naught_btn)

        # make Group Box for Calibration selection
        self.set_p_calibration_gb = QtGui.QGroupBox()
        self.set_p_calibration_gb.setTitle('Pressure Calibration')
        self.p_calibration_tab_layout.addWidget(self.set_p_calibration_gb)
        self.set_p_calibration_gb_layout = QtGui.QVBoxLayout()
        self.set_p_calibration_gb.setLayout(self.set_p_calibration_gb_layout)

        # make widgets for calibration selection
        self.choose_calibration_drop = QtGui.QComboBox()
        self.choose_calibration_drop.addItems(['Dorogokupets and Oganov, PRB 75, 024115 (2007)',
                                               'Mao et al., JGR 91, 4673 (1986)',
                                               'Dewaele et al., PRB 69, 092106 (2004)'])
        self.p_calibration_alpha_label = QtGui.QLabel('<i>A</i> =')
        self.p_calibration_alpha_label.setAlignment(QtCore.Qt.AlignRight)
        self.p_calibration_alpha_display = QtGui.QLabel('1885')
        self.p_calibration_beta_label = QtGui.QLabel('<i>B</i> =')
        self.p_calibration_beta_label.setAlignment(QtCore.Qt.AlignRight)
        self.p_calibration_beta_display = QtGui.QLabel('11.0')
        # ###self.calculation_label = QtGui.QLabel('P = ' + u'\u03B1' + '/' + u'\u03B2' + '[(' + u'\u03BB' + '/' + u'\u03BB' + '<sub>0</sub>)<sup>' + u'\u03B2' + '</sup> - 1]')
        self.calculation_label = QtGui.QLabel('<i>P</i> = <i>A/B</i> [(' + u'\u03BB' + '/' + u'\u03BB' + '<sub>0</sub>)<sup><i>B</i></sup> - 1]')
        self.calculation_label.setStyleSheet('font-size: 16pt; font-weight: bold')
        self.calculation_label.setAlignment(QtCore.Qt.AlignCenter)

        # connect signal
        self.choose_calibration_drop.currentIndexChanged.connect(self.set_new_p_calibration)

        # add widgets to layout
        self.set_p_calibration_gb_layout.addWidget(self.choose_calibration_drop)

        self.p_cal_constants_layout = QtGui.QHBoxLayout()
        self.p_cal_constants_layout.addWidget(self.p_calibration_alpha_label)
        self.p_cal_constants_layout.addWidget(self.p_calibration_alpha_display)
        self.p_cal_constants_layout.addWidget(self.p_calibration_beta_label)
        self.p_cal_constants_layout.addWidget(self.p_calibration_beta_display)
        self.set_p_calibration_gb_layout.addLayout(self.p_cal_constants_layout)

        self.set_p_calibration_gb_layout.addWidget(self.calculation_label)

        self.ow.addTab(self.p_calibration_tab, 'P Calibration')

        # ###DURATION TAB###
        # Main widget and layout
        self.focus_time_tab = QtGui.QWidget()
        self.focus_time_tab_layout = QtGui.QVBoxLayout()
        self.focus_time_tab_layout.setAlignment(QtCore.Qt.AlignTop)
        self.focus_time_tab.setLayout(self.focus_time_tab_layout)

        # make duration tab widgets
        self.duration_time_label = QtGui.QLabel('Set focusing duration (in minutes)')
        # self.duration_time_label.setStyleSheet('font-size: 12pt')
        self.duration_time_sbox = QtGui.QSpinBox()
        self.duration_time_sbox.setRange(1, 10)
        self.duration_time_sbox.setValue(5)
        # self.duration_time_sbox.setStyleSheet('font-size: 12pt')
        self.duration_time_sbox.setMaximumWidth(70)

        # connect signals
        self.duration_time_sbox.valueChanged.connect(lambda value: self.set_duration(value))

        # place widgets
        self.focus_time_tab_layout.addWidget(self.duration_time_label)
        self.focus_time_tab_layout.addWidget(self.duration_time_sbox)

        # add tab to tab widget
        self.ow.addTab(self.focus_time_tab, 'Focusing')

        # ###Fitting tab###
        # Main widget and layout
        self.fitting_roi_tab = QtGui.QWidget()
        self.fitting_roi_tab_layout = QtGui.QVBoxLayout()
        self.fitting_roi_tab_layout.setAlignment(QtCore.Qt.AlignTop)
        self.fitting_roi_tab.setLayout(self.fitting_roi_tab_layout)

        # make widgets
        self.fitting_roi_label = QtGui.QLabel('Set roi extrema for fitting (delta pixels)')
        self.fit_roi_min_label = QtGui.QLabel('ROI minimum')
        self.fit_roi_min_sbox = QtGui.QSpinBox()
        self.fit_roi_min_sbox.setRange(10, 500)
        self.fit_roi_min_sbox.setValue(150)
        self.fit_roi_min_sbox.setSingleStep(10)
        self.fit_roi_max_label = QtGui.QLabel('ROI maximum')
        self.fit_roi_max_sbox = QtGui.QSpinBox()
        self.fit_roi_max_sbox.setRange(10, 500)
        self.fit_roi_max_sbox.setValue(150)
        self.fit_roi_max_sbox.setSingleStep(10)

        # conect signals
        self.fit_roi_min_sbox.valueChanged.connect(lambda value: self.set_roi_range('min', value))
        self.fit_roi_max_sbox.valueChanged.connect(lambda value: self.set_roi_range('max', value))

        # add widgets to layout
        self.fitting_roi_tab_layout.addWidget(self.fitting_roi_label)

        self.pixel_select_layout = QtGui.QHBoxLayout()
        self.pixel_select_layout.addWidget(self.fit_roi_min_label)
        self.pixel_select_layout.addWidget(self.fit_roi_min_sbox)
        self.pixel_select_layout.addWidget(self.fit_roi_max_label)
        self.pixel_select_layout.addWidget(self.fit_roi_max_sbox)
        self.fitting_roi_tab_layout.addLayout(self.pixel_select_layout)

        self.ow.addTab(self.fitting_roi_tab, 'Fitting ROI')

        # ###EPICS tab###
        # make EPICS tab
        self.epics_tab = QtGui.QWidget()
        self.epics_tab_layout = QtGui.QVBoxLayout()
        self.epics_tab_layout.setAlignment(QtCore.Qt.AlignTop)
        self.epics_tab.setLayout(self.epics_tab_layout)

        # make widgets
        self.epics_label = QtGui.QLabel('Select EPICS PV for temperature tracking')
        self.epics_drop = QtGui.QComboBox()
        self.epics_drop.addItems(['None (disconnected)',
                                  'Lake Shore 336 TC1 Loop 1',
                                  'Lake Shore 336 TC1 Loop 2',
                                  'Lake Shore 336 TC1 Loop 3',
                                  'Lake Shore 336 TC1 Loop 4',
                                  'Lake Shore 336 TC2 Loop 1',
                                  'Lake Shore 336 TC2 Loop 2',
                                  'Lake Shore 336 TC2 Loop 3',
                                  'Lake Shore 336 TC2 Loop 4'])
        self.epics_status_label = QtGui.QLabel('Current EPICS connection status:')
        self.epics_status_display = QtGui.QLabel('Disconnected')

        # connect signals
        self.epics_drop.currentIndexChanged.connect(self.initialize_epics)

        # add widgets to layout
        self.epics_tab_layout.addWidget(self.epics_label)
        self.epics_tab_layout.addWidget(self.epics_drop)

        self.epics_tab_connection_layout = QtGui.QHBoxLayout()
        self.epics_tab_connection_layout.addWidget(self.epics_status_label)
        self.epics_tab_connection_layout.addWidget(self.epics_status_display)
        self.epics_tab_layout.addLayout(self.epics_tab_connection_layout)

        self.ow.addTab(self.epics_tab, 'EPICS')

        '''
        About window
        '''

        self.aw = QtGui.QWidget()
        self.aw.setWindowTitle('About')
        self.aw_layout = QtGui.QVBoxLayout()
        self.aw.setLayout(self.aw_layout)

        self.owner_label = QtGui.QLabel('RubyRead developed by HPCAT\n'
                                        'Python 2.7 (32-bit), PyQt4, PyQtGraph 0.10\n'
                                        'Beta version built 22 May 2019')
        self.aw_layout.addWidget(self.owner_label)

        # from Clemens' Dioptas
        # file = open(os.path.join("stylesheet.qss"))
        # stylesheet = file.read()
        # self.setStyleSheet(stylesheet)
        # file.close()

        # initialize collection thread
        self.collect_thread = CollectThread(self)
        self.collect_thread.collect_thread_callback_signal.connect(self.data_set)
        # initialize fit thread
        self.fit_thread = FitThread(self)
        self.fit_thread.fit_thread_callback_signal.connect(self.fit_set)

        # self.show()
        self.temperature_pv = []

    '''
    Class methods
    '''

    def load_data(self):
        if self.collect_thread.go:
            msg = QtGui.QMessageBox.warning(self, 'Unable to load data', 'You must stop continuous data collection before attempting to load data')
            return
        name = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', filter='*.csv'))
        xs, ys = np.genfromtxt(name,
                               delimiter=',',
                               skip_header=1,
                               filling_values=1,
                               usecols=(0, 1),
                               unpack=True)
        core.xs = xs
        core.ys = ys
        update()

    def save_data(self):
        scene = self.raw_data.scene()
        self.dialog_window = exportDialog.ExportDialog(scene)
        self.dialog_window.show(self.raw_data)

    def closeEvent(self, *args, **kwargs):
        if self.collect_thread.go:
            self.collect_thread.stop()
        while self.collect_thread.isRunning():
            time.sleep(0.01)
        app.closeAllWindows()
        sys.exit()

    # class methods for custom tool bar
    def take_one_spectrum(self):
        if not self.collect_thread.go:
            intensities = core.spec.intensities()
            if self.average_spec_cbox.isChecked():
                num = self.average_spec_sbox.value()
                for each in range(num - 1):
                    intensities += core.spec.intensities()
                intensities = intensities / num
            core.ys = intensities
            update()

    def take_n_spectra(self):
        if not self.collect_thread.go:
            self.collect_thread.start()
        else:
            self.collect_thread.stop()

    def fit_one_spectrum(self):
        if not self.fit_n_spec_btn.isChecked():
            self.fit_thread.start()

    def fit_n_spectra(self):
        if self.fit_n_spec_btn.isChecked():
            if not self.show_curve_cbtn.isChecked():
                self.show_curve_cbtn.click()
            if not self.show_fit_p_cbtn.isChecked():
                self.show_fit_p_cbtn.click()
        else:
            if self.show_curve_cbtn.isChecked():
                self.show_curve_cbtn.click()
            if self.show_fit_p_cbtn.isChecked():
                self.show_fit_p_cbtn.click()

    def set_threshold(self):
        core.threshold = self.threshold_min_input.value()

    def test_9000(self):
        print core.spec.serial_number, core.devices
        print type(core.spec.serial_number)

    def test_9999(self):
        print 'not used for the moment'

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

    def toggle_average(self):
        core.average = self.average_spec_cbox.isChecked()

    def set_num_average(self):
        core.num_average = self.average_spec_sbox.value()

    # class methods for plot control
    def show_curve_cbtn_clicked(self):
        if self.show_curve_cbtn.isChecked():
            self.pw.addItem(self.fit_data)
        else:
            self.pw.removeItem(self.fit_data)

    def show_r1r2_cbtn_clicked(self):
        if self.show_r1r2_cbtn.isChecked():
            self.pw.addItem(self.r1_data)
            self.pw.addItem(self.r2_data)
        else:
            self.pw.removeItem(self.r1_data)
            self.pw.removeItem(self.r2_data)

    def show_bg_cbtn_clicked(self):
        if self.show_bg_cbtn.isChecked():
            self.pw.addItem(self.bg_data)
        else:
            self.pw.removeItem(self.bg_data)

    def show_fit_p_cbtn_clicked(self):
        if self.show_fit_p_cbtn.isChecked():
            self.pw.addItem(self.vline_press)
        else:
            self.pw.removeItem(self.vline_press)

    def show_ref_p_cbtn_clicked(self):
        if self.show_ref_p_cbtn.isChecked():
            self.pw.addItem(self.vline_ref)
        else:
            self.pw.removeItem(self.vline_ref)

    def show_target_p_cbtn_clicked(self):
        if self.show_target_p_cbtn.isChecked():
            self.pw.addItem(self.vline_target)
        else:
            self.pw.removeItem(self.vline_target)

    def show_target_p_lambda_changed(self):
        target_lambda = float(self.show_target_p_lambda.text())
        self.show_target_p_lambda.setText('%.3f' % target_lambda)
        self.vline_target.setX(target_lambda)
        self.calculate_target_pressure(target_lambda)

    def show_target_p_pressure_changed(self):
        target_pressure = float(self.show_target_p_pressure.text())
        self.show_target_p_pressure.setText('%.2f' % target_pressure)
        target_lambda = core.lambda_0_t_user * ((target_pressure * core.beta / core.alpha + 1) ** (1 / core.beta))
        self.vline_target.setX(target_lambda)
        self.show_target_p_lambda.setText('%.3f' % target_lambda)
        self.calculate_deltas()

    def show_target_p_delta_changed(self):
        delta_p = float(self.show_target_p_delta.text())
        self.show_target_p_delta.setText('%.2f' % delta_p)
        fit_p = float(self.pressure_fit_display.text())
        target_p = fit_p + delta_p
        self.show_target_p_pressure.setText('%.2f' % target_p)
        self.show_target_p_pressure_changed()

    def set_ref_from_zero(self):
        self.show_ref_p_lambda.setText(self.lambda_naught_t_display.text())
        self.show_ref_p_pressure.setText('0.00')
        self.vline_ref.setX(float(self.lambda_naught_t_display.text()))
        self.calculate_deltas()

    def set_ref_from_fit(self):
        self.show_ref_p_lambda.setText(self.lambda_r1_display.text())
        self.show_ref_p_pressure.setText(self.pressure_fit_display.text())
        self.vline_ref.setX(float(self.lambda_r1_display.text()))
        self.calculate_deltas()

    def set_ref_from_target(self):
        self.show_ref_p_lambda.setText(self.show_target_p_lambda.text())
        self.show_ref_p_pressure.setText(self.show_target_p_pressure.text())
        self.vline_ref.setX(float(self.show_target_p_lambda.text()))
        self.calculate_deltas()

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

    # class methods for pressure control
    def calculate_lambda_0_t(self):
        t = self.temperature_input.value()
        cold_style = 'QSpinBox {background-color: #add8e6; font: bold 24px}'
        hot_style = 'QSpinBox {background-color: #ffb347; font: bold 24px}'
        rt_style = 'QSpinBox {background-color: #ffffff; font: bold 24px}'
        if t < 295:
            self.temperature_input.setStyleSheet(cold_style)
        elif t > 295:
            self.temperature_input.setStyleSheet(hot_style)
        else:
            self.temperature_input.setStyleSheet(rt_style)
        offset = core.lambda_0_user - core.lambda_0_ref
        lambda_0_t = 10000000 / (14423.0 + 0.0446*t - 0.000481*t*t + 0.000000371*t*t*t)
        core.lambda_0_t_user = lambda_0_t + offset
        self.lambda_naught_t_display.setText('%.3f' % core.lambda_0_t_user)
        calculate_pressure(core.lambda_r1)
        self.calculate_target_p_lambda()

    # class methods for tabs
    def set_lambda_naught(self, source):
        if source == 'manual':
            new_lambda = float(self.manual_lambda_naught_input.text())
        elif source == 'auto':
            new_lambda = core.lambda_r1
        core.lambda_0_user = new_lambda
        self.lambda_naught_295_display.setText('%.3f' % new_lambda)
        self.calculate_lambda_0_t()
        # save data in file for software restart
        new_gui_lambda_string = 'gui.lambda_naught_295_display.setText(\'' + '%.3f' % new_lambda + '\')'
        new_core_lambda_string = 'core.lambda_0_user = ' + '%.3f' % new_lambda
        textfile = open('rubyread.txt', 'w')
        textfile.write(new_gui_lambda_string + '\n' + new_core_lambda_string + '\n')
        textfile.close()

    def set_new_p_calibration(self):
        index = self.choose_calibration_drop.currentIndex()
        if index == 0:
            calibration = 'Dorogokupets and Oganov (2007)'
            a = 1885
            b = 11.0
        elif index == 1:
            calibration = 'Mao et al. (1986)'
            a = 1904
            b = 7.665
        else:
            calibration = 'Dewaele et al. (2004)'
            a = 1904
            b = 9.5
        self.press_calibration_display.setText(calibration)
        core.alpha = a
        core.beta = b
        self.p_calibration_alpha_display.setText(str(a))
        self.p_calibration_beta_display.setText(str(b))
        calculate_pressure(core.lambda_r1)
        self.calculate_target_pressure(float(self.show_target_p_lambda.text()))
        self.calculate_deltas()

    # class methods for duration tab
    def set_duration(self, value):
        core.duration = value*60

    # class methods for fitting roi tab
    def set_roi_range(self, end, value):
        if end == 'min':
            core.roi_min = value
        if end == 'max':
            core.roi_max = value

    # class methods for EPICS tab
    def initialize_epics(self):
        pv_list = ['None (disconnected)',
                   '16LakeShore1:LS336:TC1:IN1',
                   '16LakeShore1:LS336:TC1:IN2',
                   '16LakeShore1:LS336:TC1:IN3',
                   '16LakeShore1:LS336:TC1:IN4',
                   '16LakeShore1:LS336:TC2:IN1',
                   '16LakeShore1:LS336:TC2:IN2',
                   '16LakeShore1:LS336:TC2:IN3',
                   '16LakeShore1:LS336:TC2:IN4']
        if self.epics_drop.currentIndex() == 0:
            self.temperature_pv.disconnect()
            self.temperature_track_cbox.setChecked(False)
            self.temperature_track_cbox.setEnabled(False)
            self.epics_status_display.setText('Disconnected')
            return
        if not type(self.temperature_pv) == list:
            self.temperature_pv.disconnect()
        temperature_pv = pv_list[self.epics_drop.currentIndex()]
        self.temperature_pv = PV(temperature_pv, callback=self.track_temperature_pv,
                                 auto_monitor=True, connection_callback=self.epics_disconnect,
                                 connection_timeout=1.0)
        if not self.temperature_pv.wait_for_connection(timeout=1.0):
            self.epics_status_display.setText('Failed to connect')
            self.temperature_pv.disconnect()
            self.temperature_track_cbox.setChecked(False)
            self.temperature_track_cbox.setEnabled(False)
        else:
            self.epics_status_display.setText('Connected')
            self.temperature_track_cbox.setEnabled(True)

    def track_temperature_pv(self, value, **kwargs):
        if self.temperature_track_cbox.isChecked():
            if 3 < value < 601:
                self.temperature_input.setValue(value)

    def epics_disconnect(self, conn, **kwargs):
        if not conn:
            self.epics_drop.setCurrentIndex(0)

    # ###THREAD CALLBACK METHODS### #
    def data_set(self, data_dict):
        if int(data_dict['remaining_time']) == 0:
            self.remaining_time_display.setStyleSheet('')
            self.remaining_time_display.setText('Idle')
            self.take_n_spec_btn.setChecked(False)
        else:
            core.ys = data_dict['raw_y']
            self.remaining_time_display.setStyleSheet('background-color: green; color: yellow')
            remaining_time = str(int(data_dict['remaining_time']))
            self.remaining_time_display.setText(remaining_time)
            update()

    def fit_set(self, fit_dict):
        warning = fit_dict['warning']
        if not warning == '':
            self.fit_warning_display.setStyleSheet('background-color: red; color: yellow')
            fitted_list = [self.show_curve_cbtn, self.show_r1r2_cbtn, self.show_bg_cbtn]
            for each in fitted_list:
                if each.isChecked():
                    each.click()
        else:
            popt = fit_dict['popt']
            self.lambda_r1_display.setText('%.3f' % popt[5])
            self.fit_data.setData(core.xs_roi, double_pseudo(core.xs_roi, *popt))
            self.r1_data.setData(core.xs_roi, pseudo(core.xs_roi, popt[4], popt[5], popt[6], popt[7], popt[8], popt[9]))
            self.r2_data.setData(core.xs_roi, pseudo(core.xs_roi, popt[0], popt[1], popt[2], popt[3], popt[8], popt[9]))
            self.bg_data.setData(core.xs_roi, (popt[8] * core.xs_roi + popt[9]))
            # calculate pressure
            core.lambda_r1 = popt[5]
            calculate_pressure(core.lambda_r1)
            self.vline_press.setPos(popt[5])
            if not self.show_curve_cbtn.isChecked():
                self.show_curve_cbtn.click()
            if not self.show_fit_p_cbtn.isChecked():
                self.show_fit_p_cbtn.click()
            self.fit_warning_display.setStyleSheet('')
        self.fit_warning_display.setText(warning)


class CoreData:
    def __init__(self):
        # get spectrometer going
        spec_list = ['HR+C0308', 'HR+C0996', 'HR+D1333', 'HR+C2429', 'HR+C0614', 'HR+C2911']
        self.devices = sb.list_devices()
        self.spec = sb.Spectrometer(self.devices[0])
        if self.spec.serial_number not in spec_list:
            widget = QtGui.QWidget()
            msg = QtGui.QMessageBox.warning(widget, 'Spectrometer not recognized', 'The serial number of your spectrometer is not recognized.\nContact HPCAT staff to add your spectrometer to the list of approved devices.')
            sys.exit()
        self.spec.integration_time_micros(100000)

        # initial real and dummy spectra
        self.xs = self.spec.wavelengths()
        self.ys = self.spec.intensities()

        # initial fit boundaries
        self.roi_min = 150
        self.roi_max = 150

        # set initial roi arrays
        default_zoom = np.abs(self.xs-694.260).argmin()
        self.xs_roi = self.xs[default_zoom - self.roi_min:default_zoom + self.roi_max]
        self.ys_roi = self.ys[default_zoom - self.roi_min:default_zoom + self.roi_max]

        # variables to pass through thread
        self.average = False
        self.num_average = 1
        self.threshold = 1000
        self.warning = ''

        # initial focusing time
        self.duration = 300

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


class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.RectMode)

    # reimplement right-click to zoom roi
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.zoom_roi()

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.autoRange()

    def mouseDragEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev)

    def zoom_roi(self):
        self.setXRange(core.xs_roi[0], core.xs_roi[-1])
        self.setYRange(core.ys_roi.min(), core.ys_roi.max())


class CollectThread(QtCore.QThread):
    collect_thread_callback_signal = QtCore.pyqtSignal(dict)

    def __init__(self, parent):
        super(CollectThread, self).__init__(parent)
        self.go = False

    def run(self):
        self.go = True
        data_dict = {'remaining_time': '', 'raw_y': ''}
        start_time = time.clock()
        while self.go:
            # get the spectrum
            intensities = core.spec.intensities()
            # average if needed
            if core.average:
                num = core.num_average
                for each in range(num - 1):
                    intensities += core.spec.intensities()
                intensities = intensities / num
            # determine remaining time to collect spectra
            remaining_time = core.duration - (time.clock() - start_time)
            # update dictionary values and send the dict signal
            data_dict['remaining_time'] = remaining_time
            data_dict['raw_y'] = intensities
            self.collect_thread_callback_signal.emit(data_dict)
            # check if it's time to stop
            if not remaining_time > 0:
                self.stop()
        data_dict['remaining_time'] = 0
        self.collect_thread_callback_signal.emit(data_dict)

    def stop(self):
        self.go = False


class FitThread(QtCore.QThread):
    fit_thread_callback_signal = QtCore.pyqtSignal(dict)

    def __init__(self, parent):
        super(FitThread, self).__init__(parent)

    def run(self):
        fit_dict = {'warning': '', 'popt': ''}
        # start by defining ROI arrays and get max_index for ROI
        full_max_index = np.argmax(core.ys)
        roi_min = full_max_index - core.roi_min
        roi_max = full_max_index + core.roi_max
        # handle edge situations (for example, during background-only spectra)
        if roi_min < 0:
            roi_min = 0
        if roi_max > 2047:
            roi_max = -1
        core.xs_roi = core.xs[roi_min:roi_max]
        core.ys_roi = core.ys[roi_min:roi_max]
        roi_max_index = np.argmax(core.ys_roi)
        # start with approximate linear background (using full spectrum)
        slope = (core.ys[-1] - core.ys[0]) / (core.xs[-1] - core.xs[0])
        intercept = core.ys[0] - slope * core.xs[0]
        # obtain initial guesses for fitting parameters using ROI array
        r1_pos = core.xs_roi[roi_max_index]
        r2_pos = r1_pos - 1.4
        r1_height = core.ys_roi[roi_max_index] - (slope * r1_pos + intercept)
        r2_height = r1_height / 2.0
        # check r1_height is within range before fitting
        if r1_height < core.threshold:
            warning = 'Too weak'
        elif core.ys_roi[roi_max_index] > 16000:
            warning = 'Saturated'
        else:
            # define fitting parameters p0 (area approximated by height)
            p0 = [r2_height, r2_pos, 0.5, 1.0, r1_height, r1_pos, 0.5, 1.0, slope, intercept]
            try:
                popt, pcov = curve_fit(double_pseudo, core.xs_roi, core.ys_roi, p0=p0)
                warning = ''
                fit_dict['popt'] = popt
            except RuntimeError:
                warning = 'Poor fit'
        fit_dict['warning'] = warning
        self.fit_thread_callback_signal.emit(fit_dict)


def update():
    # take current intesities and plot them
    # Set up y scaling options
    if gui.scale_y_btn_grp.checkedId() == 1:
        viewable = vb.viewRange()
        left_index = np.abs(core.xs-viewable[0][0]).argmin()
        right_index = np.abs(core.xs-viewable[0][1]).argmin()
        view_min = core.ys[left_index:right_index].min()
        view_max = core.ys[left_index:right_index].max()
        if view_max > viewable[1][1]:
            vb.setRange(yRange=(view_min, view_max))
        if view_min < viewable[1][0]:
            vb.setRange(yRange=(view_min, viewable[1][1]))
    # y scaling done, ready to assign new data to curve
    gui.raw_data.setData(core.xs, core.ys)
    if gui.fit_n_spec_btn.isChecked():
        gui.fit_thread.start()


def calculate_pressure(lambda_r1):
    core.pressure = core.alpha * ((1 / core.beta) * (((lambda_r1 / core.lambda_0_t_user) ** core.beta) - 1))
    gui.pressure_fit_display.setText('%.2f' % core.pressure)
    gui.calculate_deltas()


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


def recall_lambda_naught():
    # try to restore lambda naught values from previous definition
    try:
        textfile = open('rubyread.txt', 'r')
        exec textfile.read()
        textfile.close()
        gui.calculate_lambda_0_t()
    except IOError:
        print 'Initialization file not found, unable to update zero pressure wavelength'
    except TypeError:
        print 'File format not correct, unable to update zero pressure wavelength'


app = QtGui.QApplication(sys.argv)
core = CoreData()
vb = CustomViewBox()
gui = Window()
pg.setConfigOptions(antialias=True)
gui.show()
update()
recall_lambda_naught()
sys.exit(app.exec_())
