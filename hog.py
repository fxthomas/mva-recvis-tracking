#!/usr/bin/python2
# coding=utf-8

# Base Python File (hog.py)
# Created: Sat 03 Dec 2011 05:31:01 PM CET
# Version: 1.0
#
# This Python script was developped by François-Xavier Thomas.
# You are free to copy, adapt or modify it.
# If you do so, however, leave my name somewhere in the credits, I'd appreciate it ;)
# 
# (ɔ) François-Xavier Thomas <fx.thomas@gmail.com>

from numpy import *
from scipy import *
from scipy.io import savemat
from scipy.ndimage.filters import convolve1d
from pylab import *
from sys import argv
from harris import *
import os
import glob

# Some constants
epsilon = 0.01 # So that we don't get /0 errors
grad_quant_nb = 9 # The histogram has 9 bins
histogram_cell_size = 7 # We want histograms over 7x7px cells
histogram_block_size = 3 # 3x3 cells for each block
pi = arctan2 (0,-1) # That's pi

def histogram (nquant, grado, gradw):
  """
  Computes the histogram with 'nquant' bins, the gradient orientations matrix 'grado', and gradient magnitude matrix 'gradw'.
  """
  h,w = grado.shape
  bins = [0.,] * nquant
  for i in range(0,h):
    for j in range(0,w):
      q = int(grado[i,j])
      if q >= nquant:
        q = nquant-1
      bins[q] = bins[q] + gradw[i,j]
  return bins

def normalizeBlock (cells):
  """
  Normalizes an array of cells
  """
  h,w,q = cells.shape
  cc = cells.reshape (h*w*q)
  cc = cc - mean (cc)
  return cc / (norm(cc,ord=2)+epsilon)

def maxCorrel (hog1, hog2):
  """
  Computes the max value of the ZNCC for HOG_1 and HOG_2 description vectors.
  """
  return max (correlate (hog1, hog2))

def imageHistogram (filename):
  # Load image
  img = imread (filename)

  # Convert to grayscale
  if img.ndim == 3:
    img = mean (img, axis=2)

  # Prepare gradient image
  gradient_kernel = array([-1,0,1])
  gradx = convolve1d (img, gradient_kernel, axis=1)
  grady = convolve1d (img, gradient_kernel, axis=0)

  # Quantize gradient orientations (yeah, that's ugly)
  grado = floor ((arctan2 (grady, gradx) + pi)/(2*pi)*9)
  gradw = pow (gradx,2)+pow (grady,2)

  # Compute Harris features
  fc = get_harris_points (compute_harris_response(img), 8, 0.10)

  # Compute histograms (erk, more ugliness)
  h,w = img.shape
  hbr = (histogram_block_size-1)/2
  hcr = (histogram_cell_size-1)/2
  histograms = array ( \
    [
      [
        [histogram( \
          grad_quant_nb, \
          grado[x+i*histogram_cell_size-hcr:x+(i+1)*histogram_cell_size-hcr,y+j*histogram_cell_size-hcr:y+(j+1)*histogram_cell_size-hcr], \
          gradw[x+i*histogram_cell_size-hcr:x+(i+1)*histogram_cell_size-hcr,y+j*histogram_cell_size-hcr:y+(j+1)*histogram_cell_size-hcr] \
        ) \
        for j in range(-hbr,hbr+1)] \
      for i in range(-hbr,hbr+1)]
    for (x,y) in fc] \
  )

  # Normalize them
  if histograms.ndim != 4:
    return None,None

  cnt,_,_,_ = histograms.shape
  histograms = array ( \
    [normalizeBlock ( \
      histograms[i,:,:,:].squeeze()
    ) \
    for i in range (0,cnt)] \
  )

  return histograms,fc
