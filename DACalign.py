__author__ = 'j.smith'

'''
A GUI saple viewing, alignment, and diamond calculation correction
'''

# import necessary modules, etc
from Tkinter import *
import tkMessageBox
import tkFileDialog
import tkFont
from epics import *
import time
import os.path

# define classes
class SampleControl:
    """
    Control and display of current sample position
    """

    def __init__(self, master):
        # make frame to put stuff in
        self.frame = Frame(master)
        self.frame.grid()

        # define variable

class MotorLine:

    def __init__(self, master, motor, precision):

        self.frame = Frame(master)
        self.frame.pack()

        # create motor
        self.axis = Motor(motor)

        # define instance variables
        self.desc = StringVar()
        self.rbv = StringVar()
        self.val = DoubleVar()
        self.twv = StringVar()
        self.desc.set(self.axis.get('DESC'))
        self.rbv.set('%.4f' % self.axis.get('RBV'))
        self.val.set('%.4f' % self.axis.get('VAL'))
        self.twv.set('%.4f' % self.axis.get('TWV'))

        # set callbacks
        self.axis.set_callback(attr='RBV', callback=self.update_rbv)
        self.axis.set_callback(attr='VAL', callback=self.update_val)
        self.axis.set_callback(attr='TWV', callback=self.update_twv)

        # make display line widgets
        self.desc_label = Label(self.frame, textvariable=self.desc, width=10, anchor='w')
        self.rbv_label = Label(self.frame, textvariable=self.rbv, width=10, anchor='w', relief=SUNKEN)
        self.val_entry = Entry(self.frame, textvariable=self.val, width=10)
        self.val_entry.bind('<FocusOut>', self.val_entry_validation)
        self.val_entry.bind('<Return>', self.val_entry_validation)
        self.twv_entry = Entry(self.frame, textvariable=self.twv, width=10)
        self.twr_button = Button(self.frame, text='<', command=lambda: self.axis.put('TWR', 1))
        self.twf_button = Button(self.frame, text='>', command=lambda: self.axis.put('TWF', 1))

        # place display line widgets
        self.desc_label.grid(row=0, column=0, padx=5, pady=2)
        self.rbv_label.grid(row=0, column=1, padx=5, pady=2)
        self.val_entry.grid(row=0, column=2, padx=5, pady=2)
        self.twv_entry.grid(row=0, column=3, padx=5, pady=2)
        self.twr_button.grid(row=0, column=4, padx=5, pady=2)
        self.twf_button.grid(row=0, column=5, padx=5, pady=2)

    def update_rbv(self, **kwargs):
        self.rbv.set('%.4f' % self.axis.get('RBV'))

    def update_val(self, **kwargs):
        self.val.set('%.4f' % self.axis.get('VAL'))

    def update_twv(self, **kwargs):
        self.twv.set('%.4f' % self.axis.get('TWV'))

    def val_entry_validation(self, *event):
        # value must be float
        # in this case, also must lie within backlash-affected limits
        try:
            val = self.val.get()
            isinstance(val, float)
            if self.axis.within_limits(val):
                print 'limits good'
                self.val.set('%.4f' % val)
                self.axis.move(val)                               
            else:
                self.val.set('%.4f' % self.axis.get('RBV'))
                # limits_warn()
        except ValueError:
            self.val.set('%.4f' % self.axis.get('RBV'))
            # invalid_entry()







'''
Program start, define primary UI
'''
root = Tk()
root.title('DACalign')




frameLeft = Frame(root)
frameLeft.pack()

mX = MotorLine(frameLeft, '16TEST1:m9', 3)
mY = MotorLine(frameLeft, '16TEST1:m10', 3)
mZ = MotorLine(frameLeft, '16TEST1:m11', 3)



root.mainloop()
