#!/usr/bin/python2
# coding=utf-8

# Base Python File (display_graph.py)
# Created: Fri 20 Jan 2012 11:01:01 PM CET
# Version: 1.0
#
# This Python script was developped by François-Xavier Thomas.
# You are free to copy, adapt or modify it.
# If you do so, however, leave my name somewhere in the credits, I'd appreciate it ;)
# 
# (ɔ) François-Xavier Thomas <fx.thomas@gmail.com>

import classify
from classify import *
from scipy.io import loadmat
from sys import argv
from glob import glob
from os import path
from re import sub,match
from matplotlib import colors as col
import networkx as nx
from networkx.readwrite.gpickle import read_gpickle
import gc

# Load ETHMS result set data
_mat = loadmat (argv[1])
winres = _mat["RES"].squeeze()
winimg = _mat["images"].squeeze()
maxidx = len (winimg)

scores = [[]] * (maxidx+1)
windows = [[]] * (maxidx+1)
features = [[]] * (maxidx+1)
ih,iw = 0,0

for fi in range (maxidx):
  ww, image_name, _ = winimg[fi]

  img = mean (imread ("images/ethms/" + str(image_name[0])), axis=2)
  ih,iw = img.shape
  print ("Loaded {0} {2}:{1}".format (str(image_name[0]), img.shape, fi))

  # Compute windows using my method
  #wins,sc,feat = detect_objects (clusters, neglut, poslut, ncoeff, img, niter=250)
  #windows[index] = wins
  #scores[index] = sc
  #features[index] = feat

  # Load windows using the paper's method
  ww = winres[fi]
  nn,_ = ww.shape
  windows[fi] = []
  scores[fi] = []

  for i in range (nn):
    windows[fi].append ((ih-ww[i,1], ww[i,0], ih-ww[i,3], ww[i,2]))
    scores[fi].append (ww[i,4])

  #display_windows (images[index], windows[index], scores[index])

# Load graph
G = read_gpickle (argv[3])

# Find track ids
current_track_id = 0
dd = {}
lenlist = []
pathname = argv[2]
fig = figure()

print ("Displaying windows...")
colors = [col.rgb2hex((rand(), rand(), rand())) for i in range(current_track_id)]
def reclabel (G, ns, color, px, py, display=False):
  if ns == 'S':
    return 0

  ok = False
  count = 0
  ia0,ja0,ia1,ja1,f,ta = ns
  pxn = (ja0+ja1)/2.
  pyn = ih - (ia1+ia0)/2.

  for neighbor in G.neighbors(ns):
    if G[ns][neighbor]['flow'] < 1:
      continue

    count = reclabel (G, neighbor, color, pxn, pyn, display=display) + 1
    if count >= 0:
      ok = True
      break

  if ok:
    if f == 1 and px != -1 and py != -1 and display:
        fig.gca().add_line (Line2D ([px, pxn], [py, pyn], color=color))
    return count
  else:
    return -1

for ns in G.neighbors('T'):
  if G['T'][ns]['flow'] == 0:
    continue
  print "   [Track {0}]".format (current_track_id+1)
  lenlist.append (reclabel (G, ns, col.rgb2hex ((rand(), rand(), rand())), -1, -1, display=(current_track_id == int(argv[4]))))
  current_track_id = current_track_id+1

print "Found tracks with lengths: ", lenlist

print ("Displaying images...")
for i in range (len (windows)):
  ww, image_name, _ = winimg[i]
  print (i)
  try:
    im = imread ("images/ethms/" + str(image_name[0]))
    fig.gca().imshow (im[::1,:], cmap=cm.gray)
    fig.savefig ("frame-traj.png")
    break
  except Exception as e:
    print "Error loading {0}!".format(image_name)
    print e
    pass
