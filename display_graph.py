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
figures = [figure() for i in range(len(windows))]

print ("Displaying windows...")
colors = [col.rgb2hex((rand(), rand(), rand())) for i in range(current_track_id)]
def reclabel (G, ns, color):
  if ns == 'S':
    return 0

  ok = False
  count = 0
  for neighbor in G.neighbors(ns):
    if G[ns][neighbor]['flow'] < 1:
      continue

    count = reclabel (G, neighbor, color) + 1
    if count >= 0:
      ok = True
      break

  if ok:
    ia0,ja0,ia1,ja1,f,ta = ns
    if f == 1:
      print " ---> Frame {0}".format (ta)
      figures[ta].gca().add_patch (Rectangle((ja0,ih-ia1), width=(ja1-ja0), height=(ia1-ia0), fill=False, color=color))
      figures[ta].gca().annotate ("{0:.3f}".format (G[ns][neighbor]['cost']), xy=(ja0, ih-ia1), bbox=dict(facecolor='red'))
    return count
  else:
    return -1

for ns in G.neighbors('T'):
  if G['T'][ns]['flow'] == 0:
    continue

  print "   [Track {0}]".format (current_track_id+1)
  lenlist.append (reclabel (G, ns, col.rgb2hex ((rand(), rand(), rand()))))
  current_track_id = current_track_id+1

print "Found tracks with lengths: ", lenlist

print ("Displaying images...")
for i in range (len (windows)):
  ww, image_name, _ = winimg[i]
  print (i)
  try:
    im = imread ("images/ethms/" + str(image_name[0]))
    figures[i].gca().imshow (im[::1,:], cmap=cm.gray)
    figures[i].savefig (path.join(pathname, "frame-{0}.png".format(i)))
    del figures[i]
  except Exception as e:
    print "Error loading {0}!".format(image_name)
    print e
    pass
  gc.collect()
