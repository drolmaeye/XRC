__author__ = 'j.smith'

'''
A GUI for displaying scans collected using the EPICS scan record
'''

# import necessary modules
import sys
from PyQt4 import QtGui, QtCore, Qt
import numpy as np
import pyqtgraph as pg
from epics import PV, caget
import time


class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(100, 100, 1080, 720)
        self.setWindowTitle('Oculus Mechanicus')
        self.setWindowIcon(QtGui.QIcon('eye1.png'))

        self.scan_trhead = ScanThread(self)
        self.scan_trhead.scan_thread_callback_signal.connect(self.draw_plot)

    def draw_plot(self):
        print 'drawing'


class ScanThread(QtCore.QThread):
    scan_thread_callback_signal = QtCore.pyqtSignal(dict)

    def __init__(self, parent):
        super(ScanThread, self).__init__(parent)

    def run(self):
        if data.get():
            print 'scan done'
            return
        plot_dict = {}
        print 'scan thread running!!!!!'






def dcv_t(**kwargs):
    pass#print 'D01CV', dnncv.get(), time.clock()


def rcv_t(**kwargs):
    pass#print 'R1CV', rmcv.get(), time.clock()


def val_t(**kwargs):
    print 'VAL', val.get(), time.clock()
    print 'D01CV', dnncv.get(), time.clock()
    print 'R1CV', rmcv.get(), time.clock()


def dda_t(**kwargs):
    pass#print 'D01DA', dnnda.get(), time.clock()


def pra_t(**kwargs):
    pass#print 'P1RA', pmra.get(), time.clock()


def data_t(**kwargs):
    print 'DATA', data.get(), time.clock()
    print 'D01DA', dnnda.get()[:cpt.get()], time.clock()
    print 'P1RA', pmra.get()[:cpt.get()], time.clock()
    for each in kwargs:
        print each
    print pmra.host
    eye.scan_trhead.start()



def cpt_t(**kwargs):
    print 'CPT', cpt.get(), time.clock()


dnncv = PV('16TEST1:scan1.D01CV', callback=dcv_t)
rmcv = PV('16TEST1:scan1.R1CV', callback=rcv_t)
r1pv = PV('16TEST1:scan1.R1PV')
desc = PV('16TEST1:m9.DESC')
val = PV('16TEST1:scan1.VAL', callback=val_t)

dnnda = PV('16TEST1:scan1.D01DA', callback=dda_t)
pmra = PV('16TEST1:scan1.P1RA', callback=pra_t)
data = PV('16TEST1:scan1.DATA', callback=data_t)
cpt = PV('16TEST1:scan1.CPT', callback=cpt_t)


app = QtGui.QApplication(sys.argv)
eye = Window()
eye.show()
sys.exit(app.exec_())
