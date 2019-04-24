# ###from scipy import exp, asarray
# ###from math import cos, sin, radians, pi, sqrt
# ###
# ###T = 200
# ###
# ###r_one_295_reference = 694.260
# ###
# ###r_one_295_user = 694.200
# ###
# ###r_one_295_offset = r_one_295_user - r_one_295_reference
# ###
# ###r_one_t_cm = 14423.0 + 0.0446*T - 0.000481*T*T + 0.000000371*T*T*T
# ###
# ###r_one_t_nm = 10000000 / r_one_t_cm
# ###
# ###print r_one_t_nm
# ###
# ###r_one_t_corrected = r_one_t_nm + r_one_295_offset
# ###
# ###print r_one_t_corrected
# ###
# ###r_one_measured = 694.200
# ###
# ###
# ###alpha = 1904
# ###beta = 7.665
# ###
# ###pressure = alpha * ((1 / beta) * (((r_one_measured / r_one_t_corrected) ** beta) - 1))
# ###print pressure

import sys
from PyQt4.Qt import *

class MyPopup(QWidget):
    def __init__(self):
        QWidget.__init__(self)

    def paintEvent(self, e):
        dc = QPainter(self)
        dc.drawLine(0, 0, 100, 100)
        dc.drawLine(100, 0, 0, 100)

class MainWindow(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.cw = QWidget(self)
        self.setCentralWidget(self.cw)
        self.btn1 = QPushButton("Click me", self.cw)
        self.btn1.setGeometry(QRect(0, 0, 100, 30))
        self.connect(self.btn1, SIGNAL("clicked()"), self.doit)
        self.w = None

    def doit(self):
        print "Opening a new popup window..."
        self.w = MyPopup()
        self.w.setGeometry(QRect(100, 100, 400, 200))
        self.w.show()

class App(QApplication):
    def __init__(self, *args):
        QApplication.__init__(self, *args)
        self.main = MainWindow()
        self.connect(self, SIGNAL("lastWindowClosed()"), self.byebye )
        self.main.show()

    def byebye( self ):
        self.exit(0)

def main(args):
    global app
    app = App(args)
    app.exec_()

if __name__ == "__main__":
    main(sys.argv)