__author__ = 'j.smith'

'''
A GUI saple viewing, alignment, and diamond calculation correction
'''

# import necessary modules, etc
from Tkinter import *
import tkMessageBox
import tkFont
from epics import *
import time
import os.path


# define classes
class MotorLine:

    def __init__(self, master, motor, heading=False):

        self.frame = Frame(master)
        self.frame.pack()

        # secondary frame to hold the tweak presets
        self.tweak_frame = Frame(self.frame)
        self.tweak_frame.grid(row=2, column=3)

        # make fonts for various use
        small_font = tkFont.Font(size=8)
        medium_font = tkFont.Font(size=12)

        # create EPICS motor
        self.axis = Motor(motor)

        # define instance variables
        self.desc = StringVar()
        self.rbv = StringVar()
        self.val = DoubleVar()
        self.val_ref = DoubleVar()
        self.twv = DoubleVar()
        self.twv_ref = DoubleVar()
        self.desc.set(self.axis.get('DESC'))
        self.rbv.set('%.3f' % self.axis.get('RBV'))
        self.val.set('%.3f' % self.axis.get('VAL'))
        self.twv.set('%.3f' % self.axis.get('TWV'))

        # set callbacks
        self.axis.set_callback(attr='RBV', callback=self.update_rbv)
        self.axis.set_callback(attr='VAL', callback=self.update_val)
        self.axis.set_callback(attr='TWV', callback=self.update_twv)

        # set up column headings if needed
        if heading:
            self.desc_head = Label(self.frame, text='Stage', font=medium_font)
            self.rbv_head = Label(self.frame, text='Readback', font=medium_font)
            self.val_head = Label(self.frame, text='Drive', font=medium_font)
            self.twv_head = Label(self.frame, text='Tweak Step', font=medium_font)
            self.twk_head = Label(self.frame, text='Tweak', font=medium_font)

            self.desc_head.grid(row=0, column=0, padx=5, pady=2, sticky='w')
            self.rbv_head.grid(row=0, column=1, padx=5, pady=2, sticky='e')
            self.val_head.grid(row=0, column=2, padx=5, pady=2, sticky='w')
            self.twv_head.grid(row=0, column=3, padx=5, pady=2)
            self.twk_head.grid(row=0, column=4, columnspan=2, padx=5, pady=2)

        # make display line widgets
        self.desc_label = Label(self.frame, textvariable=self.desc, font=medium_font, width=10, anchor='w')
        self.rbv_label = Label(self.frame, textvariable=self.rbv, font=medium_font, width=10, anchor='e')
        self.val_entry = Entry(self.frame, textvariable=self.val, font=medium_font, width=10)
        self.twv_entry = Entry(self.frame, textvariable=self.twv, font=medium_font, width=10)
        self.twv2_button = Button(self.tweak_frame, text='2', font=small_font, bg='blue', fg='white', command=lambda: self.axis.put('TWV', 0.002))
        self.twv5_button = Button(self.tweak_frame, text='5', font=small_font, bg='blue', fg='white', command=lambda: self.axis.put('TWV', 0.005))
        self.twv10_button = Button(self.tweak_frame, text='10', font=small_font, bg='blue', fg='white', command=lambda: self.axis.put('TWV', 0.010))
        self.twv25_button = Button(self.tweak_frame, text='25', font=small_font, bg='blue', fg='white', command=lambda: self.axis.put('TWV', 0.025))
        self.twv100_button = Button(self.tweak_frame, text='100', font=small_font, bg='blue', fg='white', command=lambda: self.axis.put('TWV', 0.100))
        self.twr_button = Button(self.frame, text='<', font=medium_font, command=lambda: self.axis.put('TWR', 1))
        self.twf_button = Button(self.frame, text='>', font=medium_font, command=lambda: self.axis.put('TWF', 1))

        # bind entry widgets
        self.val_entry.bind('<FocusIn>', lambda event: self.val_ref.set(self.val.get()))
        self.val_entry.bind('<FocusOut>', lambda event: self.val.set('%.3f' % self.val_ref.get()))
        self.val_entry.bind('<Return>', self.val_entry_validation)
        self.twv_entry.bind('<FocusIn>', lambda event: self.twv_ref.set(self.twv.get()))
        self.twv_entry.bind('<FocusOut>', lambda event: self.twv.set('%.3f' % self.twv_ref.get()))
        self.twv_entry.bind('<Return>', self.twv_entry_validation)

        # place display line widgets
        self.desc_label.grid(row=1, column=0, padx=5, pady=2)
        self.rbv_label.grid(row=1, column=1, padx=5, pady=2)
        self.val_entry.grid(row=1, column=2, padx=5, pady=2)
        self.twv_entry.grid(row=1, column=3, padx=5, pady=2)
        self.twv2_button.pack(side=LEFT)
        self.twv5_button.pack(side=LEFT)
        self.twv10_button.pack(side=LEFT)
        self.twv25_button.pack(side=LEFT)
        self.twv100_button.pack(side=LEFT)
        self.twr_button.grid(row=1, column=4, padx=5, pady=2)
        self.twf_button.grid(row=1, column=5, padx=5, pady=2)

    def update_rbv(self, **kwargs):
        self.rbv.set('%.3f' % self.axis.get('RBV'))

    def update_val(self, **kwargs):
        self.val.set('%.3f' % self.axis.get('VAL'))

    def update_twv(self, **kwargs):
        self.twv.set('%.3f' % self.axis.get('TWV'))

    def val_entry_validation(self, event):
        # value must be float
        # value must lie within motor limits
        try:
            val = self.val.get()
            isinstance(val, float)
            if self.axis.within_limits(val):
                self.val.set('%.3f' % val)
                self.val_ref.set('%.3f' % val)
                self.axis.move(val)                               
            else:
                self.val.set('%.3f' % self.axis.get('RBV'))
                limits_warn()
        except ValueError:
            self.val.set('%.3f' % self.axis.get('RBV'))
            invalid_entry()

    def twv_entry_validation(self, event):
        # value must be float
        try:
            twv = self.twv.get()
            isinstance(twv, float)
            self.twv.set('%.3f' % twv)
            self.twv_ref.set('%.3f' % twv)
            self.axis.put('TWV', twv)
        except ValueError:
            self.twv.set('%.3f' % self.twv_ref.get())
            invalid_entry()


# define generic functions
def limits_warn():
    tkMessageBox.showwarning('Limits Violation',
                             'Target position(s) exceeds motor limits\n'
                             'Input was reset to previous value')


def invalid_entry():
    # generic pop-up notification for invalid text entries
    tkMessageBox.showwarning('Invalid Entry',
                             message='Input was reset to default value')






'''
Program start, define primary UI
'''
root = Tk()
root.title('DACalign')

frameLeft = Frame(root, relief=RIDGE)
frameLeft.pack(side=LEFT)

frameRight = Frame(root, relief=RIDGE)
frameRight.pack(side=LEFT)

mX = MotorLine(frameLeft, '16TEST1:m9', heading=True)
mY = MotorLine(frameLeft, '16TEST1:m10')
mZ = MotorLine(frameLeft, '16TEST1:m11')



root.mainloop()
