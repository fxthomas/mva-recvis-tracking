#!/usr/bin/python2
# coding=utf-8

# Base Python File (test.py)
# Created: Thu 08 Dec 2011 12:26:31 PM CET
# Version: 1.0
#
# This Python script was developped by François-Xavier Thomas.
# You are free to copy, adapt or modify it.
# If you do so, however, leave my name somewhere in the credits, I'd appreciate it ;)
# 
# (ɔ) François-Xavier Thomas <fx.thomas@gmail.com>

from classify import *
from scipy.io import loadmat
from sys import argv

clusters = loadmat ("clusters.mat")
clusters = clusters['clusters'].squeeze()
print ("Loaded {0} clusters".format (len(clusters)))

neg = loadmat(argv[1])
neg = neg['samples'].squeeze()
print ("Loaded {0} negative samples".format (len(neg)))

pos = loadmat(argv[2])
pos = pos['samples'].squeeze()
print ("Loaded {0} positive samples".format (len(pos)))

img = mean (imread (argv[3]), axis=2)
print ("Loaded image {0} {1}".format (argv[3], img.shape))

wins,scores = detect_objects (clusters, neg, pos, img)
display_windows (img, wins, scores)

