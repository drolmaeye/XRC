#   import seabreeze
#   import seabreeze.spectrometers as sb
#

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import seabreeze.spectrometers as sb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *


devices = sb.list_devices()
spec = sb.Spectrometer(devices[0])
spec.integration_time_micros(20000)

style.use('dark_background')

fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
stoppage = False

def animate(i):

    xs = spec.wavelengths()
    ys = spec.intensities()


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

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(column=0,row=1)

ani = animation.FuncAnimation(fig, animate, interval=100)
# plt.show()

button = Button(root, text='stop', command=stop_ani)
button.grid(row=2, column=0)

root.protocol('WM_DELETE_WINDOW', close_quit)
root.mainloop()

