__author__ = 'j.smith'

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import seabreeze.spectrometers as sb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
import time


# ###devices = sb.list_devices()
# ###spec = sb.Spectrometer(devices[0])
# ###spec.integration_time_micros(20000)




class Stuff:
    def __init__(self, master, row, column):
        self.frame = Frame(master)
        self.frame.grid(row=row, column=column)

        self.ct_time = IntVar()
        self.ct_time.set(100000)
        self.avg_num = IntVar()
        self.avg_num.set(1)

        self.ct_time_entry = Entry(self.frame, textvariable=self.ct_time)
        self.ct_time_entry.grid(row=0, column=0)
        self.ct_time_entry.bind('<Return>', self.ct_time_validate)
        self.avg_num_entry = Entry(self.frame, textvariable=self.avg_num)
        self.avg_num_entry.grid(row=0, column=1)
        self.avg_num_entry.bind('<Return>', self.avg_num_validate)

    def ct_time_validate(self, event):
        print self.ct_time.get()
        spec.integration_time_micros(ct.ct_time.get())

    def avg_num_validate(self, event):
        print self.avg_num.get()




def animate(i):

    num_avg = ct.avg_num.get()
    xs = spec.wavelengths()
    ys = spec.intensities()
    print ys[0]
    for each in range(num_avg - 1):
        ys += spec.intensities()
        print ys[0]
    ys = ys/num_avg
    print ys[0]

    ax1.clear()
    ax1.plot(xs, ys)


def stop_ani():
    global stoppage
    if not stoppage:
        stoppage = True
        ani.event_source.stop()
    else:
        stoppage = False
        ani.event_source.start()





def close_quit():
    # add dialog box back in and indent following code after testing period
    # ##if askyesno('Quit Diptera', 'Do you want to quit?'):
    plt.close('all')
    root.destroy()
    root.quit()


root = Tk()

devices = sb.list_devices()
spec = sb.Spectrometer(devices[0])
spec.integration_time_micros(20000)

stoppage = False

# make drawing area
style.use('dark_background')
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(column=0, row=1)

ct = Stuff(root, 3, 0)

button = Button(root, text='stop', command=stop_ani)
button.grid(row=2, column=0)



ani = animation.FuncAnimation(fig, animate, interval=100)

root.protocol('WM_DELETE_WINDOW', close_quit)
root.mainloop()
