% This MATLAB script is used to produce a .mat file, used in the main Python scripts for this project.
% 
% Data comes from 2 places :
%
%  * Part-Based Object Recognition : http://www.cs.brown.edu/~pff/latent/
%  * ETH Moving Sequences Dataset : http://www.vision.ee.ethz.ch/~aess/dataset/

% Load model data from object detector
load ('VOC2009/person_final.mat', 'model');

% Load images from ETHMS Dataset
images = readIDL ('ethms/seq03-annot.idl');

% Prepare resulting window cell array
RES = cell (size(images,2),1);

% For each image, detect persons and store them in RES
for i=1:size(images,2)
    images(i).img
    RES{i} = process (imread (strcat('ethms/', images(i).img)), model);
end

% Save results
save seq_ethms_results.mat RES images
