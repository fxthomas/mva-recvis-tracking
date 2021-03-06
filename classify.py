#!/usr/bin/python2
# coding=utf-8

# Base Python File (classify.py)
# Created: Tue 06 Dec 2011 11:28:32 AM CET
# Version: 1.0
#
# This Python script was developped by François-Xavier Thomas.
# You are free to copy, adapt or modify it.
# If you do so, however, leave my name somewhere in the credits, I'd appreciate it ;)
# 
# (ɔ) François-Xavier Thomas <fx.thomas@gmail.com>

from hog import *
from numpy import *
from scipy import *
from scipy.signal import convolve2d
from scipy.cluster.vq import vq
from pylab import *
from sys import stdout
from harris import *

nrandomiter = 400
nmaxwin = 20
min_win_size = 24
max_win_size = 500
threshold_before_op = 0.
threshold_after_op = 15.

def inside (win):
  """
  Tests if the location is inside the window win=(x0,y0,x1,y1).
  The window must have x0 < x1 and y0 < y1.
  """
  x0,y0,x1,y1 = win
  def _inside (point):
    x,y = point
    return x > x0 and x < x1 and y > y0 and y < y1

  return _inside

def compute_lut (clusters, neg, pos):
  # Look-up tables
  neglut = zeros (len(clusters)+1)
  poslut = zeros (len(clusters)+1)

  # Number of samples
  nnb = len(neg)
  pnb = len(pos)

  # Normalizing coeff for probas
  pw = 0.

  for w in range(len(clusters)):
    t0 = len(find (neg == w))
    t1 = len(find (pos == w))
    t = t0 + t1
    if t0 != 0:
      neglut[w] = log (float(t0)/float(nnb))
    if t1 != 0:
      poslut[w] = log (float(t1)/float(pnb))
    if t != 0:
      pw = pw + log(float(t)/float(pnb+nnb))
  poslut[-1] = log(float(pnb)/float(nnb+pnb))
  neglut[-1] = log(float(nnb)/float(nnb+pnb))

  return neglut,poslut,pw

def sat_compute (neglut, poslut, h, w, hist, features):
  sat = zeros ((h,w,2))
  for i in range(len(features)):
    fx,fy = features[i]
    sat[fx,fy,0] = neglut[hist[i]]
    sat[fx,fy,1] = poslut[hist[i]]

  for i in range (h):
    for j in range (w):
      if i > 0:
        sat[i,j,:] = sat[i,j,:] + sat[i-1,j,:]
      if j > 0:
        sat[i,j,:] = sat[i,j,:] + sat[i,j-1,:]
      if i > 0 and j > 0:
        sat[i,j,:] = sat[i,j,:] - sat[i-1,j-1,:]
  return sat

def sat_sum (sat, x0, y0, x1, y1, k):
  return sat[x0,y0,k] + sat[x1,y1,k] - sat[x0,y1,k] - sat[x1,y0,k]

def classifyWindow (negc, posc, sat, window=None):
  wx0,wy0,wx1,wy1 = window
  p1 = posc + sat_sum (sat, wx0, wy0, wx1, wy1, 1)
  p0 = negc + sat_sum (sat, wx0, wy0, wx1, wy1, 0)

  # Compute log-probabilitiesa
  #pp = abs((p1+p0)/2 - ncoeff)/abs(ncoeff)
  return (p1-p0)#*pp

def gimp2win(ih):
  return lambda (x0,y0,x1,y1):(ih-y1,x0,ih-y0,x1)

def gauss_kernel_for_size (h,w):
  gh = int((h-1)/2)
  gw = int((w-1)/2)
  gk = gauss_kernel (gh,gw)
  ga = zeros ((h,w))
  ga[:2*gh+1,:2*gw+1] = gk
  return ga

def insert_sorted (l1, l2, e1, e2):
  """
  Insert e into the (ascending) sorted list l1, and insert it at the same place in l2.
  Returns the new element's index in the sorted list, or -1 if no index has been found.
  """
  i = 0
  for i in range(len(l1)):
    if e1 >= l1[i]:
      if i != 0:
        l1[i-1] = l1[i]
        l2[i-1] = l2[i]
      if i < len(l1)-1:
        l1[i] = l1[i+1]
        l2[i] = l2[i+1]
      else:
        l1[i] = e1
        l2[i] = e2
        return i
    else:
      if i != 0:
        l1[i-1] = e1
        l2[i-1] = e2
      return i-1

def overlap (wina, winb):
  xa0,ya0,xa1,ya1 = wina
  xb0,yb0,xb1,yb1 = winb

  _xa0 = min(xa0,xa1)
  _ya0 = min(ya0,ya1)
  _xa1 = max(xa0,xa1)
  _ya1 = max(ya0,ya1)
  _xb0 = min(xb0,xb1)
  _yb0 = min(yb0,yb1)
  _xb1 = max(xb0,xb1)
  _yb1 = max(yb0,yb1)

  x_overlap = min (_xb1, _xa1) - max (_xb0, _xa0)
  y_overlap = min (_yb1, _ya1) - max (_yb0, _ya0)
  overlap = x_overlap*y_overlap
  area1 = (_xa1-_xa0)*(_ya1-_ya0)
  if area1 == 0 or x_overlap < 0 or y_overlap < 0:
    return 0
  else:
    return float(overlap)/float(area1)

def mean_window (wina, winb):
  xa0,ya0,xa1,ya1 = wina
  xb0,yb0,xb1,yb1 = winb
  return ((xa0+xb0)/2, (ya0+yb0)/2, (xa1+xb1)/2, (ya1+yb1)/2)

def purge_overlap (wins, scores):
  b = 0
  while b < len(wins):
    ok = False
    wa = wins[b]
    for i in range (b+1, len (wins)):
      wb = wins[i]
      o1 = overlap (wa,wb)
      o2 = overlap (wb,wa)
      if (o1 > 0.5 or o2 > 0.5):
        wins[b] = mean_window (wa, wb)
        scores[b] = scores[b] + scores[i]
        ok = True
        del wins[i]
        del scores[i]
        break

    if not ok:
      b = b+1

def purge_reduce (wins, points):
  for i in range(len(wins)):
    pfilt = array (points[apply_along_axis (inside(wins[i]), 1, points)])
    m = mean (pfilt, axis=0)
    s = 2*std(pfilt, axis=0) + 1
    wins[i] = (m[0]-s[0],m[1]-s[1],m[0]+s[0],m[1]+s[1])

def purge_threshold (wins, sc, th):
  i = 0
  while i < len(wins):
    if sc[i] < th:
      del wins[i]
      del sc[i]
    else:
      i = i+1

def detect_objects (clusters, neglut, poslut, ncoeff, image, niter=nrandomiter, threshold_before=threshold_before_op, threshold_after=threshold_after_op):
  # Gather info about parameters
  ih,iw = image.shape

  # Compute and quantize image features into BOW
  print ("Computing image features...")
  hist,features = imageHistogram (image)
  if hist == None:
    print ("No features found...")
    exit(1)
  else:
    hist,_ = vq(hist, clusters)

  # Compute SAT before classifying (for quicker area sums)
  print ("Pre-computing probabilistic SAT...")
  prb_sat = sat_compute (neglut, poslut, ih, iw, hist, features)

  # Create random windows, and classify them
  scmax = [0,]*nmaxwin
  wimax = [(0,0,0,0)]*nmaxwin
  patch_size = 100
  for i0 in range (0, ih-patch_size, patch_size/10):
    for j0 in range (0, iw-patch_size, patch_size/10):
      stdout.write("\rFinding windows... {0}%".format(i0*j0*100/ih/iw))
      stdout.flush()

      i1 = i0 + patch_size
      j1 = j0 + patch_size
      score = classifyWindow (neglut[-1], poslut[-1], prb_sat, (i0,j0,i1,j1))
      insert_sorted (scmax, wimax, score, (i0,j0,i1,j1))

  #purge_threshold (wimax, scmax, threshold_before)
  purge_overlap (wimax, scmax)
  #purge_threshold (wimax, scmax, threshold_after)

  print ("\rFound {0} windows after cleanup :".format (len(wimax)))
  for (wi,sc) in zip(wimax,scmax):
    print ("  {1}, score: {0}".format(sc, wi))

  return wimax,scmax,features

def display_windows (image, windows, scores, block=True, title_text=None):
  ih,iw = image.shape
  fig = figure()
  if (title_text != None):
    title (title_text)
  imshow (image[::-1,:], cmap=cm.gray)
  for (wi, sc) in zip(windows, scores):
    i0,j0,i1,j1 = wi
    fig.gca().add_patch (Rectangle((j0,ih-i1), width=(j1-j0), height=(i1-i0), fill=False, color="#ff0000"))
    text (j0,ih-i1, "{0:.3f}".format(sc), bbox=dict(facecolor='red')) 
  show(block=block)
