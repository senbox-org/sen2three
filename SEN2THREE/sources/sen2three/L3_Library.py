#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from numpy import *
from scipy import interpolate as sp
from PIL import Image
import sys

def stdoutWrite(s):
    sys.stdout.write(s)
    sys.stdout.flush()
    

def stderrWrite(s):
    sys.stderr.write(s)
    sys.stderr.flush() 


def statistics(arr, comment = ''):
    """ Debug routine for data statistics

        :param arr: the object to be analyzed
        :type arr: a numpy array
        :return: the statistics
        :rtype: string

    """
    if len(arr) == 0:
        return False
    s = 'object:' + str(comment) + '\n'
    s += '--------------------' + '\n'
    s += 'shape: ' + str(shape(arr)) + '\n'
    s += 'sum  : ' + str(arr.sum()) + '\n'
    s += 'mean : ' + str(arr.mean()) + '\n'
    s += 'std  : ' + str(arr.std())  + '\n'
    s += 'min  : ' + str(arr.min())  + '\n'
    s += 'max  : ' + str(arr.max())  + '\n'
    s += '-------------------' + '\n'
    return s


def showImage(arr):
    """ Debug routine for data display

        :param arr: the image to be displayed
        :type arr: a 2dim numpy array of unsigned int (16 bit)
        :return: false, if no image
        :rtype: boolean

    """
    if(arr.ndim) != 2:
        sys.stderr.write('Must be a two dimensional array.\n')
        return False

    arrmin = arr.mean() - 3*arr.std()
    arrmax = arr.mean() + 3*arr.std()
    arrlen = arrmax-arrmin
    arr = clip(arr, arrmin, arrmax)
    scale = 255.0
    scaledArr = (arr-arrmin).astype(float32) / float32(arrlen) * scale
    arr = (scaledArr.astype(uint8))
    img = Image.fromarray(arr)
    img.show()
    return True


def reverse(a): return a[::-1]


def rectBivariateSpline(xIn, yIn, zIn):
    x = arange(zIn.shape[0], dtype=float32)
    y = arange(zIn.shape[1], dtype=float32)

    f = sp.RectBivariateSpline(x,y,zIn)
    return f(xIn,yIn)
