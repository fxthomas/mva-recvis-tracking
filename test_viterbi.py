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

# Usage: ./test.py neg.mat pos.mat *.jpg

import classify
from classify import *
from scipy.io import loadmat
from sys import argv
from glob import glob
from os import path
from re import sub,match
from matplotlib import colors as col
import networkx as nx

if len(argv) == 4: 
  maxidx = int(argv[3])
else:
  maxidx = len(file_list)

rr = sub(r"%d", r"(?P<idx>\d+)", argv[1])
rg = sub(r"%d", r"*", argv[1])
file_list = glob(rg)
scores = [[]] * (maxidx+1)
windows = [[]] * (maxidx+1)
features = [[]] * (maxidx+1)
ih,iw = 0,0
winres = loadmat ('wins_conservative.mat')['RES'].squeeze()

for fi in file_list:
  m = match (rr, fi)
  if m:
    index = 0
    try:
      index = int(m.group('idx'))
    except IndexError:
      pass

    if index >= maxidx:
      continue

    img = mean (imread (fi), axis=2)
    ih,iw = img.shape
    print ("Loaded {0} {2}:{1}".format (fi, img.shape, index))

    # Compute windows using my method
    #wins,sc,feat = detect_objects (clusters, neglut, poslut, ncoeff, img, niter=250)
    #windows[index] = wins
    #scores[index] = sc
    #features[index] = feat

    # Load windows using the paper's method
    ww = winres[index-1]
    nn,_ = ww.shape
    windows[index] = []
    scores[index] = []

    for i in range (nn):
      windows[index].append ((ih-ww[i,1], ww[i,0], ih-ww[i,3], ww[i,2]))
      scores[index].append (ww[i,4])

    #display_windows (images[index], windows[index], scores[index])

def wu (win,t):
  i0,j0,i1,j1 = win
  return (i0,j0,i1,j1,0,t)

def wv (win,t):
  i0,j0,i1,j1 = win
  return (i0,j0,i1,j1,1,t)

def ijcost (wa, wb, nf):
  ia0,ja0,ia1,ja1 = wa
  ib0,jb0,ib1,jb1 = wb
  iac,jac = (ia0+ia1)/2,(ja0+ja1)/2
  ibc,jbc = (ib0+ib1)/2,(jb0+jb1)/2
  di = iac-ibc
  dj = jac-jbc
  return -log(1-pow((di*di+dj*dj)/nf, 0.1))

# Create graph
print ("Creating graph...")
G = nx.DiGraph()
for wat in range(len(windows)):
  for waj in range(len(windows[wat])):
    wa = windows[wat][waj]

    # Add window edge
    #G.add_edge (wu(wa,wat), wv(wa,wat), cost=-scores[wat][waj]+20, flow=0)
    G.add_edge (wu(wa,wat), wv(wa,wat), cost=-scores[wat][waj], flow=0)

    # Add S-links
    G.add_edge ("S", wu(wa,wat), cost=0.2, flow=0)

    # Add T-links
    G.add_edge (wv(wa,wat), "T", cost=0.8, flow=0)

    # Add transition edges
    nb_jump = 1
    for wbt in range(wat+1, min(wat+1+nb_jump, len(windows))):
      for wbj in range(len(windows[wbt])):
        wb = windows[wbt][wbj]

        # If match on next frame, don't add links without overlap, else add them with a cost
        if overlap (wa,wb) > 0.1 and overlap (wb,wa) > 0.1:
          G.add_edge (wv(wa,wat), wu(wb,wbt), cost=0, flow=0)
        elif wbt > wat+1:
          G.add_edge (wv(wa,wat), wu(wb,wbt), cost=ijcost (wa,wb,ih*ih+iw*iw), flow=0)

# Add flow to graph
for (a,b) in G.edges():
  G[a][b]['flow'] = 0

# Iterate while we got a negative cost path
print ("Solving SSP...")
cost = -inf
pred,dist = None, None
while cost < 0:
  pred, dist = nx.algorithms.bellman_ford (G, "S", weight="cost")
  cost = dist["T"]
  print cost
  if cost >= 0:
    break
  else:
    b = "T"
    while b != "S":
      a = pred[b]
      t = G[a][b]['cost']
      f = G[a][b]['flow']
      G.remove_edge (a, b)
      G.add_edge (b, a)
      G[b][a]['cost'] = -t

      if f == 1:
        G[b][a]['flow'] = 0
      else:
        G[b][a]['flow'] = 1

      b = a

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

    count = reclabel (G, neighbor, color)+1
    if count >= 0:
      ok = True
      break

  if ok:
    ia0,ja0,ia1,ja1,f,ta = ns
    if f == 1:
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
  print (i)
  rrr = path.join ("./", sub(r"%d", str(i), argv[1]))
  try:
    im = imread (rrr)
    figures[i].gca().imshow (im[::-1,:], cmap=cm.gray)
    figures[i].savefig (path.join(pathname, "frame-{0}.png".format(i)))
  except Exception as e:
    print "Error loading {0}!".format(rrr)
    print e
    pass
