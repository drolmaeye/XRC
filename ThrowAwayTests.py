from PyQt4.QtCore import QThread, pyqtSignal

class myThread(QThread):
    callBackSignal = pyqtSignal(dict)
    def __init__(self, parent):
        super(QThread, self).__init__(parent)
        self.go = False
        self.settings = {}

    def run(self):
        self.go = True
        while self.go:

            data = {}
            self.callBackSignal.emit(data)


    def stop(self):
        self.go = False


