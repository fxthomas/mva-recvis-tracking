#!/usr/bin/python2
# coding=utf-8

# Base Python File (test.py)
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
from scipy.io import loadmat
from scipy.signal import convolve2d
from scipy.cluster.vq import vq
from pylab import *
from sys import argv,stdout
from harris import *

max_iter = 700
correl_thresh = 0.6

def inside (win):
  """
  Tests if the location is inside the window win=(x0,y0,x1,y1).
  The window must have x0 < x1 and y0 < y1.
  """
  x0,y0,x1,y1 = win
  def _inside (point):
    print point
    x,y = point
    return x > x0 and x < x1 and y > y0 and y < y1

  return _inside

clusters = loadmat ("clusters.mat")
clusters = clusters['clusters'].squeeze()
ncl,_ = clusters.shape
print ("Loaded {0} clusters".format (ncl))

neg = loadmat(argv[1])
neg = neg['samples'].squeeze()
nsc = len(neg)
print ("Loaded {0} negative samples".format (nsc))

pos = loadmat(argv[2])
pos = pos['samples'].squeeze()
psc = len(pos)
print ("Loaded {0} positive samples".format (psc))

print ("Loading image {0}...".format (argv[3]))
img = mean (imread (argv[3]), axis=2)
test_hist,fc = imageHistogram (argv[3])

if test_hist == None:
  print ("No features found...")
  exit(1)

test_hist,_ = vq(test_hist, clusters)

print ("Finding best candidates...")

def classifyWindow (words, points, window=None):
  wfilt = words
  if window != None:
    pfilt = apply_along_axis (inside(window), 1, points)
    wfilt = words[pfilt]
  print ("Found {0} words".format(len(wfilt)))

  prod1 = 0.
  prod0 = 0.
  pw = 0.
  for w in unique(wfilt):
    t1 = len(find(pos == w))
    t0 = len(find(neg == w))
    if t1 != 0:
      prod1 = prod1 + log(float(t1) / float(psc))
    if t0 != 0:
      prod0 = prod0 + log(float(t0) / float(nsc))
    pw = pw + log (float(t1+t0) / float(nsc+psc))

  p1 = log(float(psc)/float(psc+nsc)) + prod1 - pw
  print ("  -> Log-probability +1: {0}".format(p1))

  p0 = log(float(nsc)/float(psc+nsc)) + prod0 - pw
  print ("  -> Log-probability -1: {0}".format(p0))

  return p1-p0

ih,iw = img.shape
def gimp2win (x0,y0,x1,y1):
  return (ih-y1,x0,ih-y0,x1)

x0 = 360
y0 = 240
x1 = 880
y1 = 650
wwc = gimp2win (x0,y0,x1,y1)

print ("Image shape: {0}".format(img.shape))
print ("Classified window, score: {0}".format(classifyWindow (test_hist, fc, wwc)))
#print ("Classified window, score: {0}".format(classifyWindow (test_hist, fc, None)))

#imshow (img[y1:y0:-1,x0:x1], cmap=cm.gray)
#show()
