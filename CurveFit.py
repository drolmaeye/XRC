import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import seabreeze.spectrometers as sb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *



style.use('dark_background')

fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)

