#!/usr/bin/python2
# coding=utf-8

# Base Python File (train_clusters.py)
# Created: Tue 06 Dec 2011 05:11:28 PM CET
# Version: 1.0
#
# This Python script was developped by François-Xavier Thomas.
# You are free to copy, adapt or modify it.
# If you do so, however, leave my name somewhere in the credits, I'd appreciate it ;)
# 
# (ɔ) François-Xavier Thomas <fx.thomas@gmail.com>


from hog import *
from harris import *
from scipy.cluster.vq import kmeans, whiten
from scipy.io import savemat
from pylab import *

nb_clusters = 400

# scan argument path and compute hogs for each negative image
print ("Processing images...")
hlist = None
for path in argv:
  for infile in glob.glob(os.path.join(path, "*.*")):
    print ("Processing {0}...".format (infile))
    hh,_ = imageHistogram (imread(infile))
    if hh != None:
      if hlist == None:
        hlist = hh
      else:
        hlist = concatenate ((hlist, hh), axis=0)

nh,_ = hlist.shape
print ("Clustering {0} vectors...".format(nh))
centroids,_ = kmeans (hlist, nb_clusters, iter=1)
savemat ('clusters.mat', {'clusters': centroids})
