#!/usr/bin/python
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
from pylab import *
from sys import argv,stdout
from harris import *
from svmutil import *

model = svm_load_model ("model.dat".encode("latin-1"))
print ("Loaded SVM model")

print ("Loading image {0}...".format (argv[1]))
img = mean (imread (argv[1]), axis=2)
test_hist,fc = imageHistogram (argv[1])
ih,iw = img.shape

print ("Finding best candidates...")
p_labels,_,p_vals = svm_predict (zeros(len(fc)), test_hist.tolist(), model)
ncount = 0
pcount = 0

for (l,w) in zip(p_labels,p_vals):
  print ("Label {0} with w={1}".format (l,w))
  if l == 1:
    pcount = pcount+w[0]
  elif l == -1:
    ncount = ncount-w[0]

stdout.write ("\n")
print ("Found {0}+/{1}-, score is {2}".format (pcount, ncount, 2*(float(pcount)/float(pcount+ncount) - 0.5)))

votespace = zeros ((ih,iw))
for (w,(x,y)) in zip(p_vals,fc):
  votespace[x,y] = votespace[x,y]+w

votespace = convolve2d (votespace, gauss_kernel(50), mode="same")
imshow (votespace)
show()
