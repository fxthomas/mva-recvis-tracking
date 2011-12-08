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
from glob import glob
from os import path
from re import sub,match
import networkx as nx

clusters = loadmat ("clusters.mat")
clusters = clusters['clusters'].squeeze()
print ("Loaded {0} clusters".format (len(clusters)))

neg = loadmat(argv[1])
neg = neg['samples'].squeeze()
print ("Loaded {0} negative samples".format (len(neg)))

pos = loadmat(argv[2])
pos = pos['samples'].squeeze()
print ("Loaded {0} positive samples".format (len(pos)))

# Compute LUTs
neglut,poslut,ncoeff = compute_lut (clusters, neg, pos)
print ("Computed look-up tables...")

rr = sub(r"%d", r"(?P<index>\d+)", argv[3])
rg = sub(r"%d", r"*", argv[3])
file_list = glob(rg)
scores = [[],] * (len(file_list)+1)
windows = [[],] * (len(file_list)+1)
features = [[],] * (len(file_list)+1)
ih,iw = 0,0

for fi in file_list:
  m = match (rr, fi)
  if m:
    index = int(m.group('index'))
    img = mean (imread (fi), axis=2)
    ih,iw = img.shape
    print ("Loaded {0} {2}:{1}".format (fi, img.shape, index))
    wins,sc,feat = detect_objects (clusters, neglut, poslut, ncoeff, img, niter=250)
    windows[index] = wins
    scores[index] = sc
    features[index] = sc
    display_windows (img, wins, sc)

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
  return -log(1-(di*di+dj*dj)/nf)

# Create graph
G = nx.DiGraph()
for wat in range(len(windows)):
  for waj in range(len(windows[wat])):
    wa = windows[wat][waj]

    # Add window edge
    G.add_edge (wu(wa,wat), wv(wa,wat), cost=-scores[wat][waj], capacity=1)

    # Add S-links
    G.add_edge ("S", wu(wa,wat), cost=1., capacity=1)

    # Add T-links
    G.add_edge (wv(wa,wat), "T", cost=1., capacity=1)

    # Add transition edges
    nb_jump = 2
    for wbt in range(wat+1, wat+1+nb_jump):
      for wbj in range(len(windows[wbt])):
        wb = windows[wbt][wbj]
        G.add_edge (wv(wa,wat), wu(wb,wbt), cost=ijcost(wa,wb,ih*ih+iw*iw), capacity=1)
