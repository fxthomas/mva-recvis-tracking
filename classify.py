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
threshold_before_op = 7.
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

def classifyWindow (neglut, poslut, words, points, ncoeff, window=None):
  wfilt = words
  if window != None:
    pfilt = apply_along_axis (inside(window), 1, points)
    wfilt = words[pfilt]

  wu = unique(wfilt)
  p1 = poslut[-1] + sum(poslut[wu])
  p0 = neglut[-1] + sum(neglut[wu])

  # Compute log-probabilitiesa
  pp = abs((p1+p0)/2 - ncoeff)/abs(ncoeff)
  return (p1-p0)*pp

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
  if xa0 > xb1:
    return 0.
  elif xa1 < xb0:
    return 0.
  elif ya0 > yb1:
    return 0.
  elif ya1 < yb0:
    return 0.
  else:
    x_overlap = min (xb1, xa1) - max (xb0, xa0)
    y_overlap = min (yb1, ya1) - max (yb0, ya0)
    overlap = x_overlap*y_overlap
    area1 = (xa1-xa0)*(ya1-ya0)
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

  # Create random windows, and classify them
  scmax = [0,]*nmaxwin
  wimax = [(0,0,0,0)]*nmaxwin
  for it in range(niter):
    stdout.write("\rFinding windows... {0}%".format(it*100/niter))
    stdout.flush()

    i0 = randint(ih-min_win_size)
    j0 = randint(iw-min_win_size)
    i1 = i0 + randint(min(ih-i0,max_win_size) - min_win_size) + min_win_size-1
    j1 = j0 + randint(min(iw-j0,max_win_size) - min_win_size) + min_win_size-1
    score = classifyWindow (neglut, poslut, hist, features, ncoeff, (i0,j0,i1,j1))
    insert_sorted (scmax, wimax, score, (i0,j0,i1,j1))

  purge_threshold (wimax, scmax, threshold_before)
  purge_overlap (wimax, scmax)
  purge_threshold (wimax, scmax, threshold_after)

  print ("\rFound {0} windows after cleanup :".format (len(wimax)))
  for (wi,sc) in zip(wimax,scmax):
    print ("  {1}, score: {0}".format(sc, wi))

  return wimax,scmax,features

def display_windows (image, windows, scores, block=True):
  ih,iw = image.shape
  fig = figure()
  imshow (image[::-1,:], cmap=cm.gray)
  for (wi, sc) in zip(windows, scores):
    i0,j0,i1,j1 = wi
    fig.gca().add_patch (Rectangle((j0,ih-i1), width=(j1-j0), height=(i1-i0), fill=False, color="#ff0000"))
    text (j0,ih-i1, "{0}".format(sc), bbox=dict(facecolor='red')) 
  show(block=block)
