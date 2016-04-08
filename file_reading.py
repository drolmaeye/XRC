import os
import time
import numpy as np
import matplotlib.pyplot as plt



os.chdir('Z:\Python Analysis\mesh')
core = np.ones((41, 40))
t_zero = time.clock()
for zsteps in range(core.shape[0]):
    grid_index = zsteps*core.shape[1]
    for ysteps in range(core.shape[1]):
        grid_index += 1
        print grid_index
        file_index = str(grid_index).zfill(3)
        file_name = 'mesh_' + file_index + '.dat'
        f = open(file_name)
        beta_whole = f.read().split('\n')
        f.close()
        beta = beta_whole[0:-1]
        min_one = 16.0
        max_one = 16.7
        data_list = []
        total_area = 0
        for each in beta:
            doublet = each.split('  ')
            if min_one < float(doublet[0]) < max_one:
                element = (float(doublet[0]), float(doublet[1]))
                total_area += element[1]
                data_list.append(element)
        bg_area = ((data_list[-1][1] + data_list[0][1])/2)*(data_list[-1][0] - data_list[0][0])
        signal_to_bg = (total_area - bg_area)/bg_area
        core[zsteps, ysteps] = signal_to_bg
t_final = time.clock()
t_total = t_final - t_zero
print t_total
plt.contourf(core)
plt.colorbar()
# plt.hist(core)
plt.show()


# ## type(alpha)
# ## print alpha
# ## print alpha.split('  ')
# ## beta = alpha.strip('\n')
# ## chi = float((beta.split('  ')[0]))
# ## print type(chi)
# ## print chi
# #
