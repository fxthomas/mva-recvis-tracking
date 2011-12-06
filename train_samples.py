#!/usr/bin/python2
# coding=utf-8

# Base Python File (train_samples.py)
# Created: Tue 06 Dec 2011 11:27:47 AM CET
# Version: 1.0
#
# This Python script was developped by François-Xavier Thomas.
# You are free to copy, adapt or modify it.
# If you do so, however, leave my name somewhere in the credits, I'd appreciate it ;)
# 
# (ɔ) François-Xavier Thomas <fx.thomas@gmail.com>

from hog import *
from harris import *
from scipy.io import loadmat,savemat
from scipy.cluster.vq import vq

clusters = loadmat ("clusters.mat")
clusters = clusters['clusters']

# scan argument path and compute hogs for each negative image
print ("Processing images...")
path = argv[1]
hlist = None
for infile in glob.glob(os.path.join(path, "*.*")):
  print ("Processing {0}...".format (infile))
  hh,_ = imageHistogram (infile)
  if hh != None:
    if hlist == None:
      hlist = hh
    else:
      hlist = concatenate ((hlist, hh), axis=0)

qhlist,_ = vq (hlist, clusters)

# Save mat file
savemat (argv[2], {'samples': qhlist})
