#!/usr/bin/python2
# coding=utf-8

# Base Python File (track_stats.py)
# Created: Thu 19 Jan 2012 11:29:00 AM CET
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
import re

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

# Read saved graph
G = read_gpickle (argv[3])

# Read track list
class Track:
  def __init__ (self, tid, start):
    self.track_id = tid
    self.track_start = start
    self.window_ids = []

  def append_window (self, wid):
    self.window_ids.append (wid)

  def get_window_for_frame (self, fr):
    i = fr - self.track_start
    if i >= 0 and i < len(self.window_ids):
      wins, _, _ = winimg[fr]
      return wins[self.window_ids[i],:]
    else:
      return None

tracks = []
fp = open ("seq_ethms_tracks.dat")
line_expr = re.compile (r"(?P<track_id>\d+):\s*(?P<start_frame>\d+):\s*(?P<frames>(\d+,)+\d+)\n")

for l in fp:
  mo = line_expr.match (l)
  if mo:
    print l
    t = Track (int (mo.group('track_id')), int (mo.group('start_frame')))
    twid = re.split (",", mo.group ('frames'))
    for wid in twid:
      t.append_window (int (wid))
    tracks.append (t)
fp.close()

# Find track ids
current_track_id = 0
dd = {}
lenlist = []
pathname = argv[2]

print ("Computing tracks...")
colors = [col.rgb2hex((rand(), rand(), rand())) for i in range(current_track_id)]
def reclabel (G, ns, color):
  if ns == 'S':
    return []

  ok = False
  ln = 0
  for neighbor in G.neighbors(ns):
    if G[ns][neighbor]['flow'] < 1:
      continue

    ln = reclabel (G, neighbor, color)
    if ln != None:
      ok = True
      break

  if ok:
    ia0,ja0,ia1,ja1,f,ta = ns
    if f == 1:
      return ln + [(ta,ia0,ja0,ia1,ja1),]
    else:
      return ln
  else:
    return None

for ns in G.neighbors('T'):
  if G['T'][ns]['flow'] == 0:
    continue

  print "   [Track {0}]".format (current_track_id+1)
  lenlist.append (reclabel (G, ns, col.rgb2hex ((rand(), rand(), rand()))))
  current_track_id = current_track_id+1

print "Found {0} tracks".format (current_track_id)

# Compare to labeled tracks
_mapped_tids = []
for est_tck in lenlist:
  mt = []

  for (fid,i0,j0,i1,j1) in est_tck:
    max_overlap = 0.
    max_tid = -1
    for (gnd_tid,gnd_tck) in zip(range(len(tracks)),tracks):
      ww = gnd_tck.get_window_for_frame (fid)
      if ww == None:
        continue

      gnd_w = (ww[1],ww[0],ww[3],ww[2])
      est_w = (i0,j0,i1,j1)
      est_overlap = overlap (gnd_w, est_w)

      if est_overlap > max_overlap:
        max_overlap = est_overlap
        max_tid = gnd_tid

    mt.append ((max_tid,max_overlap))
  _mapped_tids.append ((gnd_tck.track_start, mt))

mapped_tids = []
for (s,f) in _mapped_tids:
  count = 0
  for (v,o) in f:
    if v >= 0:
      count = count +1
  if count > 0:
    mapped_tids.append ((s,f))

# Compute some stats
track_switching = []
track_nrdetected = {}
cur_mtid = 0

for (sf,t) in mapped_tids:
  nlt = []
  prev_tid = -1
  tid_switch_count = 0
  pk = 0
  for (cur_tid, ovl) in t:
    if cur_tid != prev_tid:
      if prev_tid != -1:
        if cur_tid != -1:
          print "Detected track {0} switch from real T{1} to T{2} on frame {3}".format (cur_mtid, prev_tid, cur_tid, sf+pk)
          tid_switch_count = tid_switch_count + 1
          nlt.append (cur_tid)
        else:
          break
      else:
        print " --- Track {0} start at frame {1} --- ".format (cur_mtid, sf+pk)
        nlt.append (cur_tid)
      prev_tid = cur_tid
    pk = pk + 1

  for t in set(nlt):
    if t in track_nrdetected:
      track_nrdetected[t] = track_nrdetected[t] + 1
    else:
      track_nrdetected[t] = 1

  print " --- Track {0} end at frame {1} spanning real tracks {2} --- ".format (cur_mtid, sf+pk, nlt)
  cur_mtid = cur_mtid + 1
  track_switching.append (tid_switch_count)

print ""
print track_switching
print track_nrdetected
