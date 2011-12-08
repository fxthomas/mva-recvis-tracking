#!/bin/bash

# Base Script File (train.sh)
# Created: Thu 08 Dec 2011 12:29:42 PM CET
# Version: 1.0
# Author: François-Xavier Thomas <fx.thomas@gmail.com>
#
# This Bash script was developped by François-Xavier Thomas.
# You are free to copy, adapt or modify it.
# If you do so, however, leave my name somewhere in the credits, I'd appreciate it ;)

echo "Training clusters..."
python2 ./train_clusters.py images/background/ images/cars/
echo "Training negative samples..."
python2 ./train_samples.py images/background/ bg.mat
echo "Training positive samples..."
python2 ./train_samples.py images/cars/ cars.mat
