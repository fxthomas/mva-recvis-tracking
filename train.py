#!/usr/bin/python
# coding=utf-8

# Base Python File (train.py)
# Created: Tue 06 Dec 2011 11:27:47 AM CET
# Version: 1.0
#
# This Python script was developped by François-Xavier Thomas.
# You are free to copy, adapt or modify it.
# If you do so, however, leave my name somewhere in the credits, I'd appreciate it ;)
# 
# (ɔ) François-Xavier Thomas <fx.thomas@gmail.com>

from hog import *
from harris import *
from svmutil import * 

# Scan argument path and compute HOGs for each negative image
print ("Processing negative images...")
neg_path = argv[1]
neg_hlist = None
for infile in glob.glob(os.path.join(neg_path, "*.*")):
  print ("Processing {0}...".format (infile))
  hh,_ = imageHistogram (infile)
  if neg_hlist == None:
    neg_hlist = hh
  else:
    neg_hlist = concatenate ((neg_hlist, hh), axis=0)

# Scan argument path and compute HOGs for each positive image
print ("Processing positive images...")
pos_path = argv[2]
pos_hlist = None
for infile in glob.glob(os.path.join(pos_path, "*.*")):
  print ("Processing {0}...".format (infile))
  hh,_ = imageHistogram (infile)
  if pos_hlist == None:
    pos_hlist = hh
  else:
    pos_hlist = concatenate ((pos_hlist, hh), axis=0)

print ("Gathering data for SVM training...")
nc,_ = neg_hlist.shape
pc,_ = pos_hlist.shape
labels = [-1,]*nc + [1,]*pc
data = concatenate ((neg_hlist,pos_hlist), axis=0).tolist()

# Save mat file
#savemat (argv[2], {'samples': hlist})
param = svm_parameter ()
param.kernel_type = RBF
param.gamma = 0.005
param.C = 1.0

problem = svm_problem (labels,data)

print ("Training SVM...")
model = svm_train (problem, param)

print ("Saving model to model.dat...")
svm_save_model ("model.dat".encode("latin-1"), model)

print ("All done!")
