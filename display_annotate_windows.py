#!/usr/bin/python2
# coding=utf-8

# Base Python File (display_annotate_windows.py)
# Created: Tue 17 Jan 2012 11:13:23 AM CET
# Version: 1.0
#
# This Python script was developped by François-Xavier Thomas.
# You are free to copy, adapt or modify it.
# If you do so, however, leave my name somewhere in the credits, I'd appreciate it ;)
# 
# (ɔ) François-Xavier Thomas <fx.thomas@gmail.com>

import classify as cl
from scipy import *
from numpy import *
from pylab import *
from scipy.io import loadmat
from sys import argv

images = loadmat ("seq_ethms_results.mat")["images"].squeeze()

for i in range (int(argv[1]), int(argv[1]) + len (images)):
  wins, imname, _ = images[i]

  winl = []
  for j in range (len (wins)):
    winl.append ((wins[j,1], wins[j,0], wins[j,3], wins[j,2]))

  im = mean (imread ("images/ethms/" + str(imname[0])), 2)

  cl.display_windows (im[::-1,:], winl, [ii for ii in range (len (wins))], block=True, title_text="Frame {0}".format(i))
