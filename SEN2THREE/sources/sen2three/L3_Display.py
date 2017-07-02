#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from numpy import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.ioff()
import matplotlib.colors as cl
import pylab as P

from scipy.stats import itemfreq

class L3_Display(object):
    ''' A support class, for display of the scene classification and the mosaic map 
        using the Python Image Library (PIL). The display of the data is a configurable option.
        
            :param config: the config object for the current tile (via __init__).
            :type config: a reference to the L3_Config object.

    '''

    def __init__(self, config):
        self._config = config
        self._noData = config.classifier['NO_DATA']
        self._minTime = config.minTime
        self._maxTime = config.maxTime
        self._plot = P
     
    def displayData(self, tables):
        ''' Performs the display of the scene classification and the mosaic map.
        
            :param tables: the table object for the current tile (via __init__).
            :type tables: a reference to the L3_Tables object.

        '''

        # define the colormaps:
        C1 = [[0.0, 0.0, 0.0],  # 0: NO_DATA, Black
              [1.0, 0.0, 0.0],  # 1: Red
              [0.0, 1.0, 0.0],  # 2: Green
              [0.0, 0.0, 1.0],  # 3: Blue
              [1.0, 1.0, 0.0],  # 4: Yellow
              [0.0, 1.0, 1.0],  # 5:
              [1.0, 0.0, 1.0],  # 6:
              [0.5, 0.0, 0.0],  # 7:
              [0.0, 0.5, 0.0],  # 8:
              [0.0, 0.0, 0.5],  # 9:
              [1.0, 0.5, 0.0],  # 10:
              [0.0, 1.0, 0.5]]  # 11:
        c1 = cl.ListedColormap(C1)

        C2 = [[0.0, 0.0, 0.0],  # 0: NO_DATA, Black
              [1.0, 0.0, 0.0],  # 1: DEFECTIVE, Red
              [0.3, 0.3, 0.3],  # 2: SHADOW, Very Dark Gray
              [0.5, 0.3, 0.0],  # 3: CLOUD_SHADOW, Brown
              [0.0, 1.0, 0.0],  # 4: VEGETATION, Green
              [1.0, 1.0, 0.0],  # 5: NOT_VEGETATED, Yellow
              [0.0, 0.0, 1.0],  # 6: WATER, Blue
              [0.4, 0.4, 0.4],  # 7: CLOUD_LOW_PROBA, Dark Gray
              [0.6, 0.6, 0.6],  # 8: CLOUD_MED_PROBA, Light Gray
              [1.0, 1.0, 1.0],  # 9: CLOUD_HI_PROBA, White
              [0.5, 1.0, 1.0],  # 10: THIN_CIRRUS, Light Blue
              [1.0, 0.5, 1.0]]  # 11: SNOW, Pink
        c2 = cl.ListedColormap(C2)

        mosaic = tables.getBand('L3', tables.MSC, uint8)
        scenec = tables.getBand('L3', tables.SCL, uint8)
        fig = self._plot.figure()
        fig.canvas.set_window_title(self._config.L2A_TILE_ID)
        ax1 = self._plot.subplot2grid((2,2), (0,0)) 
        ax2 = self._plot.subplot2grid((2,2), (1,0)) 
        ax3 = self._plot.subplot2grid((2,2), (0,1))
        ax4 = self._plot.subplot2grid((2,2), (1,1))            
        
        idxMoif = itemfreq(mosaic)[:,0]
        nClasses = idxMoif.max()
        xMoif = arange(0,nClasses+1)
        yMoif = zeros(nClasses+1, dtype=float32)
        yMoif[idxMoif] = itemfreq(mosaic)[:,1]
        yMoifCount = float32(yMoif.sum())
        yMoif = yMoif.astype(float32)/yMoifCount * 100.0
        scenecData = [scenec != 0]
        classes = ('Sat','Dark','ClS','Soil','Veg','Water','LPC','MPC','HPC','Cir','Snw')
        yScif = zeros(len(classes)+1, dtype=float32)
        idxScif = itemfreq(scenec[scenecData])[:,0]
        yScif[idxScif] = itemfreq(scenec[scenecData])[:,1]
        yScifCount = float32(yScif.sum())
        yScif = yScif.astype(float32)/yScifCount * 100.0
        xScif = arange(1,13)                
        if len(xMoif) < 3:
            xticks = [1,2]
            xmax = 3
        else:
            xticks = xMoif
            xmax = xMoif.max()+1
        ax1.imshow(mosaic, vmin=0, vmax=12, cmap=c1)
        ax1.set_xticks([0,mosaic.shape[1]])
        ax1.set_yticks([0,mosaic.shape[0]])
        ax1.set_xlabel('Tile Map')
        ax2.imshow(scenec, vmin=0, vmax=11, cmap=c2)
        ax2.set_xticks([0,scenec.shape[1]])
        ax2.set_yticks([0,scenec.shape[0]])
        ax2.set_xlabel('Class Map')
        ax3.set_xlim([0, xmax])            
        ax3.set_xticks(xticks)
        ax3.bar(xMoif, yMoif, align='center', alpha=0.4, color=C1)
        if self._config.algorithm == 'AVERAGE':
            ax3.set_xlabel('Pixel Count [#]')
        else:
            ax3.set_xlabel('Tile [#]')
        ax3.set_ylabel('Frequency [%]')
        ax4.set_xlim([0, 13])
        ax4.bar(xScif, yScif, align='center', alpha=0.4, color=C2)
        ax4.set_xlabel('Class [#]')
        ax4.set_ylabel('Frequency [%]')
        self._plot.draw()
        self._plot.tight_layout()
        self._plot.show(block=False)
        self._plot.savefig(tables.L3_Tile_PLT_File, dpi=100)
        return