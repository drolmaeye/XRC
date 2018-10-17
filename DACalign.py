__author__ = 'j.smith'

'''
A GUI for sample viewing, alignment, and diamond calculation correction
'''

# import necessary modules, etc
from Tkinter import *
import tkMessageBox
import tkFont
from epics import *
import time
import os


# define classes
class MotorLine:

    def __init__(self, master, motor, heading=False):

        self.frame = Frame(master, pady=5)
        self.frame.pack()

        # secondary frame to hold the tweak presets
        self.tweak_frame = Frame(self.frame)
        self.tweak_frame.grid(row=3, column=3)

        # make fonts for various use
        # small_font = tkFont.Font(size=8)
        # medium_font = tkFont.Font(size=12)

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
            self.motion_head = Label(self.frame, text='Alignment Stage Control', font=large_font)
            self.desc_head = Label(self.frame, text='Stage', font=medium_font)
            self.rbv_head = Label(self.frame, text='Readback', font=medium_font)
            self.val_head = Label(self.frame, text='Drive', font=medium_font)
            self.twv_head = Label(self.frame, text='Tweak Step', font=medium_font)
            self.twk_head = Label(self.frame, text='Tweak', font=medium_font)

            self.motion_head.grid(row=0, column=0, columnspan=6)
            self.desc_head.grid(row=1, column=0, padx=5, pady=2, sticky='w')
            self.rbv_head.grid(row=1, column=1, padx=5, pady=2, sticky='e')
            self.val_head.grid(row=1, column=2, padx=5, pady=2, sticky='w')
            self.twv_head.grid(row=1, column=3, padx=5, pady=2)
            self.twk_head.grid(row=1, column=4, columnspan=2, padx=5, pady=2)

        # make display line widgets
        self.desc_label = Label(self.frame, textvariable=self.desc, font=medium_font, width=15, anchor='w')
        self.rbv_label = Label(self.frame, textvariable=self.rbv, font=medium_font, width=10, anchor='e')
        self.val_entry = Entry(self.frame, textvariable=self.val, font=medium_font, width=10)
        self.twv_entry = Entry(self.frame, textvariable=self.twv, font=medium_font, width=10)
        self.twv2_button = Button(self.tweak_frame, text='2', font=small_font, bg='blue', fg='white',
                                  command=lambda: self.twv_preset_set(0.002))
        self.twv5_button = Button(self.tweak_frame, text='5', font=small_font, bg='blue', fg='white',
                                  command=lambda: self.twv_preset_set(0.005))
        self.twv10_button = Button(self.tweak_frame, text='10', font=small_font, bg='blue', fg='white',
                                   command=lambda: self.twv_preset_set(0.010))
        self.twv50_button = Button(self.tweak_frame, text='50', font=small_font, bg='blue', fg='white',
                                   command=lambda: self.twv_preset_set(0.050))
        self.twv100_button = Button(self.tweak_frame, text='100', font=small_font, bg='blue', fg='white',
                                    command=lambda: self.twv_preset_set(0.100))
        self.twv500_button = Button(self.tweak_frame, text='500', font=small_font, bg='blue', fg='white',
                                    command=lambda: self.twv_preset_set(0.500))
        self.twr_button = Button(self.frame, text='<', bg='light blue', font=medium_font,
                                 command=lambda: self.axis.put('TWR', 1))
        self.twf_button = Button(self.frame, text='>', bg='light blue', font=medium_font,
                                 command=lambda: self.axis.put('TWF', 1))

        # bind entry widgets
        self.val_entry.bind('<FocusIn>', lambda event: self.val_ref.set(self.val.get()))
        self.val_entry.bind('<FocusOut>', lambda event: self.val.set('%.3f' % self.val_ref.get()))
        self.val_entry.bind('<Return>', self.val_entry_validation)
        self.twv_entry.bind('<FocusIn>', lambda event: self.twv_ref.set(self.twv.get()))
        self.twv_entry.bind('<FocusOut>', lambda event: self.twv.set('%.3f' % self.twv_ref.get()))
        self.twv_entry.bind('<Return>', self.twv_entry_validation)

        # place display line widgets
        self.desc_label.grid(row=2, column=0, padx=5, pady=2)
        self.rbv_label.grid(row=2, column=1, padx=5, pady=2)
        self.val_entry.grid(row=2, column=2, padx=5, pady=2)
        self.twv_entry.grid(row=2, column=3, padx=25, pady=2)
        self.twv2_button.pack(side=LEFT)
        self.twv5_button.pack(side=LEFT)
        self.twv10_button.pack(side=LEFT)
        self.twv50_button.pack(side=LEFT)
        self.twv100_button.pack(side=LEFT)
        self.twv500_button.pack(side=LEFT)
        self.twr_button.grid(row=2, column=4, padx=5, pady=2)
        self.twf_button.grid(row=2, column=5, padx=5, pady=2)

    # callbacks for monitoring PVs
    def update_rbv(self, **kwargs):
        self.rbv.set('%.3f' % self.axis.get('RBV'))

    def update_val(self, **kwargs):
        self.val.set('%.3f' % self.axis.get('VAL'))

    def update_twv(self, **kwargs):
        self.twv.set('%.3f' % self.axis.get('TWV'))

    # validations functions
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

    def twv_preset_set(self, twv):
        self.twv_ref.set('%.3f' % twv)
        self.axis.put('TWV', twv)


class DiamondCorrection:

    def __init__(self, master):

        self.frame = Frame(master, pady=5)
        self.frame.pack()

        # define instance variables
        self.x_sample = DoubleVar()
        self.x_table = DoubleVar()
        self.t_diamond = DoubleVar()
        self.x_final = DoubleVar()
        self.y_final = DoubleVar()
        self.z_final = DoubleVar()
        self.sample_name = StringVar()

        # make widgets
        self.diamond_heading = Label(self.frame, text='Diamond Correction', font=large_font)
        self.step1_label = Label(self.frame, text='Step 1', font=large_font)
        self.x_sample_instructions = Label(self.frame, text='Focus on sample', font=medium_font)
        self.x_sample_label = Label(self.frame, textvariable=self.x_sample, font=medium_font, width=11, relief=SUNKEN)
        self.x_sample_button = Button(self.frame, text='Get Positions', bg='light blue', font=medium_font, width=11,
                                      command=self.get_x_sample)
        self.step2_label = Label(self.frame, text='Step 2', font=large_font)
        self.x_table_instructions = Label(self.frame, text='Focus on table', font=medium_font)
        self.x_table_label = Label(self.frame, textvariable=self.x_table, font=medium_font, width=11, relief=SUNKEN)
        self.x_table_button = Button(self.frame, text='Get Positions', bg='light blue', font=medium_font, width=11,
                                     command=self.get_x_table)
        self.step3_label = Label(self.frame, text='Step 3', font=large_font)
        self.send_instructions = Label(self.frame, text='Send positions to', font=medium_font)
        self.send_printer_button = Button(self.frame, text='Printer', bg='light blue', font=medium_font, width=11,
                                          command=self.send_to_printer)
        self.send_beamline_button = Button(self.frame, text='Beamline', bg='light blue', font=medium_font, width=11,
                                           command=self.send_to_beamline)
        self.x_ray_positions_heading = Label(self.frame, text='X-ray Positions', font=large_font)
        self.positions_final_label = Label(self.frame, text='(x, y, z)', font=italic_font)
        self.x_final_display = Label(self.frame, textvariable=self.x_final, bg='light green',
                                     font=medium_font, width=11, relief=SUNKEN)
        self.y_final_display = Label(self.frame, textvariable=self.y_final, bg='light green',
                                     font=medium_font, width=11, relief=SUNKEN)
        self.z_final_display = Label(self.frame, textvariable=self.z_final, bg='light green',
                                     font=medium_font, width=11, relief=SUNKEN)

        self.sample_name_label = Label(self.frame, text='Sample name', font=medium_font)
        self.sample_name_entry = Entry(self.frame, textvariable=self.sample_name, font=medium_font, width=38)

        # place widgets
        self.diamond_heading.grid(row=0, column=0, columnspan=4)
        self.step1_label.grid(row=1, column=0, padx=5, pady=5)
        self.x_sample_instructions.grid(row=1, column=1, padx=5, pady=5, sticky=W)
        self.x_sample_label.grid(row=1, column=2, padx=5, pady=5)
        self.x_sample_button.grid(row=1, column=3, padx=5, pady=5)

        self.step2_label.grid(row=2, column=0, padx=5, pady=5)
        self.x_table_instructions.grid(row=2, column=1, padx=5, pady=5, sticky=W)
        self.x_table_label.grid(row=2, column=2, padx=5, pady=5)
        self.x_table_button.grid(row=2, column=3, padx=5, pady=5)

        self.step3_label.grid(row=3, column=0, padx=5, pady=5)
        self.send_instructions.grid(row=3, column=1, padx=5, pady=5, sticky=W)
        self.send_printer_button.grid(row=3, column=2, padx=5, pady=5)
        self.send_beamline_button.grid(row=3, column=3, padx=5, pady=5)
        
        self.x_ray_positions_heading.grid(row=4, column=0, columnspan=4, pady=5)
        self.positions_final_label.grid(row=5, column=0)
        self.x_final_display.grid(row=5, column=1)
        self.y_final_display.grid(row=5, column=2)
        self.z_final_display.grid(row=5, column=3)

        self.sample_name_label.grid(row=6, column=0, pady=10)
        self.sample_name_entry.grid(row=6, column=1, columnspan=3, pady=10)

    def get_x_sample(self):
        self.x_sample.set('%.3f' % mX.axis.get('RBV'))
        self.x_table.set('')
        self.x_final.set('%.3f' % mX.axis.get('RBV'))
        self.y_final.set('%.3f' % mY.axis.get('RBV'))
        self.z_final.set('%.3f' % mZ.axis.get('RBV'))
        self.sample_name.set('')

    def get_x_table(self):
        self.x_table.set('%.3f' % mX.axis.get('RBV'))
        correction = (self.x_sample.get() - self.x_table.get())*1.417
        self.x_final.set('%.3f' % (self.x_sample.get() + correction))

    def send_to_printer(self):
        # ###print 'to printer'
        line1 = '\n' + 'Timestamp: ' + time.strftime('%d %b %Y %H:%M:%S', time.localtime()) + '\n\n'
        line2 = 'Sample name: ' + self.sample_name.get() + '\n\n'
        line3 = 'X:' + '{:7.3f}'.format(self.x_final.get()) + '\n'
        line4 = 'Y:' + '{:7.3f}'.format(self.y_final.get()) + '\n'
        line5 = 'Z:' + '{:7.3f}'.format(self.z_final.get()) + '\n'
        textfile = open('C:/Python27/Positions.txt', 'w')
        textfile.write(line1 + line2 + line3 + line4 + line5)
        textfile.close()
        os.startfile('C:/Python27/Positions.txt', 'print')

    def send_to_beamline(self):
        tkMessageBox.showinfo('Under Construction',
                              'Feature not yet available\n\n'
                              'Please print or write down your sample positions')


# define generic functions
# def confirm_table():
#     mY.axis.put('RLV', -0.005, wait=True)
#     root.update()
#     time.sleep(0.2)
#     mY.axis.put('RLV', 0.005, wait=True)
#

def origin_move():
    mX.axis.move(0.000)
    mY.axis.move(0.000)
    mZ.axis.move(0.000)


def origin_set():
    confirm = tkMessageBox.askyesno('Confirm action',
                                    'Make sure the image of the crosshair is in focus before proceeding.\n\n'
                                    'Are you sure you want to define the current position as the origin?')
    if confirm:
        mX.axis.set_position(0.000)
        mY.axis.set_position(0.000)
        mZ.axis.set_position(0.000)


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

small_font = tkFont.Font(size=8)
medium_font = tkFont.Font(size=12)
italic_font = tkFont.Font(size=14, slant='italic')
large_font = tkFont.Font(size=16)

frameTop = Frame(root, bd=5, relief=RIDGE, padx=15)
frameTop.pack(fill=X)
frameMiddle = Frame(root, bd=5, relief=RIDGE, padx=15)
frameMiddle.pack(fill=X)
frameBottom = Frame(root, bd=5, relief=RIDGE, padx=15)
frameBottom.pack()

mX = MotorLine(frameTop, '16TEST1:m9', heading=True)
mY = MotorLine(frameTop, '16TEST1:m10')
mZ = MotorLine(frameTop, '16TEST1:m11')

diamond = DiamondCorrection(frameMiddle)

origin_set_button = Button(frameBottom, text='Set as\n Origin', bg='light blue', font=medium_font, width=10,
                           command=origin_set)
origin_set_button.grid(row=0, column=0, padx=45, pady=15)
origin_move_button = Button(frameBottom, text='Move to\n Origin', bg='light blue', font=medium_font, width=10,
                            command=origin_move)
origin_move_button.grid(row=0, column=1, padx=45, pady=15)
table_jump_button = Button(frameBottom, text='Jump to\n Diamond\n Table', bg='light blue', font=medium_font, width=10,
                           command=lambda: mX.axis.put('RLV', -0.900))
table_jump_button.grid(row=0, column=2, padx=45, pady=15)



root.mainloop()
